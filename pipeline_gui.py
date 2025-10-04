import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import os
import json
import re

class ManimPipelineGUI:
    def __init__(self, master):
        self.master = master
        master.title("Manim Study Guide Automator Pipeline")

        self.create_widgets()

    def create_widgets(self):
        # Input Frame
        input_frame = ttk.LabelFrame(self.master, text="Pipeline Inputs", padding="10")
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # Chapter File
        ttk.Label(input_frame, text="Chapter Markdown File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.chapter_path_entry = ttk.Entry(input_frame, width=50)
        self.chapter_path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(input_frame, text="Browse", command=self.browse_chapter_file).grid(row=0, column=2, padx=5, pady=5)

        # Section
        ttk.Label(input_frame, text="Section (e.g., '1b'):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.section_entry = ttk.Entry(input_frame, width=50)
        self.section_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Gemini API Key
        ttk.Label(input_frame, text="Gemini API Key:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.api_key_entry = ttk.Entry(input_frame, width=50, show='*') # show='*' for password field
        self.api_key_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        # Pre-fill from environment variable if available
        self.api_key_entry.insert(0, os.environ.get("GEMINI_API_KEY", ""))

        # Quality
        ttk.Label(input_frame, text="Render Quality:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.quality_var = tk.StringVar(value="low") # Default to low
        ttk.Radiobutton(input_frame, text="Low", variable=self.quality_var, value="low").grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(input_frame, text="High", variable=self.quality_var, value="high").grid(row=3, column=1, padx=5, pady=5, sticky="e")

        # Run Button
        self.run_button = ttk.Button(self.master, text="Run Pipeline", command=self.run_pipeline)
        self.run_button.grid(row=1, column=0, padx=10, pady=10)

        # Output Console
        self.output_console = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=80, height=20)
        self.output_console.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        # Configure grid weights for resizing
        self.master.grid_rowconfigure(2, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)

    def browse_chapter_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Chapter Markdown File",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.* אמיתי")]
        )
        if file_path:
            self.chapter_path_entry.delete(0, tk.END)
            self.chapter_path_entry.insert(0, file_path)

    def log_output(self, message):
        self.output_console.insert(tk.END, message + "\n")
        self.output_console.see(tk.END) # Auto-scroll to the end

    def run_pipeline(self):
        chapter_path = self.chapter_path_entry.get()
        section = self.section_entry.get()
        api_key = self.api_key_entry.get()
        quality = self.quality_var.get()

        if not chapter_path or not section or not api_key:
            self.log_output("Error: All fields must be filled.")
            return

        self.log_output("Starting pipeline...")
        self.run_button.config(state=tk.DISABLED) # Disable button during execution

        try:
            # Step 1: Generate Manifest
            self.log_output("\n--- Generating Manifest ---")
            manifest_command = [
                "uv", "run", "python", "gm/manifest_generator.py",
                "--chapter", chapter_path,
                "--section", section
            ]
            self.log_output(f"Executing: {' '.join(manifest_command)}")
            manifest_process = subprocess.run(
                manifest_command,
                capture_output=True,
                text=True,
                check=True,
                cwd=os.getcwd() # Ensure command runs from project root
            )
            self.log_output(manifest_process.stdout)
            if manifest_process.stderr:
                self.log_output(f"Manifest Generator STDERR:\n{manifest_process.stderr}")

            # Extract manifest path from stdout (assuming it's printed)
            # This part needs to be robust based on actual manifest_generator.py output
            # For now, let's assume it prints the path or we can derive it
            # Based on previous info, it's <chapter_name>_<section>.json in manifests/
            chapter_name = os.path.splitext(os.path.basename(chapter_path))[0]
            generated_manifest_filename = f"{chapter_name}_{section}.json"
            generated_manifest_path = os.path.join("manifests", generated_manifest_filename)
            self.log_output(f"Assumed generated manifest path: {generated_manifest_path}")

            if not os.path.exists(generated_manifest_path):
                self.log_output(f"Error: Generated manifest not found at {generated_manifest_path}. Check manifest generator output.")
                raise FileNotFoundError("Generated manifest not found.")

            # Step 2: Render Video
            self.log_output("\n--- Rendering Video ---")
            render_command = [
                "uv", "run", "python", "-m", "gm.render_policy",
                "--manifest", generated_manifest_path,
                "--quality", quality,
                "--gemini-api-key", api_key
            ]
            self.log_output(f"Executing: {' '.join(render_command)}")
            render_process = subprocess.run(
                render_command,
                capture_output=True,
                text=True,
                check=True,
                cwd=os.getcwd() # Ensure command runs from project root
            )
            self.log_output(render_process.stdout)
            if render_process.stderr:
                self.log_output(f"Render Policy STDERR:\n{render_process.stderr}")

            self.log_output("\nPipeline completed successfully!")

        except subprocess.CalledProcessError as e:
            self.log_output(f"Pipeline failed: Command '{e.cmd}' returned non-zero exit status {e.returncode}.")
            self.log_output(f"STDOUT:\n{e.stdout}")
            self.log_output(f"STDERR:\n{e.stderr}")
        except FileNotFoundError as e:
            self.log_output(f"Pipeline failed: {e}")
        except Exception as e:
            self.log_output(f"An unexpected error occurred: {e}")
        finally:
            self.run_button.config(state=tk.NORMAL) # Re-enable button

if __name__ == "__main__":
    root = tk.Tk()
    app = ManimPipelineGUI(root)
    root.mainloop()
