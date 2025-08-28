import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os

from gm.render_policy import ManimCodeGenerator, VideoRenderer, render_video_from_manifest

class TestRenderPolicy(unittest.TestCase):

    def setUp(self):
        self.manifest = {
            "manifest_id": "test-manifest",
            "chapter_id": "test-chapter",
            "scenes": [
                {
                    "scene_id": "test-scene",
                    "manim_scene_name": "TestScene",
                    "text_content": "This is a test.",
                    "animation_suggestions": {}
                }
            ],
            "style": {"preset": "test-style"},
            "narration": {
                "text_per_scene": {
                    "test-scene": "This is a test narration."
                }
            },
            "render_settings": {"quality": "low"}
        }

    @patch('google.generativeai.GenerativeModel')
    def test_manim_code_generator(self, MockGenerativeModel):
        mock_model = MockGenerativeModel.return_value
        mock_model.generate_content.return_value = MagicMock(text="from manim import *\n\nclass TestScene(Scene):\n    def construct(self):\n        pass")

        generator = ManimCodeGenerator(gemini_api_key="test_key")
        scene_data = self.manifest['scenes'][0]
        style_preset = self.manifest['style']
        narration_text = self.manifest['narration']['text_per_scene']['test-scene']

        code = generator.generate_code(scene_data, style_preset, narration_text)

        self.assertIn("class TestScene(Scene):", code)
        mock_model.generate_content.assert_called_once()

    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open)
    def test_video_renderer_render_scene(self, mock_file, mock_subprocess_run):
        renderer = VideoRenderer()
        script_content = "from manim import *\n\nclass TestScene(Scene):\n    def construct(self):\n        pass"
        scene_name = "TestScene"
        render_settings = {"quality": "low"}

        # Mock the return value for the subprocess call
        mock_subprocess_run.return_value = MagicMock(check_returncode=lambda: None, stdout="File ready at path/to/video.mp4", stderr="")

        video_path = renderer.render_scene(script_content, scene_name, render_settings)

        self.assertEqual(video_path, "path/to/video.mp4")
        mock_file.assert_called_with(os.path.join(renderer.generated_scripts_dir, f"{scene_name}.py"), "w")
        mock_subprocess_run.assert_called_once()

    @patch('subprocess.run')
    @patch('builtins.open', new_callable=mock_open)
    def test_video_renderer_combine_videos(self, mock_file, mock_subprocess_run):
        renderer = VideoRenderer()
        video_paths = ["path/to/video1.mp4", "path/to/video2.mp4"]
        output_filename = "final_video.mp4"

        # Mock the return value for the subprocess call
        mock_subprocess_run.return_value = MagicMock(check_returncode=lambda: None, stdout="", stderr="")

        final_video_path = renderer.combine_videos(video_paths, output_filename)

        self.assertIsNotNone(final_video_path)
        mock_file.assert_called_with(os.path.join(renderer.generated_scripts_dir, "input_files.txt"), "w")
        mock_subprocess_run.assert_called_once()

    @patch('gm.render_policy.ManimCodeGenerator')
    @patch('gm.render_policy.VideoRenderer')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        "manifest_id": "test-manifest",
        "chapter_id": "test-chapter",
        "scenes": [
            {
                "scene_id": "test-scene",
                "manim_scene_name": "TestScene",
                "text_content": "This is a test.",
                "animation_suggestions": {}
            }
        ],
        "style": {"preset": "test-style"},
        "narration": {
            "text_per_scene": {
                "test-scene": "This is a test narration."
            }
        },
        "render_settings": {"quality": "low"}
    }))
    def test_render_video_from_manifest(self, mock_file, MockVideoRenderer, MockManimCodeGenerator):
        mock_code_generator = MockManimCodeGenerator.return_value
        mock_code_generator.generate_code.return_value = "from manim import *\n\nclass TestScene(Scene):\n    def construct(self):\n        pass"

        mock_renderer = MockVideoRenderer.return_value
        mock_renderer.render_scene.return_value = "path/to/scene_video.mp4"
        mock_renderer.combine_videos.return_value = "path/to/final_video.mp4"

        render_video_from_manifest("dummy_manifest.json", "low", "test_api_key")

        mock_code_generator.generate_code.assert_called_once()
        mock_renderer.render_scene.assert_called_once()
        mock_renderer.combine_videos.assert_called_once()

if __name__ == '__main__':
    unittest.main()

