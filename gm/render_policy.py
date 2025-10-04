import argparse
import sys
import re
import json
import os
import subprocess
import uuid
from datetime import datetime
import structlog
import dotenv
dotenv.load_dotenv()

import google.generativeai as genai

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger()

class ManimCodeGenerator:
    """Generates Manim code from a manifest scene."""

    def __init__(self, gemini_api_key):
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def _build_prompt(self, scene_data, style_preset, narration_text):
        prompt = "You are a senior Manim developer. Your task is to write a Python script for a single Manim scene.\n\n"
        prompt += "**Persona:**\n"
        prompt += "*   You are an expert in Manim, with deep knowledge of animations, camera controls, and best practices.\n"
        prompt += "*   You write clean, readable, and well-commented code.\n"
        prompt += "*   You are familiar with `manim-voiceover` for adding narration.\n\n"
        prompt += "**Instructions:**\n"
        prompt += f"1.  Create a Python script for a Manim scene class named {scene_data['manim_scene_name']}.\n"
        prompt += "2.  The scene should inherit from `VoiceoverScene`.\n"
        prompt += "3.  Use the `GTTSService` for text-to-speech.\n"
        prompt += f"4.  The scene should visually explain the following content: \"{scene_data['text_content']}\"\n"
        prompt += f"5.  Use the following narration for the scene: \"{narration_text}\"\n"
        prompt += f"6.  Consider the following animation suggestions: {scene_data.get('animation_suggestions', 'None')}\n"
        prompt += f"7.  The visual style should be consistent with the {style_preset} preset.\n"
        prompt += "8.  The generated code should be a single Python script. Do not add any explanations before or after the code.\n\n"
        prompt += "**Manim Code Style Guide:**\n"
        prompt += "*   Use `self.play(...)` for animations.\n"
        prompt += "*   Use `self.wait(...)` for pauses.\n"
        prompt += "*   For positioning mobjects, use methods like `center()`, `to_edge()`, `next_to()`, `align_to()`, etc. directly on the mobject. Avoid chaining `.to_center()` or similar methods. Do NOT use `center_x()`, `center_y()`, `shift_x()`, `shift_y()` as direct methods on Mobjects; instead, use `mobject.to_center()` or `mobject.shift(RIGHT * x)` for positioning.\n"
        prompt += "*   Use `with self.voiceover(text=...) as tracker:` to synchronize animations with narration. After the animation, ensure the scene waits for the full duration of the voiceover using `self.wait(tracker.duration)`. When setting `run_time` for animations synchronized with voiceovers, use `run_time=tracker.duration` directly; do NOT use `get_remaining_duration_for` or similar methods.\n"
        prompt += "*   Ensure all necessary Manim classes and functions are imported at the beginning of the script (e.g., `from manim import *`). Specifically, `Grid` and `MobjectTable` are available through `from manim import *` and should not be imported from `manim.mobject.table` directly. For specialized classes not covered by `from manim import *`, import them explicitly from their respective submodules.\n"
        prompt += "*   When working with grid-like structures (e.g., `Grid` or `MobjectTable`), access rows and columns using their documented methods (e.g., `grid.get_rows()`, `grid.get_columns()`). Ensure the object is indeed a `Grid` or `MobjectTable` before attempting to use these methods. If it's a `VGroup` of Mobjects arranged in a grid, access elements by indexing or iterating.\n"
        prompt += "*   For positioning, use standard Manim constants like `LEFT`, `RIGHT`, `UP`, `DOWN`, `ORIGIN`, etc. Do NOT use non-standard constants like `LEFT_SIDE_OF_SCREEN` or similar.\n"
        prompt += "*   When transforming between Mobjects, choose the appropriate animation. Use `TransformMatchingTex` (from `manim.animation.transform_matching_parts`) ONLY for `MathTex` objects or `Text` objects created from LaTeX strings. For transforming between general `Text` objects, use `Transform` (from `manim.animation.transform`) or `TransformMatchingStrings` if the text content is similar.\n"
        prompt += "*   When manipulating parts of a `Text` Mobject, use indexing/slicing (e.g., `text[0:5]`) or the `t2c`, `t2f`, `t2s`, `t2w` arguments during `Text` object creation. For example, to color specific words, use `Text(\"Hello World\", t2c={'Hello': BLUE, 'World': RED})`. Do NOT use `get_parts_by_text`, `get_parts_by_string`, or any similar methods, as they are not standard Manim methods for `Text` objects.\n"
        prompt += "*   For scene dimensions, use `self.camera.frame_width` and `self.camera.frame_height` instead of global `FRAME_WIDTH` and `FRAME_height`.\n"
        prompt += "*   If using `Grid`, ensure it is imported from `manim.mobject.geometry` (e.g., `from manim.mobject.geometry import Grid`).\n"
        prompt += "*   When highlighting parts of a `Text` Mobject, do NOT use `get_submob_by_string`. Instead, create a new `Text` Mobject for the specific part you want to highlight and position it over the original text, or use `Text.get_part_by_string` if available and appropriate for the Manim version.\n"
        prompt += "*   When using `t2c` (text-to-color) in `Text` objects, ensure there are no overlapping color definitions for the same text segments to avoid `ValueError: Ambiguous style for text` errors.\n"
        prompt += "*   When positioning a `Text` Mobject, use `text.center()` or `text.to_edge()` as separate calls after the `Text` object has been created. Do NOT chain `.to_center()` or similar positioning methods directly after the `Text` constructor.\n\n"
        prompt += "**Example of a simple scene:**\n"
        prompt += "```python\n"
        prompt += "from manim import *\n"
        prompt += "from manim_voiceover import VoiceoverScene\n"
        prompt += "from manim_voiceover.services.gtts import GTTSService\n\n"
        prompt += "class ExampleScene(VoiceoverScene):\n"
        prompt += "    def construct(self):\n"
        prompt += "        self.set_speech_service(GTTSService())\n"
        prompt += "        text = Text(\"Hello, Manim!\")\n"
        prompt += "        text.center()\n"
        prompt += "        with self.voiceover(text=\"This is a simple text example.\") as tracker:\n"
        prompt += "            self.play(Write(text), run_time=tracker.duration)\n"
        prompt += "        self.wait(tracker.duration)\n"
        prompt += "```\n\n"
        prompt += f"**Now, generate the Manim script for the scene {scene_data['manim_scene_name']}.**\n"
        return prompt

    def generate_code(self, scene_data, style_preset, narration_text):
        """Generates and returns the Manim code for a single scene."""
        log.info("Generating code for scene", scene=scene_data['manim_scene_name'])
        prompt = self._build_prompt(scene_data, style_preset, narration_text)
        try:
            response = self.model.generate_content(prompt)
            code = response.text
            match = re.search(r"```python\n(.*?)\n```", code, re.DOTALL)
            if match:
                log.info("Successfully generated code for scene", scene=scene_data['manim_scene_name'])
                return match.group(1)
            log.info("Successfully generated code for scene", scene=scene_data['manim_scene_name'])
            return code
        except Exception as e:
            log.error("Error generating code from Gemini API", scene=scene_data['manim_scene_name'], error=str(e))
            return None

