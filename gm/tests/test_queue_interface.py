import pytest
import os
from gm.queue_interface import add_to_queue, get_next_job, mark_job_complete, QUEUE_FILE

@pytest.fixture(autouse=True)
def setup_and_teardown_queue_file():
    # Setup: Ensure queue file is clean before each test
    if os.path.exists(QUEUE_FILE):
        os.remove(QUEUE_FILE)
    yield
    # Teardown: Clean up queue file after each test
    if os.path.exists(QUEUE_FILE):
        os.remove(QUEUE_FILE)

def test_add_to_queue_new_manifest():
    assert add_to_queue("manifests/manifest1.json") is True
    with open(QUEUE_FILE, 'r') as f:
        content = f.read()
    assert "manifests/manifest1.json" in content

def test_add_to_queue_existing_manifest():
    add_to_queue("manifests/manifest1.json")
    assert add_to_queue("manifests/manifest1.json") is False # Should not add duplicate
    with open(QUEUE_FILE, 'r') as f:
        content = f.readlines()
    assert len(content) == 1 # Should still only have one line

def test_get_next_job_empty_queue():
    assert get_next_job() is None

def test_get_next_job_non_empty_queue():
    add_to_queue("manifests/manifest1.json")
    add_to_queue("manifests/manifest2.json")
    assert get_next_job() == "manifests/manifest1.json"

def test_mark_job_complete_existing_manifest():
    add_to_queue("manifests/manifest1.json")
    add_to_queue("manifests/manifest2.json")
    assert mark_job_complete("manifests/manifest1.json") is True
    assert get_next_job() == "manifests/manifest2.json"
    with open(QUEUE_FILE, 'r') as f:
        content = f.read()
    assert "manifests/manifest1.json" not in content
    assert "manifests/manifest2.json" in content

def test_mark_job_complete_non_existent_manifest():
    add_to_queue("manifests/manifest1.json")
    assert mark_job_complete("manifests/manifest3.json") is False
    with open(QUEUE_FILE, 'r') as f:
        content = f.read()
    assert "manifests/manifest1.json" in content # Should not have changed

def test_queue_fifo_order():
    add_to_queue("manifests/manifestA.json")
    add_to_queue("manifests/manifestB.json")
    add_to_queue("manifests/manifestC.json")

    assert get_next_job() == "manifests/manifestA.json"
    mark_job_complete("manifests/manifestA.json")

    assert get_next_job() == "manifests/manifestB.json"
    mark_job_complete("manifests/manifestB.json")

    assert get_next_job() == "manifests/manifestC.json"
    mark_job_complete("manifests/manifestC.json")

    assert get_next_job() is None
