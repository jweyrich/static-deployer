from typing import Any, Dict
import attr
import logging


@attr.s(auto_attribs=True)
class FileMapping(object):
    local_path: str
    remote_path: str


@attr.s(auto_attribs=True)
class ContentDetails(object):
    root_dir: str
    patterns: str


@attr.s(auto_attribs=True)
class StorageDetails(object):
    name: str
    prefix: str

    def __attrs_post_init__(self):
        if self.prefix.startswith('/'):
            logging.warning('The specified storage prefix starts with a slash (\'/\').' +
                            ' Please, remove it! prefix=\'%s\'', self.prefix)
            # Strip off the leading '/'
            self.prefix = self.prefix[1:]


@attr.s(auto_attribs=True)
class CdnDetails(object):
    distribution_id: str
    origin_name: str


@attr.s(auto_attribs=True)
class DeploySpec(object):
    content: ContentDetails
    storage: StorageDetails
    cdn: CdnDetails
    version: str

    def to_dict(self) -> Dict[str, Any]:
        return attr.asdict(self)


@attr.s(auto_attribs=True)
class RollbackSpec(object):
    storage: StorageDetails
    cdn: CdnDetails
    version: str

    def to_dict(self) -> Dict[str, Any]:
        return attr.asdict(self)
