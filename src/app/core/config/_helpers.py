import os
import pathlib


def __is_project_dir(path: str) -> bool:
    if not os.path.exists(path):
        return False

    # Find "src" dir
    for l1 in os.listdir(path):
        l1_path = os.path.join(path, l1)
        if not os.path.isdir(l1_path) or l1 != "app":
            continue

        for l2 in os.listdir(os.path.join(path, l1)):
            l2_path = os.path.join(l1_path, l2)
            if os.path.isfile(l2_path) and l2 == "__init__.py":
                with open(l2_path, "r") as f:
                    if f.readline().strip() == "# VERSEBASE BACKEND PROJECT ROOT":
                        return True
    return False


def get_workdir() -> str:
    current_workdir = str(pathlib.Path().resolve())
    if __is_project_dir(current_workdir):
        return current_workdir
    for path in os.environ.get("PYTHONPATH", "").split(":"):
        if __is_project_dir(path):
            return path

    raise RuntimeError("unable to detect a valid working directory")


def update_workdir() -> None:
    workdir = get_workdir()
    os.chdir(workdir)
