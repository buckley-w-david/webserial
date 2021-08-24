import logging
import os
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Optional, List

import typer

from webserial.errors import WebserialError
from webserial.config import WebserialConfig
from webserial.calibredb import CalibreDb
from webserial.fff import FanFicFare
from webserial.utils import most_recent_file, normalize_url

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

    with TemporaryDirectory() as tempdir:
        for url in urls:
            normalized_url = normalize_url(url)

            search_query = f"Identifiers:url:{normalized_url}"
            matching_ids = calibredb.search(search_query)
            if not matching_ids:
                logger.warning("Did not find calibre record for %s", search_query)

                try:
                    with NamedTemporaryFile(suffix=".epub", dir=str(tempdir)) as f:
                        fanficfare.download_serial(f.name, normalized_url, update=False)
                        new_id = calibredb.add(f.name)
                        logger.info(f"Added %s as %s", url, new_id)
                except WebserialError as e:
                    logger.warning("%s skipping", e)
                except Exception as e:
                    logger.error("🔥🔥🔥 %s 🔥🔥🔥", e)
            elif len(matching_ids) > 1:
                logger.warning("%s returned more than 1 result. skipping", search_query)
            else:
                calibre_id = matching_ids[0]
                logger.info("Found %s as %s", url, calibre_id)

                # It'd be nice if export gave the exported file name
                calibredb.export(calibre_id, tempdir)
                exported_serial = most_recent_file(tempdir)

                try:
                    fanficfare.download_serial(
                        exported_serial, normalized_url, update=True
                    )
                    calibredb.remove(calibre_id)
                    new_id = calibredb.add(exported_serial)
                    logger.info(f"Added %s as %s", url, new_id)
                except WebserialError as e:
                    logger.warning("%s skipping", e)
                except Exception as e:
                    logger.error("🔥🔥🔥 %s 🔥🔥🔥", e)