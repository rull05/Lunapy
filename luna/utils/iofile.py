import requests
import re
from pathlib import Path
from datetime import datetime
import magic
import mimetypes
from typing import Union, Optional


URL_MATCH = re.compile(r"^https?://")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
}


def save_to_file(data: Union[str, bytes], filename: Optional[str] = None) -> str:
    if filename is None:
        # default filename is current time with milisecond
        current_time = datetime.now()
        filename = current_time.strftime("%Y-%m-%d_%H-%M-%S-%f")

    cwd = Path.cwd()
    tmp_folder = cwd.joinpath("tmp")
    if not tmp_folder.exists():
        tmp = cwd / "tmp"
        tmp.mkdir()

    buff = data
    if isinstance(data, str):
        if URL_MATCH.match(data):
            buff = requests.get(data, headers=HEADERS).content
        else:
            with open(data, "rb") as f:
                buff = f.read()
    mime = magic.from_buffer(buff, mime=True)
    ext = mimetypes.guess_extension(mime)
    filepath = tmp_folder / (filename + f"{ext}")
    with open(filepath, "wb") as f:
        f.write(buff.encode() if isinstance(buff, str) else buff)
    # returning a str path
    return str(filepath)
