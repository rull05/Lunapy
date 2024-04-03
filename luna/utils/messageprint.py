from termcolor import colored
import difflib
from luna.wa_classes import Message
from neonize.proto import def_pb2 as wa_proto
import phonenumbers as pn


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


def color_diff(text_before: str, text_after: str) -> str:
    diff = difflib.ndiff(text_before.split(), text_after.split())

    result = []
    for d in diff:
        if d[0] == "-":
            # Words that are in text_before but not in text_after will be colored red
            result.append(colored(d, "red"))
        elif d[0] == "+":
            # Words that are in text_after but not in text_before will be colored green
            result.append(colored(d, "green"))
        else:
            result.append(d)

    return " ".join(result)


class MessagePrint:
    SQUARE_BRACKET = f"{colored('[', 'white')}%value{colored(']', 'white')}"

    def __init__(self, msg: Message) -> None:
        self.msg = msg

    def __call__(self) -> None:
        self.msg.runner.chats.setdefault(self.msg.chat, {})
        self.msg.runner.chats[self.msg.chat][self.msg.id] = self.msg
        msg = self.msg
        tag = colored("SENT", "cyan") if msg.is_bot else colored("RECV", "green")
        recv_type = (
            colored("CMD", "yellow") if msg.command else colored("MSG", "magenta")
        )
        tag = self.SQUARE_BRACKET.replace("%value", tag)
        recv_type = self.SQUARE_BRACKET.replace("%value", recv_type)

        text = msg.text
        msg_type = colored(msg.msg_type.title(), "grey")
        if msg.msg_type == "protocolMessage":
            protocol_msg: wa_proto.ProtocolMessage = (
                msg._message.Message.protocolMessage
            )
            protocol_type = wa_proto.ProtocolMessage.Type.Name(protocol_msg.type)
            match protocol_type:
                case "MESSAGE_EDIT":
                    msg_edited: Message = msg.runner.chats[msg.chat].get(
                        protocol_msg.key.id, None
                    )
                    if msg_edited:
                        text_before = msg_edited.text
                        text_after = _get_text(protocol_msg.editedMessage)
                        text = color_diff(text_before, text_after)

            msg_type = colored(f"{protocol_type}", "blue")
        msg_type = self.SQUARE_BRACKET.replace("%value", msg_type)

        sender_name = msg.runner.get_name(msg.sender)
        if group_metadata := msg.group_metadata():
            group_name = group_metadata.subject.name

        sender = pn.parse("+" + msg.sender.split("@")[0])
        sender = pn.format_number(sender, pn.PhoneNumberFormat.INTERNATIONAL)
        chat = f"{group_name}" if msg.is_group else f"{sender}"
        chat_name = sender_name
        chat = self.SQUARE_BRACKET.replace("%value", colored(chat, "light_yellow"))
        chat_name = f"{colored(chat_name, 'blue')}: {text}"
        print(f"{tag} {recv_type} {msg_type} {chat}")
        if msg.quoted:
            quoted_name = msg.runner.get_name(msg.quoted.sender)
            quoted_chat = f"{colored(quoted_name, 'blue')}: {msg.quoted.text if msg.quoted.text else colored(msg.quoted.msg_type.title(), 'grey')}"
            chat_name = f"{quoted_chat} {colored('<=', 'green')} {chat_name}"

        print(chat_name)
