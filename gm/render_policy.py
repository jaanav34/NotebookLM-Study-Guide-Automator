import argparse
import sys
import re
import json
import os
import subprocess
import uuid
from datetime import datetime
from rich.live import Live
from rich.panel import Panel
from rich.console import Console, Group
from rich.syntax import Syntax
import dotenv
dotenv.load_dotenv()

import google.generativeai as genai

console = Console()

class LogManager:
    def __init__(self):
        self.logs = []
        self.live = Live(console=console, auto_refresh=False)
        self.model_counts = {}

    def __enter__(self):
        self.live.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.live.stop()

    def log(self, message, level="INFO"):
        log_entry = {
            "ts": datetime.now().isoformat(),
            "level": level,
            "msg": message,
        }
        self.logs.append(json.dumps(log_entry))
        self.update_display()

    def update_sticky(self):
        sticky_message = " | ".join([f"{model}: {count}" for model, count in self.model_counts.items()])
        return Panel(sticky_message, title="Gemini API Usage", border_style="blue")

    def update_display(self):
        from rich.console import Group
        log_panel = Panel("\n".join(self.logs), title="Logs", border_style="green")
        sticky_panel = self.update_sticky()
        self.live.update(Group(sticky_panel, log_panel))
        self.live.refresh()


class ManimCodeGenerator:
    """Generates Manim code from a manifest scene."""

    def __init__(self, gemini_api_key, log_manager):
        genai.configure(api_key=gemini_api_key) # type: ignore
        self.model = genai.GenerativeModel('gemini-2.5-pro') # type: ignore
        self.log_manager = log_manager

    def _build_prompt(self, scene_data, style_preset, narration_text):
        # This prompt is inspired by marcelo-earth-generative-manim-8a5edab282632443.txt
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
        prompt += "*   Use `with self.voiceover(text=...) as tracker:` to synchronize animations with narration.\n"
        prompt += "*   Keep the code clean and readable.\n\n"
        prompt += "**Example of a simple scene:**\n"
        prompt += "```python\n"
        prompt += "from manim import *\n"
        prompt += "from manim_voiceover import VoiceoverScene\n"
        prompt += "from manim_voiceover.services.gtts import GTTSService\n\n"
        prompt += "class ExampleScene(VoiceoverScene):\n"
        prompt += "    def construct(self):\n"
        prompt += "        self.set_speech_service(GTTSService())\n"
        prompt += "        circle = Circle()\n"
        prompt += "        with self.voiceover(text=\"This is a circle.\") as tracker:\n"
        prompt += "            self.play(Create(circle), run_time=tracker.duration)\n"
        prompt += "        self.wait()\n"
        prompt += "```\n\n"
        prompt += f"**Now, generate the Manim script for the scene {scene_data['manim_scene_name']}.**\n"
        return prompt

    def generate_code(self, scene_data, style_preset, narration_text):
        """Generates and returns the Manim code for a single scene."""
        self.log_manager.log(f"Generating code for scene: {scene_data['manim_scene_name']}")
        prompt = self._build_prompt(scene_data, style_preset, narration_text)
        try:
            model_name = self.model._model_name
            self.log_manager.model_counts[model_name] = self.log_manager.model_counts.get(model_name, 0) + 1
            response = self.model.generate_content(prompt)
            # The response might contain markdown ```python ... ```, so we need to extract the code.
            code = response.text
            match = re.search(r"```python\n(.*?)\n```", code, re.DOTALL)
            if match:
                self.log_manager.log(f"Successfully generated code for scene: {scene_data['manim_scene_name']}")
                return match.group(1)
            self.log_manager.log(f"Successfully generated code for scene: {scene_data['manim_scene_name']}")
            return code # If no markdown block is found, return the whole response.
        except Exception as e:
            self.log_manager.log(f"Error generating code from Gemini API for scene {scene_data['manim_scene_name']}: {e}", level="ERROR")
            return None



