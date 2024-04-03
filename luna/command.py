import importlib
import inspect
import pathlib
import re
import string
from enum import Enum
from typing import TYPE_CHECKING, Optional, Set, Tuple, Union

from watchdog.events import (
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from luna.utils import logger

if TYPE_CHECKING:
    from luna.wa_classes import Message


class PermissionError(Enum):
    GROUP_ONLY = "Perintah ini hanya bisa digunakan di grup"
    PRIVATE_ONLY = "Perintah ini hanya bisa digunakan di private chat"
    SUPERADMIN_ONLY = "Perintah ini hanya bisa digunakan oleh owner grup"
    ADMIN_ONLY = "Perintah ini hanya bisa digunakan oleh admin grup"
    OWNER_ONLY = True


def is_overridden(_cls, instance, method_name):
    """Check if a method is overridden in a subclass."""
    if not hasattr(instance, method_name):
        return False

    func_method = getattr(instance, method_name)
    cls_method = getattr(_cls, method_name)
    return func_method.__code__ is not cls_method.__code__


class BaseCommand:
    owner_only: bool = False
    group_only: bool = False
    private_only: bool = False
    admin_only: bool = False
    superadmin_only: bool = False
    premium_only: bool = False
    limit_usage: int = 0
    name: str = ""
    tags: Optional[Union[str, list[str]]] = None
    description: str = ""
    usage: Union[str, list[str]] = ""
    pattern: str = ""
    prefix: Optional[str] = None
    _pattern: Optional[re.Pattern[str]] = None
    _prefix: Optional[re.Pattern[str]] = None
    on_message_is_overridden: bool = False
    exec_is_overridden: bool = False

    def __init_subclass__(cls):
        cls.name = cls.__name__ if not cls.name else cls.name
        exec_overridden = is_overridden(cls, BaseCommand, "execute")
        on_message_overridden = is_overridden(cls, BaseCommand, "on_message")

        if not exec_overridden:
            if not on_message_overridden:
                raise ValueError("Execute or on_message method must be overridden")

        if exec_overridden:
            if not cls.pattern:
                raise ValueError("Pattern cannot be empty")
            pattern = cls.pattern if cls.pattern.startswith("^") else f"^{cls.pattern}"
            pattern = pattern if pattern.endswith("$") else f"{pattern}$"

            cls._pattern = re.compile(pattern, re.I)
            cls._prefix = (
                re.compile(f"^{re.escape(cls.prefix)}") if cls.prefix else None
            )

        if on_message_overridden:
            if not hasattr(cls.on_message, "__annotations__"):
                raise ValueError("on_message method must have the correct signature")

        cls.on_message_is_overridden = on_message_overridden
        cls.exec_is_overridden = exec_overridden

    def on_message(self, m: "Message", *args, **kwargs): ...

    def execute(self, m: "Message", *args, **kwargs): ...

    def match(self, text: str):
        if self._pattern:
            return self._pattern.search(text)
        return False

    def get_prefix(self) -> Optional[re.Pattern[str]]:
        return self._prefix

    def get_pattern(self) -> Optional[re.Pattern[str]]:
        return self._pattern

    def __repr__(self):
        text = f"Name: {self.name}"
        if self.tags:
            text += f"\nTags: {self.tags}"
        if self.description:
            text += f"\nDescription: {self.description}"
        if self.usage:
            text += f"\nUsage: {self.usage}"
        return text

    def get_usage(self, prefix: str):
        if isinstance(self.usage, tuple):
            usage = "".join((f"{prefix}{u}\n" for u in self.usage))
        else:
            usage = f"{prefix}{self.usage}"
        return usage


CommandPathLike = Union[str, pathlib.Path]
CommandPair = Tuple[CommandPathLike, BaseCommand]
SetOfCommand = Set[CommandPair]


class CommandHandler:
    def __init__(
        self, dir_commands: str = "commands", prefix: str = string.punctuation
    ):
        self.commands: SetOfCommand = set()
        self.dir = pathlib.Path(dir_commands)
        self._prefix = re.compile(f"^[{re.escape(prefix)}]", re.I)
        self.load_commands()
        self._observer = Observer()

        self._watcher = self._observer.schedule(
            FileReloader(self), self.dir, recursive=True
        )

        self._observer.start()

    def load_command(self, path: pathlib.Path, reload: bool = False):
        try:
            self._import_and_register(path, reload)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")

    def load_commands(self, directory: Optional[pathlib.Path] = None) -> None:
        if directory is None:
            directory = self.dir

        for path in directory.iterdir():
            if path.name.startswith("__") or path.name.startswith("."):
                continue

            if path.is_dir():
                if not any(path.iterdir()):
                    continue

                init_file = path / "__init__.py"
                init_file.touch(exist_ok=True)
                dir_name = directory / path.name
                self.load_commands(dir_name)

            elif path.suffix == ".py":
                self._import_and_register(path)

    def _import_and_register(self, path: pathlib.Path, reload: bool = False) -> None:
        try:
            module_path = path.as_posix().replace("/", ".")[:-3]
            module = importlib.import_module(module_path)
            if reload:
                importlib.reload(module)

            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseCommand)
                    and obj != BaseCommand
                ):
                    self.register(obj, path)
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")

    def register(
        self, command: type[BaseCommand], command_path: CommandPathLike
    ) -> None:
        reload = False
        for c in self.commands:
            if c[1].name == command.name:
                reload = True
                self.commands.remove(c)
                break
        logger.info(
            f"{'re - ' if reload else ''}Registering {command.name} from {command_path}"
        )
        self.commands.add((command_path, command()))

    def unregister(self, pathLike: CommandPathLike) -> None:
        path = pathlib.Path(pathLike)
        for command in self.commands:
            if command[0] == path:
                self.commands.remove(command)
                logger.warn(f"Unregistered {command[1].name} from {command[0]}")
                break

    def get_command(self, name: str) -> Optional[CommandPair]:
        for command in self.commands:
            if command[1].name == name:
                return command
        return None

    def get_commands(self) -> SetOfCommand:
        return self.commands

    def handle(self, m: "Message") -> None:
        if m.is_bot:
            return

        if m.chat == "status@broadcast":
            return

        for name, command in self.commands:
            if command.on_message_is_overridden:
                if not command.on_message(m):
                    continue

            _prefix = self._prefix
            if cmd_prefix := command.get_prefix():
                _prefix = cmd_prefix

            if match_prefix := _prefix.search(m.text):
                no_prefix = m.text[match_prefix.end() :].strip()
                used_command, *args = no_prefix.split(" ")
                body = " ".join(args)
                match_command = command.match(used_command)
                if not match_command:
                    continue
                if error := self.validate(m, command):
                    if isinstance(error, str):
                        m.reply(error)
                    return
                m.command = match_command[0]
                m.body = body
                m.used_prefix = match_prefix[0]
                if command.exec_is_overridden:
                    command.execute(m)
                    return

    def validate(
        self, m: "Message", command: BaseCommand
    ) -> Optional[Union[str, bool]]:
        if command.admin_only or command.superadmin_only:
            command.group_only = True

        if command.owner_only and m.sender not in m.runner.owners:
            return PermissionError.OWNER_ONLY.value

        if group_metadata := m.group_metadata():
            if command.private_only:
                return PermissionError.PRIVATE_ONLY.value
            admin_status = group_metadata.is_sender_admin
            if command.admin_only and admin_status != "admin":
                return PermissionError.ADMIN_ONLY.value
            if command.superadmin_only and admin_status != "superadmin":
                return PermissionError.SUPERADMIN_ONLY.value
        else:
            if command.group_only:
                return PermissionError.GROUP_ONLY.value


class FileReloader(FileSystemEventHandler):
    def __init__(self, handler: CommandHandler):
        self.handler = handler

    def on_modified(self, event: FileModifiedEvent):
        if event.is_directory:
            return
        if event.src_path.endswith(".py"):
            self.handler.load_command(pathlib.Path(event.src_path), reload=True)

    def on_deleted(self, event: FileDeletedEvent):
        self.handler.unregister(event.src_path)
