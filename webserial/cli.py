import json
import logging
from pathlib import Path
from typing import List

import typer

from webserial.config import WebserialConfig
from webserial.calibredb import CalibreDb
from webserial.fff import FanFicFare
from webserial.update import perform

logging.getLogger("fanficfare").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

# TODO configurable log level
logging.basicConfig(level=logging.INFO)

app = typer.Typer()


@app.command()
def touch(config_file: Path = Path("webserial.toml")):
    if not config_file.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config = WebserialConfig()  # Creates a config structure with default values
        config.dump(config_file)


@app.command()
def update(urls: List[str], config_file: Path = Path("webserial.toml")):
    touch(config_file)
    config = WebserialConfig.load(config_file)

    calibredb = CalibreDb(
        config.calibre_username, config.calibre_password, config.calibre_library
    )
    fanficfare = FanFicFare()

    ids = perform(calibredb, fanficfare, urls)
    print(json.dumps(ids))
