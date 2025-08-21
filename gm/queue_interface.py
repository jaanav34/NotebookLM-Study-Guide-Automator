import os
import argparse

QUEUE_FILE = "queue.txt"

def _read_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def _write_queue(queue_list):
    with open(QUEUE_FILE, 'w') as f:
        for item in queue_list:
            f.write(f"{item}\n")

def add_to_queue(manifest_path):
    """
    Adds a manifest path to the queue.
    """
    queue_list = _read_queue()
    if manifest_path not in queue_list:
        queue_list.append(manifest_path)
        _write_queue(queue_list)
        return True
    return False # Already in queue

def get_next_job():
    """
    Retrieves the next manifest path from the queue (FIFO).
    Returns None if the queue is empty.
    """
    queue_list = _read_queue()
    if queue_list:
        return queue_list[0]
    return None

def mark_job_complete(manifest_path):
    """
    Removes a manifest path from the queue.
    """
    queue_list = _read_queue()
    if manifest_path in queue_list:
        queue_list.remove(manifest_path)
        _write_queue(queue_list)
        return True
    return False # Not found in queue

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage the render queue.")
    parser.add_argument("command", choices=["add", "get", "complete"], help="Command to execute.")
    parser.add_argument("--manifest", help="Path to the manifest file (required for add and complete commands).")

    args = parser.parse_args()

    if args.command == "add":
        if not args.manifest:
            print("Error: --manifest is required for 'add' command.")
            exit(1)
        if add_to_queue(args.manifest):
            print(f"Manifest '{args.manifest}' added to queue.")
        else:
            print(f"Manifest '{args.manifest}' already in queue.")
    elif args.command == "get":
        next_job = get_next_job()
        if next_job:
            print(f"Next job: {next_job}")
        else:
            print("Queue is empty.")
    elif args.command == "complete":
        if not args.manifest:
            print("Error: --manifest is required for 'complete' command.")
            exit(1)
        if mark_job_complete(args.manifest):
            print(f"Manifest '{args.manifest}' marked as complete and removed from queue.")
        else:
            print(f"Manifest '{args.manifest}' not found in queue.")
