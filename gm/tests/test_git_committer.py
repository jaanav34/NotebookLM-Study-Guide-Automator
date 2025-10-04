import pytest
import json
import os
import subprocess
from unittest.mock import patch, MagicMock
from gm.git_committer import commit_manifest, run_git_command

# Helper to create a dummy manifest file
@pytest.fixture
def dummy_manifest_file(tmp_path):
    manifest_content = {
        "chapter_id": "test_chapter",
        "chapter_section": "test_section_1",
        "manifest_id": "123-abc",
        "title": "Test Chapter Title",
        "scenes": []
    }
    file_path = tmp_path / "test_manifest.json"
    file_path.write_text(json.dumps(manifest_content))
    return file_path

# Test successful commit
def test_commit_manifest_success(dummy_manifest_file):
    with patch('subprocess.run') as mock_subprocess_run:
        mock_subprocess_run.return_value = MagicMock(stdout="", stderr="")
        
        commit_manifest(str(dummy_manifest_file))
        
        # Assert git commands were called correctly
        mock_subprocess_run.assert_any_call(
            "git checkout -b feature/manim-manifest-test_chapter",
            shell=True, check=True, capture_output=True, text=True
        )
        mock_subprocess_run.assert_any_call(
            f"git add {dummy_manifest_file}",
            shell=True, check=True, capture_output=True, text=True
        )
        mock_subprocess_run.assert_any_call(
            "git commit -m \"feat(manim): add manifest for section test_section_1\"",
            shell=True, check=True, capture_output=True, text=True
        )

# Test FileNotFoundError
def test_commit_manifest_file_not_found():
    with pytest.raises(FileNotFoundError, match="Manifest file not found"):
        commit_manifest("non_existent_manifest.json")

# Test JSONDecodeError
def test_commit_manifest_invalid_json(tmp_path):
    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text("{\"key\": \"value") # Malformed JSON
    with pytest.raises(json.JSONDecodeError):
        commit_manifest(str(invalid_json_file))

# Test subprocess.CalledProcessError during git command execution
def test_commit_manifest_git_command_failure(dummy_manifest_file):
    with patch('subprocess.run') as mock_subprocess_run:
        # Simulate a git command failure
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd="git checkout", stderr="fatal: branch exists"
        )
        with pytest.raises(subprocess.CalledProcessError):
            commit_manifest(str(dummy_manifest_file))
