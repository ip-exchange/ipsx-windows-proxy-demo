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

import winreg
import struct


class IEWindowsRegEditor(object):
    """
    Helper class for Windows Internet Settings Registry

    Some registry keys and byte order/masks are taken from:
    https://blogs.msdn.microsoft.com/askie/2017/06/20/what-is-defaultconnectionsettings-key/
    """

    AUTO_CONFIG_REGVAL = "AutoConfigURL"
    CONNECTION_SETTINGS = "DefaultConnectionSettings"
    LEGACY_SETTINGS = "SavedLegacySettings"
    CFG_IDX = 8
    LEN_IDX = 20
    STR_IDX = 24
    PADDING_LEN = 24
    NOOP = 0x01
    ALL = 0x0f
    AUTO_DETECT_SETTINGS = 0x09
    AUTO_CONFIG_SCRIPT = 0x05
    MANUAL_PROXY = 0x03
    LITTLE = ">"
    CHAR = "B"

    COMPLETE_REG_PATH = (
        "Software",
        "Microsoft",
        "Windows",
        "CurrentVersion",
        "Internet Settings",
        "Connections"
    )

    HKEY = winreg.HKEY_CURRENT_USER
    ACCESS = winreg.KEY_ALL_ACCESS

    def __init__(self):
        self.query = winreg.QueryValueEx
        self.ropen = winreg.OpenKey
        self.rsave = winreg.SetValueEx
        self.auto_config_path = -1
        self.connection_settings_path = len(self.COMPLETE_REG_PATH)

    def rfind(self, path: tuple) -> tuple:
        return self.HKEY, "\\".join(path), 0, self.ACCESS

    def get_reg(self, index: int):
        params = self.rfind(self.COMPLETE_REG_PATH[:index])
        return self.ropen(*params)

    def read_auto_config(self) -> str:
        reg = self.get_reg(self.auto_config_path)
        value, _ = self.query(reg, self.AUTO_CONFIG_REGVAL)
        return value

    def write_auto_config(self, value: str) -> None:
        reg = self.get_reg(self.auto_config_path)
        self.rsave(reg, self.AUTO_CONFIG_REGVAL, 0, winreg.REG_SZ, value)

    def read_default_connection_settings(self) -> bytes:
        reg = self.get_reg(self.connection_settings_path)
        value, _ = self.query(reg, self.CONNECTION_SETTINGS)
        return value

    def write_default_connection_settings(self, value: bytes) -> None:
        reg = self.get_reg(self.connection_settings_path)
        self.rsave(reg, self.CONNECTION_SETTINGS, 0, winreg.REG_BINARY, value)

    def read_saved_legacy_settings(self) -> bytes:
        reg = self.get_reg(self.connection_settings_path)
        value, _ = self.query(reg, self.LEGACY_SETTINGS)
        return value

    def write_saved_legacy_settings(self, value: bytes) -> None:
        reg = self.get_reg(self.connection_settings_path)
        self.rsave(reg, self.LEGACY_SETTINGS, 0, winreg.REG_BINARY, value)

    @classmethod
    def alter_bin_reg(cls, enable: bool, bytes_in: bytes, data: str="") -> bytes:
        byte_list = list(bytes_in)
        cfg = cls.AUTO_DETECT_SETTINGS
        if enable:
            cfg |= cls.AUTO_CONFIG_SCRIPT
        byte_list[cls.CFG_IDX] = cfg
        start_idx = cls.STR_IDX
        end_idx = byte_list[cls.LEN_IDX]
        end_idx += cls.STR_IDX
        del byte_list[start_idx:end_idx]
        data_len = len(data.strip())
        if data_len > 0:
            chars = [ord(c) for c in data]
            enc = cls.LITTLE + (cls.CHAR * data_len)
            byte_list[start_idx:start_idx] = struct.pack(enc, *chars)
        byte_list[cls.LEN_IDX] = data_len
        return bytes(byte_list)
