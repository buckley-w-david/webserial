from pydantic import BaseModel
import toml


class TomlModel(BaseModel):
    @classmethod
    def load(cls, file):
        with open(file, "r") as f:
            return cls.parse_obj(toml.load(f))

    def dump(self, file):
        with open(file, "w") as f:
            toml.dump(self.dict(), f)


class WebserialConfig(TomlModel):
    calibre_library: str = ""
    calibre_username: str = ""
    calibre_password: str = ""
