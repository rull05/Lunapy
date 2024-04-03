from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Callable, Type

from neonize.events import (
    EVENT_TO_INT,
    CallOfferEv,
    ConnectedEv,
    Event,
    EventType,
    MessageEv,
)
from neonize.utils import log

from luna import CommandHandler
from luna.utils import MessageSerialize, MessagePrint
from luna.wa_classes import Message

import atexit

# import all commands from the commands directory


if TYPE_CHECKING:
    from luna import Runner


class EventHandler(Event):
    """
    Represents an event handler for the runner.

    """

    def __init__(self, runner, **kwargs):
        super().__init__(runner)
        self.dir_commands = kwargs.get("dir_commands", "commands")
        self.executor = ThreadPoolExecutor()
        self.register()
        atexit.register(self.shutdown_thread)

    def on_message(self, runner: "Runner", message: MessageEv):
        msg: Message = MessageSerialize(runner, message).serialize()
        runner.command_handler.handle(msg)
        msg_print = MessagePrint(msg)
        msg_print()

    def shutdown_thread(self):
        self.executor.shutdown(wait=False)

    def on_call(self, runner: "Runner", call: CallOfferEv):
        log.debug(call)
        _ = runner

    def on_connected(self, runner: "Runner", _: ConnectedEv):
        log.info("Bot Connected!")
        runner.initialize_owner()

    def register(self):
        self._register_event(MessageEv, self.on_message)
        self._register_event(CallOfferEv, self.on_call)
        self._register_event(ConnectedEv, self.on_connected)

    def _register_event(self, event: Type[EventType], func: Callable):
        wrapped_func = super().wrap(func, event)
        self.list_func.update({EVENT_TO_INT[event]: wrapped_func})
