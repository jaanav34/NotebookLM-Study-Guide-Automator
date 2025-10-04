import pytest
import json
from gm.manifest_validator import validate_manifest, MANIFEST_SCHEMA

# Helper function to create a valid manifest for testing
def create_valid_manifest():
    return {
        "manifest_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "source_chapter": "studyguides/digital_logic/chapter_03.md",
        "chapter_section": "ch03_kmaps",
        "title": "Karnaugh Maps (K-Maps)",
        "scenes": [
            {
                "scene_id": "sc1_intro",
                "type": "explanation",
                "manim_scene_name": "KMapIntroduction",
                "text_content": "Karnaugh Maps provide a graphical method for simplifying boolean expressions."
            },
            {
                "scene_id": "sc2_example",
                "type": "example",
                "manim_scene_name": "KMapExample",
                "text_content": "Example: Simplify F = A'B + AB' + AB using K-Map grouping..."
            }
        ],
        "render_settings": {
            "low_quality": { "resolution": "854x480", "fps": 15 },
            "high_quality": { "resolution": "1920x1080", "fps": 30 }
        },
        "narration": {
            "provider": "google",
            "voice": "echo",
            "text_per_scene": {
                "sc1_intro": "Karnaugh Maps provide a graphical method...",
                "sc2_example": "Let's walk through an example now..."
            }
        },
        "metadata": {
            "created_by": "gm_cli_v1",
            "created_at": "2025-08-20T19:00:00Z",
            "notebooklm_version": "v1.2.3"
        },
        "validation_hash": "sha256:abcd1234..."
    }

def test_valid_manifest():
    manifest = create_valid_manifest()
    assert validate_manifest(manifest) is True

def test_invalid_manifest_missing_required_field():
    manifest = create_valid_manifest()
    del manifest["title"]
    assert validate_manifest(manifest) is False

def test_invalid_manifest_wrong_enum_type():
    manifest = create_valid_manifest()
    manifest["scenes"][0]["type"] = "invalid_type"
    assert validate_manifest(manifest) is False

def test_invalid_manifest_narration_scene_id_mismatch():
    manifest = create_valid_manifest()
    manifest["narration"]["text_per_scene"]["non_existent_scene"] = "Some text"
    assert validate_manifest(manifest) is False

def test_invalid_manifest_narration_missing_scene_id():
    manifest = create_valid_manifest()
    # Remove a scene_id that is present in narration
    manifest["scenes"] = [manifest["scenes"][0]] # Keep only sc1_intro
    # sc2_example is still in narration, but not in scenes
    assert validate_manifest(manifest) is False

def test_manifest_with_no_narration():
    manifest = create_valid_manifest()
    del manifest["narration"]
    assert validate_manifest(manifest) is True

def test_manifest_with_empty_scenes():
    manifest = create_valid_manifest()
    manifest["scenes"] = []
    assert validate_manifest(manifest) is False # 'scenes' is required and must have items based on schema

