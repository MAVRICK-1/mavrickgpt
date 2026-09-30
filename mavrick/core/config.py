import os

config_path_dir: str = os.environ.get(
    "MAVRICK_CONFIGPATH_DIR", os.path.expanduser("~/.mavrick")
)
