from typing import TYPE_CHECKING, List, Optional

from neonize.proto import def_pb2 as wa_proto

from luna.wa_classes import (
    GroupDesc,
    GroupMetadata,
    GroupParticipant,
    GroupSubject,
    Message,
    QuotedMessage,
)
from luna.utils import jid_to_str, str_to_jid

if TYPE_CHECKING:
    from neonize.events import MessageEv
    from neonize.proto.def_pb2 import ContextInfo
    from neonize.proto.Neonize_pb2 import (
        GroupInfo,
        GroupName,
        GroupTopic,
        SendResponse,
    )
    from neonize.proto.Neonize_pb2 import (
        GroupParticipant as GroupParticipantsProto,
    )

    from luna.core import Runner


def _get_text(msg: wa_proto.Message) -> str:
    msg_fields = msg.ListFields()
    if msg_fields:
        _, field_value = msg_fields[0]
        if isinstance(field_value, str):
            return field_value
        text_attrs = ["text", "caption", "name"]
        for attr in text_attrs:
            if hasattr(field_value, attr):
                return getattr(field_value, attr)
    return ""


class QuotedSerialize:
    def __init__(
        self, runner: "Runner", raw_message: "ContextInfo", message: "Message"
    ) -> None:
        self._message = message
        self._runner = runner
        self._raw_message = raw_message

    def serialize(self) -> "QuotedMessage":
        return QuotedMessage(
            id=self._id,
            sender=self._sender,
            msg_type=self._msg_type,
            text=self._text,
            download=self._download,
            is_owner=self._is_owner,
            is_bot=self._is_bot,
            reply=self._reply,
            mimetype=self._mime_type,
        )

    @property
    def _mime_type(self) -> str:
        msg = self._raw_message.quotedMessage
        msg_fields = msg.ListFields()
        if msg_fields:
            _, field_value = msg_fields[0]
            if hasattr(field_value, "mimetype"):
                return field_value.mimetype
        return ""

    @property
    def _id(self) -> str:
        return self._raw_message.stanzaId

    @property
    def _text(self) -> str:
        msg = self._raw_message.quotedMessage
        return _get_text(msg)

    @property
    def _is_bot(self) -> bool:
        return self._id.startswith("3EB0")

    @property
    def _msg_type(self) -> str:
        return self._runner.get_message_type(self._raw_message.quotedMessage)

    @property
    def _sender(self) -> str:
        return self._raw_message.participant

    @property
    def _is_from_me(self) -> bool:
        return self._raw_message.participant == self._runner.user_info.jid

    @property
    def _is_owner(self) -> bool:
        return self._sender in self._runner.owners

    def _download(self):
        return self._runner.download_any(self._raw_message.quotedMessage)

    def _reply(self, text: str) -> Optional["SendResponse"]:
        return self._runner.reply_message(
            text,
            self._raw_message.quotedMessage,  # type: ignore
        )


class GroupSerialize:
    @staticmethod
    def serialize(
        __group_info: "GroupInfo", bot_jid: str = "", sender_jid: str = ""
    ) -> GroupMetadata:
        group_jid = jid_to_str(__group_info.JID)
        group_owner_jid = jid_to_str(__group_info.OwnerJID)
        group_participants = GroupSerialize._serialize_participants(
            list(__group_info.Participants)
        )  # Convert to list
        group_desc = GroupSerialize._serialize_desc(__group_info.GroupTopic)
        group_subject = GroupSerialize._serialize_subject(__group_info.GroupName)

        return GroupMetadata(
            is_sender_admin=GroupSerialize._get_participant_is_admin(
                group_participants, sender_jid
            ),
            is_bot_admin=GroupSerialize._get_participant_is_admin(
                group_participants, bot_jid
            ),
            owner_jid=group_owner_jid,
            jid=group_jid,
            desc=group_desc,
            subject=group_subject,
            participants=group_participants,
            is_locked=__group_info.GroupLocked.isLocked,
            is_announce=__group_info.GroupAnnounce.IsAnnounce,
            is_ephemeral=__group_info.GroupEphemeral.IsEphemeral,
            is_incognito=__group_info.GroupIncognito.IsIncognito,
            is_parent=__group_info.GroupParent.IsParent,
            group_linked_parent_jid=jid_to_str(
                __group_info.GroupLinkedParent.LinkedParentJID
            ),
            is_default_sub_group=__group_info.GroupIsDefaultSub.IsDefaultSubGroup,
            created_at=__group_info.GroupCreated,
        )

    @staticmethod
    def _serialize_participants(
        participants: List["GroupParticipantsProto"],
    ) -> List[GroupParticipant]:
        return [
            GroupParticipant(
                jid=jid_to_str(p.JID),
                lid=jid_to_str(p.LID),
                is_admin=(
                    "super_admin" if p.IsSuperAdmin else "admin" if p.IsAdmin else None
                ),
                display_name=p.DisplayName,
            )
            for p in participants
        ]

    @staticmethod
    def _serialize_desc(group_topic: "GroupTopic") -> GroupDesc:
        return GroupDesc(
            topic=group_topic.Topic,
            topic_id=group_topic.TopicID,
            set_at=group_topic.TopicSetAt,
            set_by=jid_to_str(group_topic.TopicSetBy),
            topic_deleted=group_topic.TopicDeleted,
        )

    @staticmethod
    def _serialize_subject(group_name: "GroupName") -> GroupSubject:
        return GroupSubject(
            name=group_name.Name,
            set_by=jid_to_str(group_name.NameSetBy),
            set_at=group_name.NameSetAt,
        )

    @staticmethod
    def _get_participant_is_admin(
        participants: List[GroupParticipant], jid: Optional[str]
    ) -> Optional[str]:
        if not jid:
            return None
        for participant in participants:
            if participant.jid == jid:
                return participant.is_admin
        return None


