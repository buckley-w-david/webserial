import glob
import os
import re
import subprocess

from pydantic import BaseModel, FilePath, DirectoryPath, HttpUrl
from pydantic.tools import parse_obj_as

from webserial.errors import (
    EqualChapterError,
    LocalAheadOfRemoteError,
    NoChaptersFoundError,
    WebserialError,
)

# Shamelessly stolen from https://github.com/MrTyton/AutomatedFanfic/blob/d062eb1dd8ede38208f97b95e5f73503415f61f4/fanficdownload.py
url_parsers = [
    (
        re.compile("(https?://).*(fanfiction.net/s/\d*)/?.*"),
        "www.",
    ),  # ffnet - TODO confirm prefix
    (re.compile("(https?://).*(archiveofourown.org/works/\d*)/?.*"), ""),  # ao3
    (
        re.compile("(https?://).*(fictionpress.com/s/\d*)/?.*"),
        "",
    ),  # fictionpress - TODO confirm prefix
    (re.compile("(https?://).*(royalroad.com/fiction/\d*)/?.*"), "www."),  # royalroad
    (re.compile("(https?://)(.*)"), ""),  # other sites
]
equal_chapters = re.compile(r".* already contains \d* chapters.")
chapter_difference = re.compile(r".* contains \d* chapters, more than source: \d*.")
bad_chapters = re.compile(
    r".* doesn't contain any recognizable chapters, probably from a different source.  Not updating."
)
more_chapters = re.compile(
    r".*File\(.*\.epub\) Updated\(.*\) more recently than Story\(.*\) - Skipping"
)


def normalize_url(url: HttpUrl) -> HttpUrl:
    for regex, prefix in url_parsers:
        match = regex.search(str(url))
        if match:
            return parse_obj_as(HttpUrl, f"{match.group(1)}{prefix}{match.group(2)}")


def most_recent_file(directory: DirectoryPath, extension="epub") -> FilePath:
    list_of_files = glob.glob(f"{directory}/*.{extension}")
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file
