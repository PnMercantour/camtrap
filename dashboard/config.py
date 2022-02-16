from dotenv import load_dotenv
from os import getenv
from pathlib import Path
import json

project_root = Path(__file__).parent.parent.resolve()
load_dotenv(project_root / '.env')
load_dotenv(project_root / 'config/default_config')

data_root = project_root / getenv('CAMTRAP_DATA')
"Location of processed files"

video_root = project_root / getenv('CAMTRAP_VIDEO')
"Location of raw video files"

try:
    with (project_root / "config/users.json").open() as f:
        camtrap_users = json.load(f)
except:
    if (project_root / "config/users.json").exists():
        print(
            'ERROR: config/users.json could not be parsed, either remove or fix this file')
        exit(1)
    else:
        print('WARNING: config/users.json not found')
    camtrap_users = []
camtrap_users.append({"label": "Invité", "value": "guest"})
