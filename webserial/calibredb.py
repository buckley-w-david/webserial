import json
import re
import subprocess
from typing import List, Dict, Tuple, Union, Optional

from pydantic import FilePath, DirectoryPath

from webserial.errors import WebserialError

added = re.compile(r"Added book ids: (\d+)")


class CalibreDb:
    def __init__(self, username: str, password: str, library: str):
        self.username = username
        self.password = password
        self.library = library

    def run(self, command):
        full_command = [
            "calibredb",
            *command,
            "--with-library",
            self.library,
            "--username",
            self.username,
            "--password",
            self.password,
        ]

        return subprocess.run(full_command, capture_output=True)

    def search(self, query: str) -> List[int]:
        completed_process = self.run(["search", query])
        result = completed_process.stdout.decode("utf-8")
        if result:
            return [int(id) for id in result.split(",")]
        else:
            return []

    def list(self, query: str, fields: Optional[List[str]]) -> Dict:
        command = ["list", "--for-machine", "--search", query]
        if fields:
            command.extend(["--fields", ",".join(fields)])

        completed_process = self.run(command)
        result = completed_process.stdout.decode("utf-8")
        if result:
            return json.loads(result)
        else:
            return {}

    def get_metadata(self, calibre_id: int) -> Dict[str, str]:
        completed_process = self.run(["show_metadata", str(calibre_id)])
        result = completed_process.stdout.decode("utf-8")
        if result:
            ret = {}
            for line in result.split("\n"):
                try:
                    key, value = line.split(":", 1)
                    ret[key.strip()] = value.strip()
                except Exception:
                    pass
            return ret
        else:
            return {}

    # Dangerous mutable default arugment
    def set_metadata(
        self,
        calibre_id: int,
        metadata: List[Tuple[str, str]] = [],
        metadata_file: FilePath = None,
    ) -> None:
        command = ["set_metadata", str(calibre_id)]
        for name, value in metadata:
            command.append(f"--field")
            command.append(f"{name}:{value}")
        if metadata_file:
            command.append(str(metadata_file))

        completed_process = self.run(command)
        return completed_process.stdout.decode("utf-8")

    def export(
        self,
        id: int,
        output_directory: DirectoryPath,
        dont_save_cover=True,
        dont_write_opf=False,
    ) -> str:
        command = ["export", str(id), "--single-dir"]
        if dont_save_cover:
            command.append("--dont-save-cover")
        if dont_write_opf:
            command.append("--dont-write-opf")
        command.extend(["--to-dir", str(output_directory)])

        completed_process = self.run(command)
        return completed_process.stdout

    def remove(self, id: int) -> str:
        completed_process = self.run(["remove", str(id)])
        return completed_process.stdout.decode("utf-8")

    def add(self, ebook: FilePath, duplicate: bool = True) -> int:
        # FIXME use duplicate flag
        completed_process = self.run(["add", "-d", str(ebook)])
        result = completed_process.stdout.decode("utf-8")
        err = completed_process.stderr.decode("utf-8")
        match = added.search(result)
        if match:
            return int(match.group(1))
        else:
            raise WebserialError(result if not err else err)
