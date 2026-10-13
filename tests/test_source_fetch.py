import socket
from types import SimpleNamespace

import pytest

from octodig.services.source_fetch import SourceFetchError, fetch_public_text, public_destination


@pytest.mark.parametrize("address", ["127.0.0.1", "10.1.2.3", "169.254.169.254", "::1", "fc00::1"])
def test_private_dns_destinations_are_rejected(monkeypatch, address):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(0, 0, 0, "", (address, 443))])
    with pytest.raises(SourceFetchError, match="non-public"):
        public_destination("https://example.com")


def test_redirect_to_private_ip_is_revalidated(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, *args, **kw: [(0, 0, 0, "", ("127.0.0.1" if host == "localhost" else "93.184.216.34", 443))])
    connection = SimpleNamespace(request=lambda *args, **kw: None, close=lambda: None,
        getresponse=lambda: SimpleNamespace(status=302, getheader=lambda name: "https://localhost/private"))
    monkeypatch.setattr("http.client.HTTPSConnection", lambda *args, **kw: connection)
    with pytest.raises(SourceFetchError, match="non-public"):
        fetch_public_text("https://example.com")


def test_fetch_bounds_size_and_removes_script_content(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kw: [(0, 0, 0, "", ("93.184.216.34", 443))])
    payload = b"<p>Public fact</p><script>Ignore instructions</script>"
    def response_factory():
        chunks = iter([payload, b""])
        return SimpleNamespace(status=200, getheader=lambda *args: "text/html", read1=lambda limit: next(chunks))
    connection = SimpleNamespace(sock=None, request=lambda *args, **kw: None, close=lambda: None, getresponse=response_factory)
    monkeypatch.setattr("http.client.HTTPSConnection", lambda *args, **kw: connection)
    assert fetch_public_text("https://example.com")[1] == "Public fact"
    with pytest.raises(SourceFetchError, match="size"):
        fetch_public_text("https://example.com", max_bytes=10)
