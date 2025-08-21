import pytest
import json
import os
from unittest.mock import MagicMock, patch
from gm.render_policy import ManimCodeGenerator, VideoRenderer, render_video_from_manifest

# Mock for ManimCodeGenerator
class MockManimCodeGenerator:
    def generate_manim_code(self, text_content, animation_suggestions, manim_docs_context):
        return {
            "imports": "from manim import *\nfrom manim_voiceover import VoiceoverScene\nfrom manim_voiceover.services.gtts import GTTSService",
            "class_definition": "class GenScene(VoiceoverScene):",
            "construct_method": f"""
    def construct(self):
        self.set_speech_service(GTTSService())
        text = Text(\"{text_content}\").scale(0.8)
        with self.voiceover(text=f\"Narrating: {text_content}\") as tracker:
            self.play(Write(text), run_time=tracker.duration)
        self.wait(1)
"""
        }

# Mock for VideoRenderer
class MockVideoRenderer:
    def render_video(self, manim_code, render_settings, output_path, subtitle_option=None):
        # Simulate successful video creation
        with open(output_path, 'w') as f:
            f.write("Simulated video content")
        if subtitle_option == "srt":
            with open(output_path.replace(".mp4", ".srt"), 'w') as f:
                f.write("Simulated subtitle content")
        return True

@pytest.fixture
def mock_render_components(monkeypatch):
    monkeypatch.setattr("gm.render_policy.ManimCodeGenerator", MockManimCodeGenerator)
    monkeypatch.setattr("gm.render_policy.VideoRenderer", MockVideoRenderer)

def test_render_video_from_manifest_happy_path(mock_render_components, tmp_path):
    manifest_content = {
        "manifest_id": "test-manifest-id",
        "source_chapter": "test_chapter.md",
        "chapter_section": "test_section",
        "chapter_id": "test_chapter_id",
        "title": "Test Title",
        "scenes": [
            {
                "scene_id": "scene_1",
                "type": "explanation",
                "manim_scene_name": "Scene1",
                "text_content": "This is the first scene."
            },
            {
                "scene_id": "scene_2",
                "type": "example",
                "manim_scene_name": "Scene2",
                "text_content": "This is the second scene."
            }
        ],
        "render_settings": {
            "low_quality": { "resolution": "854x480", "fps": 15 },
            "high_quality": { "resolution": "1920x1080", "fps": 30, "subtitles": "srt" }
        },
        "narration": {
            "provider": "google",
            "voice": "echo",
            "text_per_scene": {
                "scene_1": "Narration for scene 1.",
                "scene_2": "Narration for scene 2."
            }
        },
        "metadata": {
            "created_by": "test",
            "created_at": "2025-01-01T00:00:00Z",
            "notebooklm_version": "1.0"
        },
        "validation_hash": "hash"
    }
    manifest_file = tmp_path / "test_manifest.json"
    manifest_file.write_text(json.dumps(manifest_content))

    # Ensure the 'renders' directory exists for the test output
    renders_dir = tmp_path / "renders"
    renders_dir.mkdir()

    result = render_video_from_manifest(str(manifest_file), output_base_dir=tmp_path)
    assert result is True
    assert (renders_dir / "test_chapter_id_final.mp4").exists()
    assert (renders_dir / "test_chapter_id_final.srt").exists()

def test_render_video_from_manifest_file_not_found():
    with pytest.raises(FileNotFoundError, match="Manifest file not found"):
        render_video_from_manifest("non_existent_manifest.json")

def test_render_video_from_manifest_invalid_json(tmp_path):
    manifest_file = tmp_path / "invalid_manifest.json"
    manifest_file.write_text("{\"key\": \"value") # Invalid JSON
    with pytest.raises(json.JSONDecodeError):
        render_video_from_manifest(str(manifest_file))