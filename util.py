# #!/usr/bin/env python
#
# Copyright 2018 ip.sx
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Tuple, List
from urllib.parse import urlparse
from res import HISTORY_LOG_FILE


class FileWriter(object):

    buffer = set([])

    def __init__(self, filepath: str):
        self.filepath = filepath

    def add(self, data: bytes) -> "FileWriter":
        self.buffer.add(data)
        return self

    def binary_dump(self) -> Tuple[bool, str]:
        try:
            with open(self.filepath, "wb") as file_:
                [file_.write(d) for d in self.buffer]
        except Exception as e:
            return False, str(e)
        return True, ""

    def flush(self) -> "FileWriter":
        self.buffer = set([])
        return self


def hex_dump(data: bytes) -> List[Tuple]:
    return [(i, b) for i, b in enumerate(list(data))]


def validate_pac_url(url: str) -> bool:
    if len(url.strip()) == 0:
        return False
    vld = urlparse(url)
    if vld.scheme not in ("http", "https"):
        return False
    if vld.netloc == "":
        return False
    if not vld.path.endswith(".pac"):
        return False
    return True


def history_log(event: str) -> Tuple[bool, str]:
    try:
        with open(HISTORY_LOG_FILE, "a") as file_:
            file_.write(event)
        return True, event
    except Exception as e:
        return False, str(e)

def history_init() -> Tuple[bool, str]:
    try:
        with open(HISTORY_LOG_FILE, "r") as file_:
            return True, file_.read()
    except Exception as e:
        return False, str(e)
