from typing import Callable, Any, Dict, List

from luna.utils import logger


class EventEmitter:
    """
    Event emitter class with decorator support for event subscription.

    Provides methods for:
    - Registering event listeners with decorators (@events.on)
    - Manually registering listeners using the on() method
    - Emitting events with optional arguments
    - Removing event listeners

    Examples:
    ```python
    from your_events import events

    emitter = EventEmitter()

    @events.on("trx")
    def handle_transaction(*args, **kwargs):
        logger.info(f"Transaction occurred! Received args: {args}, kwargs: {kwargs}")

    # Manually register another listener
    def logger_event(event_name, *args, **kwargs):
        logger.info(f"Event "{event_name}" emitted with args: {args}, kwargs: {kwargs}")
    emitter.on("any_event")(logger_event)

    emitter.emit("trx", 1, 2, data="some value")  # Triggers handle_transaction
    emitter.emit("other_event", 1, 2, data="some value")  # Triggers logger_event
    ```
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable[..., Any]]] = {}

    def on(self, event_name: str) -> Callable[..., Any]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            logger.info("Registering an event for %s" % event_name)
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            self._listeners[event_name].append(func)
            return func

        return decorator

    def emit(self, event_name: str, *args) -> None:
        """
        Emits an event with optional arguments.

        Args:
            event_name: The name of the event to emit.
            *args: Positional arguments to pass to the listeners.
            **kwargs: Keyword arguments to pass to the listeners.
        """
        if event_name in self._listeners:
            for callback in self._listeners[event_name]:
                callback(*args)

    def remove_listener(self, event_name: str, callback) -> None:
        """
        Removes an event listener.

        Args:
            event_name: The name of the event to remove the listener from.
            callback: The function to remove.
        """
        if event_name in self._listeners:
            try:
                self._listeners[event_name].remove(callback)
            except ValueError:
                pass  # Silently handle if the callback is not found
