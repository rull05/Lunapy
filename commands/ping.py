import time


from luna.wa_classes import Message
from luna import BaseCommand


class Ping(BaseCommand):
    pattern: str = r"ping"
    desc: str = "test speed"
    helper = ["ping"]
    tags = ["main"]

    def execute(self, m: Message):
        start_time = time.time()
        m.reply("Pong!")
        end_time = time.time() - start_time
        m.reply(f"Waktu respon bot: `{end_time:.2f}` detik")
