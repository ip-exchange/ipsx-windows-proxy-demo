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

from typing import Tuple
from re import compile, match
from config import OK
from reg import IEWindowsRegEditor
from util import FileWriter, hex_dump


class ProxyHelper(object):

    EMPTY_STRING = ""
    last_error, last_status = "", ""
    backup_file = ""

    @classmethod
    def read_proxy(cls) -> str:
        net = IEWindowsRegEditor()
        try:
            return net.read_auto_config()
        except:
            return cls.EMPTY_STRING

    @classmethod
    def backup(cls) -> Tuple[bool, str]:
        fw = FileWriter(cls.backup_file)
        net = IEWindowsRegEditor()
        fw.add(net.read_default_connection_settings())
        fw.add(net.read_saved_legacy_settings())
        ok, err = fw.binary_dump()
        if ok:
            cls.last_status = "Created backup at {}".format(cls.backup_file)
        cls.last_error = err
        return ok, err

    @classmethod
    def restoreDefaults(cls) -> "ProxyHelper":
        net = IEWindowsRegEditor()
        net.write_auto_config(cls.EMPTY_STRING)
        bytez_in = net.read_default_connection_settings()
        bytez_out = IEWindowsRegEditor.alter_bin_reg(False, bytez_in)
        net.write_default_connection_settings(bytez_out)
        net.write_saved_legacy_settings(bytez_out)
        cls.last_status = "Proxy configuration disabled!"
        return cls

    @classmethod
    def installPacFile(cls, link: str) -> "ProxyHelper":
        net = IEWindowsRegEditor()
        net.write_auto_config(link)
        bytez_in = net.read_default_connection_settings()
        bytez_out = IEWindowsRegEditor.alter_bin_reg(True, bytez_in, link)
        net.write_default_connection_settings(bytez_out)
        net.write_saved_legacy_settings(bytez_out)
        cls.last_status = "Proxy configuration enabled on your system!"
        return cls

    @classmethod
    def save(cls) -> bytes:
        if cls.last_error != cls.EMPTY_STRING:
            return FAIL
        return OK