class MessageSerialize:
    def __init__(self, runner: "Runner", message: "MessageEv"):
        self._runner = runner
        self._message = message
        self._msg_source = message.Info.MessageSource

    def serialize(self) -> Message:
        return self.__initialize_message()

    def _download(self) -> Optional[bytes]:
        return self._runner.download_any(self._message.Message)

    def _reply(self, text: str) -> "SendResponse":
        return self._runner.reply_message(text, self._message)

    def group_metadata(self) -> Optional[GroupMetadata]:
        if self._is_group:
            group_info = self._runner.group_metadata(self._chat)
            return GroupSerialize.serialize(
                group_info, bot_jid=self._runner.user_info.jid, sender_jid=self._sender
            )
        return None

    @property
    def _mimetype(self) -> str:
        msg = self._message.Message
        msg_fields = msg.ListFields()
        if msg_fields:
            _, field_value = msg_fields[0]
            if hasattr(field_value, "mimetype"):
                return field_value.mimetype
        return ""

    def _mentioned_jids(self) -> List[str]:
        try:
            mentioned_jids = (
                self._message.ListFields()[1][1]
                .ListFields()[0][1]
                .contextInfo.mentionedJid
            )
        except (IndexError, AttributeError):
            return []
        return mentioned_jids

    @property
    def _push_name(self) -> str:
        _sender_contact = self._runner.contact.get_contact(str_to_jid(self._sender))
        if _sender_contact.Found:
            return _sender_contact.PushName
        return ""

    @property
    def _is_bot(self) -> bool:
        return self._id.startswith("3EB0")

    @property
    def _msg_type(self) -> str:
        return self._runner.get_message_type(self._message.Message)

    @property
    def _quoted(self) -> Optional["QuotedMessage"]:
        msg = self.__initialize_message(quoted=False)
        if msg_fields := self._message.Message.ListFields():
            _, field_value = msg_fields[0]
            if isinstance(field_value, str):
                return None  # msg doesn't have a quoted message if it's a string (conversation message)
            if hasattr(field_value, "contextInfo"):
                context_info: ContextInfo = getattr(field_value, "contextInfo")
                return QuotedSerialize(self._runner, context_info, msg).serialize()
        return None

    def __initialize_message(self, quoted=True) -> "Message":
        message = Message(
            id=self._id,
            text=self._text,
            sender=self._sender,
            chat=self._chat,
            is_group=self._is_group,
            is_from_me=self._is_from_me,
            msg_type=self._msg_type,
            download=self._download,
            group_metadata=self.group_metadata,
            is_owner=self._is_owner,
            is_bot=self._is_bot,
            reply=self._reply,
            runner=self._runner,
            push_name=self._push_name,
            _message=self._message,
            mentioned_jid=self._mentioned_jids(),
            mimetype=self._mimetype,
        )
        if quoted:
            message.quoted = (
                self._quoted if self._quoted and self._quoted.msg_type else None
            )
        return message

    @property
    def _is_owner(self) -> bool:
        return self._sender in self._runner.owners

    @property
    def _is_from_me(self) -> bool:
        return self._msg_source.IsFromMe

    @property
    def _sender(self) -> str:
        if self._is_group:
            return jid_to_str(self._msg_source.Sender)
        return jid_to_str(self._msg_source.Chat)

    @property
    def _chat(self) -> str:
        return jid_to_str(self._msg_source.Chat)

    @property
    def _is_group(self) -> bool:
        return self._msg_source.IsGroup

    @property
    def _text(self) -> str:
        msg = self._message.Message
        return _get_text(msg)

    @property
    def _id(self) -> str:
        return self._message.Info.ID
