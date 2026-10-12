from octodig.models import RunStatus
from octodig.settings import Settings


def test_worker_recovery_has_a_bounded_retry_limit() -> None:
    settings = Settings()

    assert settings.run_max_attempts == 3
    assert settings.run_max_attempts > 0
    assert RunStatus.FAILED == "failed"
