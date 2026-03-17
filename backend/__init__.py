from pathlib import Path

from backend.utils import get_current_dir

APP_ROOT = get_current_dir()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
