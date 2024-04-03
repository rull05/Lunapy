import mimetypes
import os
from io import BytesIO
from typing import TYPE_CHECKING, Optional, Union

import magic
from cachetools import TTLCache, cached
from neonize.client import NewClient
from neonize.proto import Neonize_pb2 as neonize_proto
from neonize.proto import def_pb2 as wa_proto
from neonize.utils.iofile import get_bytes_from_name_or_url
from luna.command import CommandHandler

from luna.config import DIR_SESSION, OWNERS_NUMBER
from luna.events import EventHandler
from luna.utils import jid_to_str, str_to_jid, logger
from luna.wa_classes import Message, UserInfo


if TYPE_CHECKING:
    from neonize.types import MessageWithContextInfo as MessageWithContextInfoType

MessageWithContextInfo = (
    wa_proto.ImageMessage,
    wa_proto.ContactsArrayMessage,
    wa_proto.ExtendedTextMessage,
    wa_proto.DocumentMessage,
    wa_proto.AudioMessage,
    wa_proto.VideoMessage,
    wa_proto.LiveLocationMessage,
    wa_proto.StickerMessage,
    wa_proto.GroupInviteMessage,
    wa_proto.ProductMessage,
    wa_proto.ListMessage,
    wa_proto.ListResponseMessage,
    wa_proto.ButtonsMessage,
    wa_proto.PollCreationMessage,
    wa_proto.MessageHistoryBundle,
    wa_proto.EventMessage,
)


class Runner(NewClient):
    def __init__(self, name: str, **kwargs):
        """
        Initializes a Runner object.

        :param name: The name of the bot.
        :type name: str
        :param kwargs: Additional keyword arguments.

        """
        # Create a sessions directory if it doesn"t exist.
        os.makedirs(DIR_SESSION, exist_ok=True)
        super().__init__(f"{DIR_SESSION}/{name}.sqlite3")
        self.bot_name = name
        self.command_handler = CommandHandler(kwargs.get("dir_commands", "commands"))
        self.event = EventHandler(self)
        self.owners = OWNERS_NUMBER
        self.chats = {}
        self.tokovoucher = {}

    def initialize_owner(self):
        self.owners.append(self.user_info.jid)

    def run(self):
        self.connect()

    @cached(cache=TTLCache(maxsize=1024, ttl=300))
    def group_metadata(self, chat: str):
        group_jid = str_to_jid(chat)
        return self.get_group_info(group_jid)

    @property
    def user_info(self) -> UserInfo:
        if not self.is_connected:
            return UserInfo(
                jid="", push_name="", bussines_name="", platform="", initialized=False
            )
        me = self.get_me()
        return UserInfo(
            jid=jid_to_str(me.JID),
            push_name=me.PushName,
            bussines_name=me.BussinessName,
            platform=me.Platform,
            initialized=me.Initialized,
        )

    def _add_context_info(
        self, message: "MessageWithContextInfoType", quoted: Message
    ) -> "MessageWithContextInfoType":
        quoted_message = self._make_quoted_message(quoted._message)
        message.contextInfo.MergeFrom(quoted_message)
        return message

    def relay_message(
        self,
        to: Union[neonize_proto.JID, str],
        message: Union[wa_proto.Message, "MessageWithContextInfoType"],
        quoted: Optional[Message] = None,
    ):
        msg_type = self.get_message_type(message)

        if not isinstance(to, neonize_proto.JID):
            to = str_to_jid(to)

        if isinstance(message, wa_proto.Message):
            build_message = message
            partial_message: MessageWithContextInfoType = getattr(
                build_message, msg_type
            )
            if quoted:
                self._add_context_info(partial_message, quoted)
            getattr(build_message, msg_type).MergeFrom(partial_message)
        else:
            build_message = wa_proto.Message()
            if quoted:
                self._add_context_info(message, quoted)
            getattr(build_message, msg_type).MergeFrom(message)

        logger.debug(f"Relaying message to {to}")
        logger.debug(f"Message: {build_message}")
        return super().send_message(to, build_message)

    def get_message_type(
        self, message: Union[wa_proto.Message, "MessageWithContextInfoType", str]
    ) -> str:
        if isinstance(message, wa_proto.Message):
            fields = message.ListFields()
            if len(fields) < 1:
                return ""
            field_name: str = fields[0][1].__class__.__name__
            if field_name == "str":
                field_name = "Conversation"
            elif field_name == "MessageContextInfo":
                field_name = fields[1][1].__class__.__name__
        else:
            field_name = message.__class__.__name__

        return field_name[0].lower() + field_name[1:]

    def send_poll(
        self,
        to: str,
        options: list[str],
        name: str = "",
        selectable_count: int = 1,
        quoted: Optional[Message] = None,
    ):
        self.chats[to] = self.chats[to] if self.chats.get("to") else {}
        message = super().build_poll_vote_creation(name, options, selectable_count)
        self.chats[to]["messages"] = (
            self.chats[to]["messages"] if self.chats[to].get("messages") else {}
        )

        msg = self.relay_message(to, message, quoted)
        self.chats[to]["messages"][msg.ID] = message
        return msg

    def send_file(
        self,
        to: str,
        file: Union[str, bytes],
        caption: str = "",
        filename: str = "",
        title: str = "",
        quoted: Optional[Message] = None,
        as_document: bool = False,
        ptt: bool = False,
    ):
        if quoted:
            quoted_message = quoted._message
        jid = str_to_jid(to)
        io = BytesIO(get_bytes_from_name_or_url(file))
        io.seek(0)
        buff = io.read()
        mime = magic.from_buffer(buff)

        if as_document or "application" in mime:
            ext = mimetypes.guess_extension(mime[0])
            filename = f"{caption}{ext}"
            return self.send_document(
                jid, buff, caption, title, filename, quoted_message
            )
        match mime[0]:
            case "image":
                return self.send_image(jid, buff, caption, quoted_message)
            case "audio":
                return self.send_audio(jid, buff, ptt, quoted_message)
            case "video":
                return self.send_video(jid, buff, caption, quoted_message)
            case _:
                ext = mimetypes.guess_extension(mime[0])
                filename = f"{caption}{ext}"
                return self.send_document(
                    jid, buff, title, caption, filename, quoted_message
                )

    def get_name(self, jid: str) -> str:
        contact = self.contact.get_contact(str_to_jid(jid))
        if contact.Found:
            return contact.PushName
        return jid.split("@")[0]
