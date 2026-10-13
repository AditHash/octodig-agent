"""Run the committed Nginx production configuration against offline fixtures.

Requires a locally installed Nginx binary and MIME configuration. Does not require
root, Docker, customer data or provider credentials.
"""

import os
from pathlib import Path
import subprocess
import tempfile


def serve():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="octodig-proxy-") as directory:
        temporary = Path(directory)
        server = (root / "frontend/nginx.conf").read_text()
        server = server.replace("listen 8080;", "listen 127.0.0.1:5175;")
        server = server.replace("/usr/share/nginx/html", str(root / "frontend/dist"))
        server = server.replace("http://api:8000", "http://127.0.0.1:8801")
        (temporary / "server.conf").write_text(server)
        main = (root / "frontend/nginx-main.conf").read_text()
        main = main.replace("/tmp/", f"{directory}/")
        # Playwright uses socket-backed stdio, which Nginx cannot reopen as a log.
        main = main.replace("/dev/stderr", str(temporary / "error.log"))
        main = main.replace("/dev/stdout", str(temporary / "access.log"))
        main = main.replace("/etc/nginx/mime.types", os.environ.get("OCTODIG_TEST_NGINX_MIME", "/etc/nginx/mime.types"))
        main = main.replace("/etc/nginx/conf.d/*.conf", str(temporary / "server.conf"))
        (temporary / "nginx.conf").write_text(main)
        arguments = [os.environ["OCTODIG_TEST_NGINX_BIN"], "-p", directory, "-c", str(temporary / "nginx.conf")]
        subprocess.run([*arguments, "-t"], check=True)
        subprocess.run([*arguments, "-g", "daemon off;"], check=True)


if __name__ == "__main__":
    serve()