class VideoRenderer:
    """Renders a Manim script to a video file."""

    def __init__(self, output_dir="renders", generated_scripts_dir="generated_manim_scripts"):
        self.output_dir = output_dir
        self.generated_scripts_dir = generated_scripts_dir
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

    def render_scene(self, manim_script_content, scene_name, render_settings):
        """Renders a single scene and returns the path to the video file."""
        log.info("Rendering scene", scene=scene_name)
        script_path = os.path.join(self.generated_scripts_dir, f"{scene_name}.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(manim_script_content)

        quality_flag = "-ql" if render_settings.get("quality", "low") == "low" else "-qh"

        command = [
            sys.executable,
            "-m",
            "manim",
            script_path,
            scene_name,
            quality_flag,
            "--media_dir", self.output_dir
        ]

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='latin-1')
            log.info("Manim execution successful", scene=scene_name)
            
            output = result.stdout
            error_output = result.stderr

            if error_output:
                filtered_error_output = "\n".join([line for line in error_output.splitlines() if line.strip()])
                if filtered_error_output:
                    log.warning("Manim stderr output", scene=scene_name, stderr=filtered_error_output)

            video_path_match = re.search(r"File ready at\s*(.+)", output)
            if video_path_match:
                video_path = video_path_match.group(1).replace('\n', '').replace('\r', '').strip()
                video_path = os.path.normpath(video_path.strip("'"))
                log.info("Successfully rendered scene", scene=scene_name, path=video_path)
                return video_path
            else:
                log.error("Could not find video path in Manim output", scene=scene_name, stdout=output)
                return None

        except subprocess.CalledProcessError as e:
            log.error(
                "Error rendering scene",
                scene=scene_name,
                return_code=e.returncode,
                stdout="\n".join([line for line in e.stdout.splitlines() if line.strip()]),
                stderr="\n".join([line for line in e.stderr.splitlines() if line.strip()])
            )
            
            return None
        except FileNotFoundError:
            log.error("Manim command not found. Make sure Manim is installed and in your PATH.")
            return None

    def combine_videos(self, video_paths, output_filename):
        """Combines multiple video files into a single video using ffmpeg."""
        log.info("Combining videos", count=len(video_paths))
        output_path = os.path.join(self.output_dir, output_filename)
        input_files_path = os.path.join(self.generated_scripts_dir, "input_files.txt")

        with open(input_files_path, "w") as f:
            for path in video_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")

        command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", input_files_path,
            "-c", "copy",
            output_path,
            "-y" # Overwrite output file if it exists
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            log.info("Successfully combined videos", output_path=output_path)
            return output_path
        except subprocess.CalledProcessError as e:
            log.error("Error combining videos", error=e.stderr)
            return None
        except FileNotFoundError:
            log.error("ffmpeg command not found. Make sure ffmpeg is installed and in your PATH.")
            return None


