import os
from pathlib import Path

def load_env_file() -> None:
    """Loads variables from .env file into os.environ."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        load_dotenv(Path(__file__).parent / ".env")
        return
    except ImportError:
        pass

    search_paths = [
        Path(__file__).parent / ".env",
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]

    for env_path in search_paths:
        if not env_path.is_file():
            continue

        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
        break
