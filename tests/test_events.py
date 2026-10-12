from octodig.api import _sse
from octodig.models import ResearchEvent


def test_sse_encodes_only_event_metadata() -> None:
    event = ResearchEvent(id="event_1", run_id="run_1", event_type="run.queued", data={"provider": "openai"})
    assert _sse(event) == 'id: event_1\nevent: run.queued\ndata: {"provider":"openai"}\n\n'
