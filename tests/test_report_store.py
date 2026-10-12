from octodig.services.report_store import storage_id


def test_storage_ids_are_stable_but_unique_across_runs_and_entity_kinds() -> None:
    source_id = storage_id("run_1", "source", "source_1")

    assert source_id == storage_id("run_1", "source", "source_1")
    assert source_id != storage_id("run_2", "source", "source_1")
    assert source_id != storage_id("run_1", "claim", "source_1")
    assert len(source_id) == 64
