#!/usr/bin/env python
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

import wx

from typing import Callable
from res import APP_CONFIG, OK, BACKUP_REG, BACKUP_ERR, INVALID_URL
from proxy import ProxyHelper
from util import validate_pac_url, history_log, history_init


class IPSXFrame(wx.Frame):
    """
    IP.SX Main Frame for GUI.
    """

    LABEL = "IP.SX proxy auto config URI"

    INPUT_STYLE = {
        "flag": wx.ALL | wx.ALIGN_CENTER_VERTICAL,
        "border": 5,
    }

    ENABLE_BTN_STYLE = {
        "label": "Install PAC file",
        "size": (130, -1)
    }

    DISABLE_BTN_STYLE = {
        "label": "Restore config",
        "size": (130, -1)
    }

    DIALOG_PROPS = (
        "Info", wx.OK
    )

    def __init__(self):
        wx.Frame.__init__(self, None, **APP_CONFIG)
        self.panel = wx.Panel(self)
        self.sizer = wx.GridBagSizer(vgap=0, hgap=5)
        self.setup()
        self.panel.SetSizerAndFit(self.sizer)
        self.statusbar = self.CreateStatusBar()
        self.Show(True)

    def setup(self):
        self.create_header()
        self.create_enable_btn()
        self.create_disable_btn()
        self.create_pac_input()
        self.create_history()
        sizer_input = wx.BoxSizer(wx.VERTICAL)
        sizer_btns = wx.BoxSizer(wx.HORIZONTAL)
        sizer_input.Add(self.label)
        sizer_input.Add(self.pac_link_input)
        sizer_btns.Add(self.enable_btn)
        sizer_btns.Add(self.disable_btn)
        self.sizer.Add(sizer_input, pos=(0, 0), border=5, flag=wx.ALL|wx.EXPAND)
        ln = wx.StaticLine(self.panel, -1, style=wx.LI_HORIZONTAL)
        self.sizer.Add(ln, pos=(1, 0), border=5, flag=wx.ALL|wx.EXPAND)
        self.sizer.Add(sizer_btns, pos=(2, 0), border=5, flag=wx.ALL|wx.EXPAND)
        self.sizer.Add(self.history, pos=(3, 0), border=5, flag=wx.ALL|wx.EXPAND)

    def create_header(self):
        pass

    def create_history(self):
        self.history = wx.TextCtrl(self.panel, wx.ID_ANY, style=wx.TE_MULTILINE|wx.TE_READONLY, size=(260, 180))
        ok, txt = history_init()
        if not ok:
            txt = "...\n"
        self.history.SetValue(txt)

    def create_pac_input(self):
        self.label = wx.StaticText(self.panel, wx.ID_ANY, self.LABEL)
        self.pac_link_input = wx.TextCtrl(self.panel, wx.ID_ANY, size=(260, -1))
        proxy = ProxyHelper.read_pac_link()
        if len(proxy) > 0:
            self.enable_btn.Disable()
            self.pac_link_input.SetValue(proxy)
        else:
            self.disable_btn.Disable()

    def create_enable_btn(self):
        self.enable_btn = wx.Button(self.panel, wx.ID_ANY, **self.ENABLE_BTN_STYLE)
        self.enable_btn.SetDefault()
        self.Bind(wx.EVT_BUTTON, self._enable_proxy_cb, self.enable_btn)

    def create_disable_btn(self):
        self.disable_btn = wx.Button(self.panel, wx.ID_ANY, **self.DISABLE_BTN_STYLE)
        self.Bind(wx.EVT_BUTTON, self._disable_proxy_cb, self.disable_btn)

    def _enable_proxy_cb(self, event):
        link = self.pac_link_input.GetValue()
        if not validate_pac_url(link):
            self.alert_dialog(INVALID_URL)
            return
        ok, err = ProxyHelper.backup()
        if not ok:
            ProxyHelper.last_error = BACKUP_ERR.format(err)
        else:
            self._invoke_helper(ProxyHelper.install_pac_file, link)
            self.enable_btn.Disable()
            self.disable_btn.Enable()
        self.alert_dialog()

    def _disable_proxy_cb(self, event):
        self._invoke_helper(ProxyHelper.restore_defaults)
        self.alert_dialog()
        self.disable_btn.Disable()
        self.enable_btn.Enable()

    def _invoke_helper(self, cb: Callable, *args: str) -> str:
        if cb(*args).save() is not OK:
            return ProxyHelper.get_last_error()
        return ProxyHelper.get_last_status()

    def alert_dialog(self, message: str=""):
        if message == ProxyHelper.EMPTY_STRING:
            message = ProxyHelper.get_last_status()
        self.log_event(message)
        alert = wx.MessageDialog(self, message, *self.DIALOG_PROPS)
        alert.ShowModal()
        alert.Destroy()

    def log_event(self, event):
        self.statusbar.SetStatusText(event)
        self.history.AppendText("{}\n".format(event))
        ok, txt = history_log("{}\n".format(event))
        if not ok:
            pass # TODO: handle this
