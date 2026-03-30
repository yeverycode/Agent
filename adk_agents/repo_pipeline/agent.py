from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.adk_pipeline import build_pipeline_agent  # noqa: E402

root_agent = build_pipeline_agent()
