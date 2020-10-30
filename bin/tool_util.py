import os
import sys

project_path, _, _ = os.path.dirname(__file__).rpartition("/")
sys.path.append(project_path)
src_path = f"{project_path}/src"
sys.path.append(src_path)


def error_and_exit(error_message: str, suggestion: str = None):
    print(f"ERROR: {error_message}")
    print(f"\tSUGGESTION:{suggestion}")
    exit(-1)
