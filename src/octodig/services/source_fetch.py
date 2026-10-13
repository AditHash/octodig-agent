"""Bounded HTTPS retrieval with DNS validation and pinned connection addresses."""

import http.client
import ipaddress
import socket
import ssl
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit


class SourceFetchError(ValueError):
    pass


def public_destination(url: str) -> tuple[str, str, str]:
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise SourceFetchError("Evidence URL must be public HTTPS without credentials")
    if parts.port not in {None, 443}:
        raise SourceFetchError("Evidence URL must use the standard HTTPS port")
    host = parts.hostname
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise SourceFetchError("Source DNS resolution failed") from exc
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise SourceFetchError("Source resolves to a non-public destination")
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return host, addresses[0][4][0], path


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def fetch_public_text(url: str, *, max_bytes: int = 512_000, timeout: int = 8, max_redirects: int = 3) -> tuple[str, str]:
    deadline = time.monotonic() + timeout
    for redirect in range(max_redirects + 1):
        if time.monotonic() >= deadline:
            raise SourceFetchError("Evidence retrieval time limit exceeded")
        host, address, path = public_destination(url)
        connection = http.client.HTTPSConnection(host, timeout=timeout, context=ssl.create_default_context())
        # TLS still verifies the original hostname. The socket connects only to
        # the validated IP, so a second DNS answer cannot redirect the request.
        connection._create_connection = lambda *_args, **_kwargs: socket.create_connection((address, 443), timeout)
        try:
            connection.request("GET", path, headers={"User-Agent": "OctoDig/0.1 public-evidence", "Accept-Encoding": "identity"})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location or redirect == max_redirects:
                    raise SourceFetchError("Source redirect limit exceeded")
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise SourceFetchError("Source is unavailable")
            content_type = response.getheader("Content-Type", "").split(";")[0].strip().lower()
            if content_type not in {"text/html", "text/plain"}:
                raise SourceFetchError("Unsupported evidence content type")
            chunks = []
            total = 0
            while total <= max_bytes:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise SourceFetchError("Evidence retrieval time limit exceeded")
                if connection.sock is not None:
                    connection.sock.settimeout(remaining)
                chunk = response.read1(min(64_000, max_bytes + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
            payload = b"".join(chunks)
            if len(payload) > max_bytes:
                raise SourceFetchError("Source exceeds response-size limit")
            decoded = payload.decode("utf-8", errors="replace")
            if content_type == "text/html":
                parser = VisibleText()
                parser.feed(decoded)
                decoded = " ".join(parser.parts)
            return url, " ".join(decoded.split())
        except (OSError, http.client.HTTPException) as exc:
            raise SourceFetchError("Evidence retrieval failed") from exc
        finally:
            connection.close()
    raise SourceFetchError("Source redirect limit exceeded")