def render_video_from_manifest(manifest_path, quality, gemini_api_key):
    """
    Renders a video from a manifest file.
    """
    log.info("Starting video rendering process", manifest=manifest_path)
    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        log.error("Manifest file not found", path=manifest_path)
        return
    except json.JSONDecodeError:
        log.error("Invalid JSON in manifest file", path=manifest_path)
        return

    code_generator = ManimCodeGenerator(gemini_api_key=gemini_api_key)
    renderer = VideoRenderer()

    scene_video_paths = []
    for scene in manifest.get("scenes", []):
        scene_id = scene.get("scene_id")
        if not scene_id:
            log.warning("Scene missing 'scene_id'")
            continue

        narration_text = manifest.get("narration", {}).get("text_per_scene", {}).get(scene_id, "")
        manim_code = code_generator.generate_code(scene, manifest.get("style", {}), narration_text)

        if manim_code:
            render_settings = manifest.get("render_settings", {}).get(f"{quality}_quality", {})
            video_path = renderer.render_scene(manim_code, scene["manim_scene_name"], render_settings)
            if video_path:
                scene_video_paths.append(video_path)
            else:
                log.error("Failed to render scene", scene=scene_id)
                return # Stop the process if a scene fails
        else:
            log.error("Failed to generate code for scene", scene=scene_id)
            return # Stop the process if code generation fails

    if scene_video_paths:
        final_video_filename = f"{manifest.get('chapter_id', 'video')}_{quality}.mp4"
        final_video_path = renderer.combine_videos(scene_video_paths, final_video_filename)
        if final_video_path:
            log.info("Final video rendered successfully", path=final_video_path)
            # TODO: Update manifest metadata (created_at, validation_hash)
        else:
            log.error("Failed to combine scene videos")
    else:
        log.warning("No scenes were rendered")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a video from a Manim manifest.")
    parser.add_argument("--manifest", required=True, help="Path to the manifest JSON file.")
    parser.add_argument("--quality", choices=["low", "high"], default="low", help="Render quality.")
    parser.add_argument("--gemini-api-key", help="Gemini API key.", default=os.environ.get("GEMINI_API_KEY"))
    args = parser.parse_args()

    if not args.gemini_api_key:
        print("Error: Gemini API key not found. Please set the GEMINI_API_KEY environment variable or provide it with the --gemini-api-key argument.")
        sys.exit(1)

    render_video_from_manifest(args.manifest, args.quality, args.gemini_api_key)