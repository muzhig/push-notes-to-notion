import os
import sys
from pathlib import Path


def read_dotenv():
    env_fname = Path(__file__).parent / ".env"
    env = {}
    if os.path.isfile(env_fname):
        for line in open(env_fname).read().split("\n"):
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split("=", 1)
                k = k.strip()
                v = v.strip()
                if k:
                    env[k] = v
    return env


def load_env():
    env = read_dotenv()
    os.environ.update(env)


def add_root_to_path():
    root = str(Path(__file__).parent)
    if root not in sys.path:
        sys.path.append(root)


load_env()
add_root_to_path()
