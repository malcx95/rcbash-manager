from pathlib import Path

RESULT_FOLDER_PATH = Path.home() / "RCBashResults"
# this is necessary in production
if Path("/home/malcolm/RCBashResults").exists():
    RESULT_FOLDER_PATH = Path("/home/malcolm/RCBashResults")

MAX_POINTS_IN_NON_FINALS = 40
MAX_POINTS_IN_FINALS = 80
