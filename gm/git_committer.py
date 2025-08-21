import argparse
import subprocess
import os
import json

def run_git_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e.cmd}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise

def commit_manifest(manifest_path):
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{manifest_path}'")
        raise

    chapter_id = manifest_data.get("chapter_id", "unknown_chapter")
    chapter_section = manifest_data.get("chapter_section", "unknown_section")

    branch_name = f"feature/manim-manifest-{chapter_id}"
    commit_message = f"feat(manim): add manifest for section {chapter_section}"

    # Create and switch to a new branch
    print(f"Creating and switching to branch: {branch_name}")
    run_git_command(f"git checkout -b {branch_name}")

    # Stage the manifest file
    print(f"Staging manifest file: {manifest_path}")
    run_git_command(f"git add {manifest_path}")

    # Commit the file
    print(f"Committing changes with message: \"{commit_message}\"")
    run_git_command(f"git commit -m \"{commit_message}\"")

    print(f"Successfully committed manifest for {chapter_id}/{chapter_section}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Git commits for Manim manifests.")
    parser.add_argument("manifest_path", help="Path to the manifest JSON file.")
    args = parser.parse_args()

    try:
        commit_manifest(args.manifest_path)
    except (FileNotFoundError, json.JSONDecodeError, subprocess.CalledProcessError) as e:
        print(f"Error during git commit operation: {e}")
        exit(1)
