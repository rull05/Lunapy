import subprocess
import shlex

from luna.command import BaseCommand
from luna.wa_classes import Message


class Exec(BaseCommand):
    pattern: str = r"(.*)"
    prefix = "$"
    owner_only = True

    def execute(self, m: Message):
        cmd = f"{m.command} {m.body}"
        cmd = shlex.split(cmd)
        print(cmd)
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            out, err = process.communicate()
            if out:
                m.reply(out.decode("utf-8"))
            if err:
                m.reply(err.decode("utf-8"))
        except Exception as e:
            m.reply(f"Error: {e}")
