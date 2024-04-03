from neonize.proto.Neonize_pb2 import JID
from neonize.utils.jid import JIDToNonAD, Jid2String
import inspect


def str_to_jid(jid: str, raw_agent=0, device=0, integrator=0, is_empty=False) -> JID:
    """Convert a string to a JID object"""
    user, server = jid.split("@")
    if not user or not server:
        is_empty = True
    return JID(
        User=user,
        Server=server,
        RawAgent=raw_agent,
        Device=device,
        Integrator=integrator,
        IsEmpty=is_empty,
    )


def jid_to_str(jid: JID) -> str:
    """Convert a JID object to a string"""
    return Jid2String(JIDToNonAD(jid))


def get_repr(obj) -> str:
    """
    Get the repr of an object class
    """
    attributes = inspect.getmembers(obj)
    attr_strings = (
        f'    {name}: {repr(value) if not callable(value) or inspect.isclass(value) else f"{name}{inspect.signature(value)}"}'
        for name, value in attributes
        if not name.startswith("_")
    )
    return f"{obj.__class__.__name__} {{\n" + ",\n".join(attr_strings) + "\n}"
