from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Optional

from luna.utils import get_repr

if TYPE_CHECKING:
    from neonize.events import MessageEv
    from neonize.proto.Neonize_pb2 import SendResponse

    from luna.core import Runner

    from .groups import GroupMetadata

    DownloadType = Callable[[], Optional[bytes]]
    ReplyType = Callable[[str], Optional[SendResponse]]


@dataclass
class QuotedMessage:
    id: str
    sender: str
    msg_type: str
    text: str
    is_owner: bool
    is_bot: bool
    download: DownloadType
    reply: ReplyType
    mimetype: str

    def __repr__(self) -> str:
        return get_repr(self)


@dataclass
class Message:
    id: str
    text: str
    sender: str
    chat: str
    is_group: bool
    is_from_me: bool
    msg_type: str
    is_owner: bool
    is_bot: bool
    runner: Runner
    push_name: str
    _message: "MessageEv"
    download: DownloadType
    mimetype: str
    group_metadata: Callable[[], Optional[GroupMetadata]]
    reply: ReplyType
    quoted: Optional[QuotedMessage] = field(default=None, init=True)
    mentioned_jid: List[str] = field(default_factory=list, init=True)
    args: List[str] = field(default_factory=list, init=True)
    body: str = field(default="", init=True)
    command: str = field(default="", init=True)
    used_prefix: str = field(default="", init=True)

    def __repr__(self) -> str:
        return get_repr(self)
