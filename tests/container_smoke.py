"""Offline smoke test of actual images against an external disposable PostgreSQL.

Build octodig-api:verification and octodig-frontend:verification first. Set local
OCTODIG_TEST_DATABASE_URL and container-reachable OCTODIG_CONTAINER_TEST_DATABASE_URL
to the same database, whose name must end in _test. No database container is used.
"""

import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


CLIENT_CHECK = r'''
import json, time
from urllib.request import Request, urlopen
def call(path, payload=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    body = json.dumps(payload).encode() if payload is not None else None
    with urlopen(Request('http://frontend:8080' + path, data=body, headers=headers), timeout=5) as response:
        return response.read(), response.headers
page, headers = call('/')
assert b'<div id="root">' in page
assert "frame-ancestors 'none'" in headers['Content-Security-Policy']
token = json.loads(call('/api/v1/auth/register', {'email': 'container@example.com', 'name': 'Smoke owner',
    'workspace_name': 'Disposable smoke workspace', 'password': 'offline-smoke-password'})[0])['access_token']
target = json.loads(call('/api/v1/targets', {'name': 'Offline smoke account'}, token)[0])
call('/api/v1/offerings', {'name': 'Fixture offering', 'description': 'Offline fixture', 'approved': True}, token)
run = json.loads(call('/api/v1/targets/' + target['id'] + '/research', {'provider': 'openai', 'max_cost_usd': '0.05'}, token)[0])
deadline = time.monotonic() + 30
while run['status'] not in ['completed_partial', 'failed', 'budget_exceeded'] and time.monotonic() < deadline:
    time.sleep(0.3)
    run = json.loads(call('/api/v1/runs/' + run['id'], token=token)[0])
assert run['status'] == 'completed_partial', 'Offline worker did not return its honest unconfigured-provider report'
report = json.loads(call('/api/v1/runs/' + run['id'] + '/report', token=token)[0])
assert len(report['sections']) == 12 and report['gaps']
markdown = call('/api/v1/runs/' + run['id'] + '/report.md', token=token)[0]
assert b'Offline smoke account' in markdown
assert json.loads(call('/api/v1/runs', token=token)[0])[0]['id'] == run['id']
print('Container workflow passed: registration, catalog, queue, worker, report, history and export.')
'''


def main():
    local_url = make_url(os.environ["OCTODIG_TEST_DATABASE_URL"])
    container_url = make_url(os.environ["OCTODIG_CONTAINER_TEST_DATABASE_URL"])
    for url in (local_url, container_url):
        if url.get_backend_name() != "postgresql" or not (url.database or "").endswith("_test"):
            raise ValueError("Container checks require disposable PostgreSQL databases ending in _test")
    if local_url.database != container_url.database:
        raise ValueError("Local and container database names must match")
    executable = os.environ.get("OCTODIG_TEST_DOCKER_BIN", "docker")
    suffix = uuid.uuid4().hex
    schema = f"octodig_smoke_{suffix}"
    network = f"octodig-smoke-{suffix}"
    containers = []
    engine = create_engine(local_url)

    def docker(*arguments, check=True, timeout=60):
        result = subprocess.run([executable, *arguments], capture_output=True, text=True, timeout=timeout)
        if check and result.returncode != 0:
            # Do not echo arbitrary command output, arguments, URLs or credentials.
            raise RuntimeError(f"Container smoke operation failed: {arguments[0]}")
        return result

    restrictions = ["--read-only", "--tmpfs", "/tmp", "--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        connection.execute(text(f'CREATE TABLE "{schema}".smoke_ownership (marker TEXT NOT NULL)'))
        connection.execute(text(f'INSERT INTO "{schema}".smoke_ownership VALUES (:marker)'), {"marker": suffix})
    try:
        with tempfile.TemporaryDirectory(prefix="octodig-smoke-") as directory:
            env_path = Path(directory) / "fixture.env"
            database = container_url.update_query_dict({"options": f"-csearch_path={schema}"})
            values = {"OCTODIG_DATABASE_URL": database.render_as_string(hide_password=False),
                      "OCTODIG_ENVIRONMENT": "production", "JWT_SECRET": secrets.token_urlsafe(48),
                      "OCTODIG_CORS_ORIGINS": "https://smoke.example.test",
                      "OPENAI_API_KEY": "", "GOOGLE_API_KEY": "", "OCTODIG_WORKER_POLL_SECONDS": "0.2"}
            env_path.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n")
            env_path.chmod(0o600)
            native_path = str(env_path)
            if executable.endswith(".exe"):
                native_path = subprocess.check_output(["wslpath", "-w", str(env_path)], text=True).strip()
            env_args = ["--env-file", native_path]
            ownership = (
                "from octodig.db import engine; from sqlalchemy import text; "
                f"c=engine.connect(); assert c.scalar(text('SELECT current_schema()')) == '{schema}'; "
                f"assert c.scalar(text('SELECT marker FROM smoke_ownership')) == '{suffix}'; c.close()"
            )
            docker("run", "--rm", *restrictions, *env_args, "octodig-api:verification", "python", "-c", ownership)
            docker("run", "--rm", *restrictions, *env_args, "octodig-api:verification", "alembic", "upgrade", "head")
            docker("network", "create", network)

            def start(service, image, *command, environment=False):
                name = f"octodig-smoke-{service}-{suffix}"
                containers.append(name)
                docker("run", "-d", "--name", name, "--network", network, "--network-alias", service,
                       *restrictions, *(env_args if environment else []), image, *command)
                return name

            api = start("api", "octodig-api:verification", environment=True)
            start("worker", "octodig-api:verification", "python", "-m", "octodig.worker", environment=True)
            frontend = start("frontend", "octodig-frontend:verification")
            for name in (api, frontend):
                assert docker("exec", name, "id", "-u").stdout.strip() != "0", "Runtime must not use root"
            readiness = "from urllib.request import urlopen; urlopen('http://api:8000/health/ready', timeout=3)"
            deadline = time.monotonic() + 30
            while docker("exec", api, "python", "-c", readiness, check=False).returncode:
                if time.monotonic() >= deadline:
                    raise RuntimeError("Container API did not become ready")
                time.sleep(0.3)
            result = docker("exec", api, "python", "-c", CLIENT_CHECK)
            print(result.stdout.strip())
    finally:
        for name in reversed(containers):
            docker("rm", "-f", name, check=False)
        docker("network", "rm", network, check=False)
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


if __name__ == "__main__":
    main()
