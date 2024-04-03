from dataclasses import dataclass

from luna.utils import get_repr


@dataclass
class UserInfo:
    jid: str
    push_name: str
    bussines_name: str
    platform: str
    initialized: bool

    def __repr__(self) -> str:
        return get_repr(self)
