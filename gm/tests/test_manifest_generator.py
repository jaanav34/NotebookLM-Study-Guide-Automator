import pytest
import json
from gm.manifest_generator import generate_manifest, GeminiAPI, extract_section_and_title
import os

# A mock for the Gemini API client
class MockGeminiAPI:
    def generate_content(self, prompt):
        # Simulate a realistic response from the Gemini API
        return {
            "scenes": [
                {
                    "scene_id": "scene_1_intro",
                    "type": "explanation",
                    "manim_scene_name": "KMapIntroduction",
                    "text_content": "Karnaugh Maps (K-Maps) provide a graphical method for simplifying Boolean expressions..."
                },
                {
                    "scene_id": "scene_2_example",
                    "type": "example",
                    "manim_scene_name": "KMapExample",
                    "text_content": "Exam Style Problem & Explanation (SoP Minimization with Don't Cares):..."
                }
            ],
            "narration": {
                "scene_1_intro": "Let's begin with an introduction to Karnaugh Maps...",
                "scene_2_example": "Now, let's walk through an example problem..."
            }
        }

@pytest.fixture
def mock_gemini_api(monkeypatch):
    monkeypatch.setattr("gm.manifest_generator.GeminiAPI", MockGeminiAPI)

def test_generate_manifest_happy_path(mock_gemini_api, tmp_path):
    chapter_content = """
# My Awesome Chapter

## section_1a
This is the content for section 1a.

## section_1b
This is the content for section 1b.
"""
    chapter_file = tmp_path / "test_chapter.md"
    chapter_file.write_text(chapter_content)

    manifest = generate_manifest(str(chapter_file), "section_1a")

    assert manifest is not None
    assert "manifest_id" in manifest
    assert manifest["source_chapter"] == str(chapter_file)
    assert manifest["chapter_section"] == "section_1a"
    assert manifest["title"] == "My Awesome Chapter"
    assert len(manifest["scenes"]) == 2 # Based on MockGeminiAPI response
    assert manifest["narration"]["text_per_scene"]["scene_1_intro"] == "Let's begin with an introduction to Karnaugh Maps..."

def test_generate_manifest_file_not_found():
    with pytest.raises(FileNotFoundError):
        generate_manifest("non_existent_file.md", "section_1a")

def test_generate_manifest_section_not_found(tmp_path):
    chapter_content = """
# My Awesome Chapter

## section_1a
This is the content for section 1a.
"""
    chapter_file = tmp_path / "test_chapter.md"
    chapter_file.write_text(chapter_content)

    with pytest.raises(ValueError, match="Section 'non_existent_section' not found or is empty"):
        generate_manifest(str(chapter_file), "non_existent_section")

def test_extract_section_and_title():
    markdown_content = """
# Chapter Title Example

Some introductory text.

## Section A
Content for section A.
Line 2 of section A.

## Section B
Content for section B.
"""
    title, section_content = extract_section_and_title(markdown_content, "Section A")
    assert title == "Chapter Title Example"
    assert section_content == "Content for section A.\nLine 2 of section A."

    title, section_content = extract_section_and_title(markdown_content, "Section B")
    assert title == "Chapter Title Example"
    assert section_content == "Content for section B."

    title, section_content = extract_section_and_title(markdown_content, "Non Existent Section")
    assert title == "Chapter Title Example"
    assert section_content == ""