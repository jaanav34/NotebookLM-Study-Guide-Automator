
import argparse
import json
import os
from jsonschema import validate, ValidationError

# The JSON schema for the manifest
MANIFEST_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Manim Video Manifest",
    "description": "A manifest file describing a Manim video to be rendered from a study guide chapter.",
    "type": "object",
    "properties": {
        "manifest_id": { "type": "string", "format": "uuid" },
        "source_chapter": { "type": "string" },
        "chapter_section": { "type": "string" },
        "title": { "type": "string" },
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scene_id": { "type": "string" },
                    "type": { "type": "string", "enum": ["explanation", "example", "derivation", "diagram"] },
                    "manim_scene_name": { "type": "string" },
                    "text_content": { "type": "string" },
                    "animation_suggestions": { "type": "object" }
                },
                "required": ["scene_id", "type", "manim_scene_name", "text_content"]
            }
        },
        "render_settings": {
            "type": "object",
            "properties": {
                "low_quality": {
                    "type": "object",
                    "properties": { "resolution": { "type": "string" }, "fps": { "type": "integer" } }
                },
                "high_quality": {
                    "type": "object",
                    "properties": { "resolution": { "type": "string" }, "fps": { "type": "integer" } }
                }
            }
        },
        "narration": {
            "type": "object",
            "properties": {
                "provider": { "type": "string" },
                "voice": { "type": "string" },
                "text": { "type": "string" },
                "text_per_scene": { "type": "object" }
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "created_by": { "type": "string" },
                "created_at": { "type": "string" },
                "notebooklm_version": { "type": "string" }
            },
            "required": ["created_by", "created_at", "notebooklm_version"]
        },
        "validation_hash": { "type": "string" }
    },
    "required": ["manifest_id", "source_chapter", "chapter_section", "title", "scenes", "render_settings"]
}

def validate_manifest(manifest_data):
    """
    Validates a manifest against the JSON schema and performs semantic checks.
    """
    try:
        validate(instance=manifest_data, schema=MANIFEST_SCHEMA)
    except ValidationError as e:
        print(f"Schema validation error: {e.message}")
        return False

    # Semantic checks
    scene_ids = {scene["scene_id"] for scene in manifest_data.get("scenes", [])}
    if "narration" in manifest_data and "text_per_scene" in manifest_data["narration"]:
        for narration_scene_id in manifest_data["narration"]["text_per_scene"]:
            if narration_scene_id not in scene_ids:
                print(f"Semantic validation error: Narration scene ID '{narration_scene_id}' not found in scenes.")
                return False

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate a Manim manifest JSON file.")
    parser.add_argument("manifest_path", help="Path to the manifest JSON file.")
    args = parser.parse_args()

    if not os.path.exists(args.manifest_path):
        print(f"Error: Manifest file not found at '{args.manifest_path}'")
        exit(1)

    try:
        with open(args.manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{args.manifest_path}'")
        exit(1)

    if validate_manifest(manifest_data):
        print(f"Manifest '{args.manifest_path}' is valid.")
        exit(0)
    else:
        print(f"Manifest '{args.manifest_path}' is invalid.")
        exit(1)
