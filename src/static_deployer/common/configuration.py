from typing import Any, Dict
from . import log
import logging
import toml
import attr
from io import IOBase


@attr.s(auto_attribs=True, init=False)
class ConfigOptions(object):
    @attr.s(auto_attribs=True)
    class ContentConfig:
        root_dir: str
        patterns: str

    @attr.s(auto_attribs=True)
    class StorageConfig:
        name: str
        prefix: str

    @attr.s(auto_attribs=True)
    class CdnConfig:
        distribution_id: str
        origin_name: str

    content: ContentConfig
    storage: StorageConfig
    cdn: CdnConfig
    version: str
    dry_run: bool

    def to_dict(self) -> Dict[str, Any]:
        return attr.asdict(self)

    def load_from_dict(self, data: dict) -> None:
        self.content = ConfigOptions.ContentConfig(
            root_dir=data["content"].get("root_dir"),
            patterns=data["content"].get("patterns"),
        ) if data.get("content") else None
        self.storage = ConfigOptions.StorageConfig(
            name=data["storage"].get("name"),
            prefix=data["storage"].get("prefix"),
        ) if data.get("storage") else None
        self.cdn = ConfigOptions.CdnConfig(
            distribution_id=data["cdn"].get("distribution_id"),
            origin_name=data["cdn"].get("origin_name"),
        ) if data.get("cdn") else None
        self.version = data.get("version")
        self.dry_run = data.get("dry_run")
        log.debug(f'config={str(self)}')

    def load_from_toml(self, data: str) -> bool:
        try:
            parsed = toml.loads(data)
            self.load_from_dict(parsed)
            return True
        except (TypeError, toml.TomlDecodeError):
            logging.error(f'failed to decode config data')
            return False

    def load_from_file(self, file: str) -> bool:
        try:
            with open(file, 'r') as f:
                success = self.load_from_toml(f.read())
                return success
        except OSError:
            logging.error(f'failed to open config file {file}')
            return None

    def load_from_io(self, file: IOBase) -> bool:
        try:
            success = self.load_from_toml(file.read())
            return success
        except OSError:
            logging.error(f'failed to open config file {file}')
            return None


@attr.frozen
class ConfigOptionsAdapter(object):
    config: ConfigOptions

    def to_args(self) -> Dict[str, Any]:
        return {
            'root_dir': self.config.content.root_dir,
            'patterns': self.config.content.patterns,
            'bucket_name': self.config.storage.name,
            'bucket_prefix': self.config.storage.prefix,
            'distribution_id': self.config.cdn.distribution_id,
            'origin_name': self.config.cdn.origin_name,
            'version': self.config.version,
            'dry_run': self.config.dry_run,
        }

    def merge_args(self, data: dict) -> None:
        value = data.get('root_dir')
        if value:
            self.config.content.root_dir = value
        value = data['patterns']
        if value:
            self.config.content.patterns = value
        value = data.get('bucket_name')
        if value:
            self.config.storage.name = value
        value = data.get('bucket_prefix')
        if value:
            self.config.storage.prefix = value
        value = data.get('distribution_id')
        if value:
            self.config.cdn.distribution_id = value
        value = data.get('origin_name')
        if value:
            self.config.cdn.origin_name = value
        value = data.get('version')
        if value:
            self.config.version = value
        value = data['dry_run']
        if value:
            self.config.dry_run = value if type(value) == bool else self._str_to_bool(value)
        log.debug(f'config={str(self.config)}')

    @staticmethod
    def _str_to_bool(data: str) -> bool:
        return data.lower() in ['true', '1', 't', 'y', 'yes']