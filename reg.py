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

    Some registry key values and byte order/masks are taken from:
    https://blogs.msdn.microsoft.com/askie/2017/06/20/what-is-defaultconnectionsettings-key/

    This is a work-in-progress that tries to decode two Windows registries:
    DefaultConnectionSettings and SavedLegacySettings (the last one is a copy of
    the first; more or less).
    """

    INT16 = struct.calcsize("h")
    INT32 = struct.calcsize("i")

    AUTO_CONFIG_REGVAL = "AutoConfigURL"
    CONNECTION_SETTINGS = "DefaultConnectionSettings"
    LEGACY_SETTINGS = "SavedLegacySettings"

    PROXY_IDX = 8
    X_LEN_IDX = 16

    NOOP = 0x01
    ALL = 0x0f
    AUTO_DETECT_SETTINGS = 0x09
    AUTO_CONFIG_SCRIPT = 0x05
    MANUAL_PROXY = 0x03

    LITTLE = ">"
    NATIVE = "@"
    CHAR = "B"
    INT = "i"

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
        """
        Registry finder. Creates ready-to-use params for the registry opener.

        Args:
            path (tuple) - Path to registry key tokens.

        Returns:
            tuple - Registry opener parameter arguments.
        """
        return self.HKEY, "\\".join(path), 0, self.ACCESS

    def get_reg(self, index: int) -> "PyHKEY":
        """
        Registry opener. Retrieves the handle object of the Windows Registry.

        Args:
            index (int) - Stop index of the registry path.

        Returns:
            Windows HKEY
        """
        params = self.rfind(self.COMPLETE_REG_PATH[:index])
        return self.ropen(*params)

    def read_auto_config(self) -> str:
        """
        Getter interface for AutoConfigURL registry.

        Returns:
            str - Value of AutoConfigURL.
        """
        reg = self.get_reg(self.auto_config_path)
        value, _ = self.query(reg, self.AUTO_CONFIG_REGVAL)
        return value

    def write_auto_config(self, value: str) -> None:
        """
        Setter interface for AutoConfigURL registry.

        Args:
            value (str) - Value to write.

        Returns:
            None
        """
        reg = self.get_reg(self.auto_config_path)
        self.rsave(reg, self.AUTO_CONFIG_REGVAL, 0, winreg.REG_SZ, value)

    def read_default_connection_settings(self) -> bytes:
        """
        Getter interface for DefaultConnectionSettings registry.

        Returns:
            bytes - Value of DefaultConnectionSettings.
        """
        reg = self.get_reg(self.connection_settings_path)
        value, _ = self.query(reg, self.CONNECTION_SETTINGS)
        return value

    def write_default_connection_settings(self, value: bytes) -> None:
        """
        Setter interface for DefaultConnectionSettings registry.

        Args:
            value (bytes) - Value to write.

        Returns:
            None
        """
        reg = self.get_reg(self.connection_settings_path)
        self.rsave(reg, self.CONNECTION_SETTINGS, 0, winreg.REG_BINARY, value)

    def read_saved_legacy_settings(self) -> bytes:
        """
        Getter interface for SavedLegacySettings registry.

        Returns:
            bytes - Value of SavedLegacySettings.
        """
        reg = self.get_reg(self.connection_settings_path)
        value, _ = self.query(reg, self.LEGACY_SETTINGS)
        return value

    def write_saved_legacy_settings(self, value: bytes) -> None:
        """
        Setter interface for DefaultConnectionSettings registry.

        Args:
            value (bytes) - Value to write.

        Returns:
            None
        """
        reg = self.get_reg(self.connection_settings_path)
        self.rsave(reg, self.LEGACY_SETTINGS, 0, winreg.REG_BINARY, value)

    @classmethod
    def alter_bin_reg(cls, enable: bool, bytes_in: bytes, data: str="") -> bytes:
        """
        Helper method to edit bytes values for Windows Registries.

        Args:
            enable (bool) - Wheather to enable or not the auto config script.
            bytes_in (bytes) - Initial bytes as an input.
            data (str) - Additional string sequence to append to registry.

        Returns:
            bytes - The updated input.

        Raises:
            ValueError - If some bytes order are not as expected.
        """
        byte_list = list(bytes_in)
        cfg = cls.AUTO_DETECT_SETTINGS
        data_length = len(data.strip())

        # It's the equivalent of the GUI's checkbox for the "Use automatic
        # configuration script". Update configuration byte afterwards
        if enable:
            cfg |= cls.AUTO_CONFIG_SCRIPT
        byte_list[cls.PROXY_IDX:cls.PROXY_IDX+cls.INT32] = [cfg, 0x0, 0x0, 0x0]

        # Resolve X-Byte order and padding
        x_size = byte_list[cls.X_LEN_IDX:cls.X_LEN_IDX + cls.INT32]
        x_len = struct.unpack(cls.NATIVE + cls.INT, bytes(x_size))
        if len(x_len) == 0:
            raise ValueError("Invalid format")
        x_len = x_len[0]

        # Resolve data byte order and data len
        data_len_start = cls.X_LEN_IDX + cls.INT32 + x_len
        data_len_end = data_len_start + cls.INT32
        b_size = byte_list[data_len_start:data_len_end]
        data_len = struct.unpack(cls.NATIVE + cls.INT, bytes(b_size))
        if len(data_len) == 0:
            raise ValueError("Invalid format")
        data_len = data_len[0]

        # Set data length
        b_size_in = struct.pack(cls.NATIVE + cls.INT, data_length)
        byte_list[data_len_start:data_len_end] = list(b_size_in)

        # Remove old data
        data_start = data_len_end
        data_end = data_start + data_len
        del byte_list[data_start:data_end]

        # Set new data
        chars = [ord(c) for c in data]
        enc = cls.NATIVE + (cls.CHAR * data_length)
        byte_list[data_start:data_start] = struct.pack(enc, *chars)
        return bytes(byte_list)
