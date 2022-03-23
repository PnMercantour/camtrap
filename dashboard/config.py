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

with (project_root/"config"/"species.json").open() as f:
    species_options = json.load(f)

with (project_root/"config"/"domestic.json").open() as f:
    domestic_options = json.load(f)