class VideoRenderer:
    """Renders a Manim script to a video file."""

    def __init__(self, log_manager, output_dir="renders", generated_scripts_dir="generated_manim_scripts"):
        self.output_dir = output_dir
        self.generated_scripts_dir = generated_scripts_dir
        self.log_manager = log_manager
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

    def render_scene(self, manim_script_content, scene_name, render_settings):
        """Renders a single scene and returns the path to the video file."""
        self.log_manager.log(f"Rendering scene: {scene_name}")
        script_path = os.path.join(self.generated_scripts_dir, f"{scene_name}.py")
        with open(script_path, "w") as f:
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
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "File ready at" in line:
                    video_path = line.split("File ready at")[-1].strip()
                    self.log_manager.log(f"Successfully rendered scene: {scene_name}")
                    return video_path
            self.log_manager.log("Could not find video path in Manim output.", level="ERROR")
            return None
        except subprocess.CalledProcessError as e:
            self.log_manager.log(f"Error rendering scene: {scene_name}", level="ERROR")
            self.log_manager.log(f"Stdout: {e.stdout}", level="ERROR")
            self.log_manager.log(f"Stderr: {e.stderr}", level="ERROR")
            return None

    def combine_videos(self, video_paths, output_filename):
        """Combines multiple video files into a single video using ffmpeg."""
        self.log_manager.log(f"Combining {len(video_paths)} videos")
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
            output_path
        ]

        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            self.log_manager.log(f"Successfully combined videos: {output_filename}")
            return output_path
        except subprocess.CalledProcessError as e:
            self.log_manager.log(f"Error combining videos: {e.stderr}", level="ERROR")
            return None


def render_video_from_manifest(manifest_path, quality, gemini_api_key):
    """
    Renders a video from a manifest file.
    """
    with LogManager() as log_manager:
        log_manager.log(f"Starting video rendering process for manifest: {manifest_path}")
        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
        except FileNotFoundError:
            log_manager.log(f"Manifest file not found at: {manifest_path}", level="ERROR")
            return
        except json.JSONDecodeError:
            log_manager.log(f"Invalid JSON in manifest file: {manifest_path}", level="ERROR")
            return

        code_generator = ManimCodeGenerator(gemini_api_key=gemini_api_key, log_manager=log_manager)
        renderer = VideoRenderer(log_manager=log_manager)

        scene_video_paths = []
        for scene in manifest.get("scenes", []):
            scene_id = scene.get("scene_id")
            if not scene_id:
                log_manager.log("Scene missing 'scene_id'", level="WARNING")
                continue

            narration_text = manifest.get("narration", {}).get("text_per_scene", {}).get(scene_id, "")
            manim_code = code_generator.generate_code(scene, manifest.get("style", {}), narration_text)

            if manim_code:
                render_settings = manifest.get("render_settings", {})
                video_path = renderer.render_scene(manim_code, scene["manim_scene_name"], render_settings)
                if video_path:
                    scene_video_paths.append(video_path)
                else:
                    log_manager.log(f"Failed to render scene: {scene_id}", level="ERROR")
                    return
            else:
                log_manager.log(f"Failed to generate code for scene: {scene_id}", level="ERROR")
                return

        if scene_video_paths:
            final_video_filename = f"{manifest.get('chapter_id', 'video')}_{quality}.mp4"
            final_video_path = renderer.combine_videos(scene_video_paths, final_video_filename)
            if final_video_path:
                log_manager.log(f"Final video rendered successfully: {final_video_path}")
                # Here you would update the manifest metadata
            else:
                log_manager.log("Failed to combine scene videos.", level="ERROR")
        else:
            log_manager.log("No scenes were rendered.", level="WARNING")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a video from a Manim manifest.")
    parser.add_argument("--manifest", required=True, help="Path to the manifest JSON file.")
    parser.add_argument("--quality", choices=["low", "high"], default="high", help="Render quality.")
    parser.add_argument("--gemini-api-key", help="Gemini API key.", default=os.environ.get("GEMINI_API_KEY"))
    args = parser.parse_args()

    if not args.gemini_api_key:
        console.print("[bold red]Error:[/ ] Gemini API key not found. Please set the GEMINI_API_KEY environment variable or provide it with the --gemini-api-key argument.")
        sys.exit(1)

    render_video_from_manifest(args.manifest, args.quality, args.gemini_api_key)
