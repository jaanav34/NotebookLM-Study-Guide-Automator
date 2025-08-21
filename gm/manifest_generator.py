import argparse
import json
import uuid
import os
from dotenv import load_dotenv
import google.generativeai as genai
import markdown

load_dotenv()

class GeminiAPI:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-pro')

    def generate_content(self, prompt):
        response = self.model.generate_content(prompt)
        # Assuming the response is a JSON string, parse it
        try:
            # The LLM might return markdown code block, so we need to extract the JSON
            text_content = response.text.strip()
            if text_content.startswith("```json") and text_content.endswith("```"):
                text_content = text_content[7:-3].strip()
            return json.loads(text_content)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Gemini API: {e}")
            print(f"Raw response text: {response.text}")
            raise

def extract_section_and_title(markdown_content, section_id):
    # This is a simplified markdown parser.
    # In a real implementation, a more robust parser would be used.
    lines = markdown_content.splitlines()
    section_content = []
    title = "Untitled Chapter"
    in_section = False

    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
        if line.strip() == f"## {section_id}": # Assuming sections are H2 with ID
            in_section = True
            continue
        if in_section and line.startswith("## "): # End of current section
            in_section = False
            break
        if in_section:
            section_content.append(line)

    return title, "\n".join(section_content).strip()

def generate_manifest(chapter_path, section_id):
    """
    Generates a manifest for a given chapter and section.
    """
    if not os.path.exists(chapter_path):
        raise FileNotFoundError(f"Chapter file not found: {chapter_path}")

    with open(chapter_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    title, section_content = extract_section_and_title(markdown_content, section_id)

    if not section_content:
        raise ValueError(f"Section '{section_id}' not found or is empty in {chapter_path}")

    gemini_api = GeminiAPI()
    prompt = f"""
    You are an expert in creating Manim video manifests from text.
    Analyze the following markdown content for a study guide section and break it down into logical \"scenes\" (e.g., introduction, example, explanation, derivation, diagram).
    For each scene, provide:
    - a unique `scene_id` (e.g., \"scene_1_intro\")
    - a `type` (enum: \"explanation\", \"example\", \"derivation\", \"diagram\")
    - a `manim_scene_name` (a descriptive name for the Manim class, e.g., \"KMapIntroduction\")
    - `text_content` (the relevant text for this scene)
    - a concise narration script for the scene.

    Return the output as a JSON object with a \"scenes\" array and a \"narration\" object.

    Example JSON structure:
    {{
      \"scenes\": [
        {{
          \"scene_id\": \"scene_1_intro\",
          \"type\": \"explanation\",
          \"manim_scene_name\": \"KMapIntroduction\",
          \"text_content\": \"Karnaugh Maps (K-Maps) provide a graphical method for simplifying Boolean expressions...\"
        }},
        {{
          \"scene_id\": \"scene_2_example\",
          \"type\": \"example\",
          \"manim_scene_name\": \"KMapExample\",
          \"text_content\": \"Exam Style Problem & Explanation (SoP Minimization with Don't Cares):...\"
        }}
      ],
      \"narration\": {{
        \"scene_1_intro\": \"Let's begin with an introduction to Karnaugh Maps...\",
        \"scene_2_example\": \"Now, let's walk through an example problem...\"
      }}
    }}

    Markdown Content for Section '{section_id}':
    {section_content}
    """
    response_data = gemini_api.generate_content(prompt)

    manifest = {
        "manifest_id": str(uuid.uuid4()),
        "source_chapter": chapter_path,
        "chapter_section": section_id,
        "title": title,
        "scenes": response_data.get("scenes", []),
        "render_settings": {
            "low_quality": { "resolution": "854x480", "fps": 15 },
            "high_quality": { "resolution": "1920x1080", "fps": 30 }
        },
        "narration": {
            "provider": "google", # Default provider
            "voice": "echo",     # Default voice
            "text_per_scene": response_data.get("narration", {})
        },
        "metadata": {
            "created_by": "gm_cli_v1",
            "created_at": "2025-08-20T19:00:00Z", # Placeholder, should be dynamic
            "notebooklm_version": "v1.2.3" # Placeholder
        },
        "validation_hash": "sha256:..." # Placeholder
    }

    return manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", required=True, help="Path to the chapter markdown file")
    parser.add_argument("--section", required=True, help="Section of the chapter to process")
    args = parser.parse_args()

    try:
        manifest = generate_manifest(args.chapter, args.section)

        chapter_base_name = os.path.splitext(os.path.basename(args.chapter))[0]
        output_filename = f"manifests/{chapter_base_name}_{args.section}.json"

        os.makedirs("manifests", exist_ok=True) # Ensure directory exists

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        print(f"Manifest generated at {output_filename}")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"Error generating manifest: {e}")
        exit(1)