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
from config import APP_CONFIG, OK, BACKUP_REG, BACKUP_ERR, INVALID_URL
from proxy import ProxyHelper
from util import validate_pac_url


class IPSXFrame(wx.Frame):

    input_style = {
        "flag": wx.ALL | wx.ALIGN_CENTER_VERTICAL,
        "border": 5,
    }

    enable_btn_style = {
        "label": "Install PAC file",
        "size": (120, -1)
    }

    disable_btn_style = {
        "label": "Restore config",
        "size": (120, -1)
    }

    dialog_props = (
        "Info", wx.OK
    )

    def __init__(self):
        wx.Frame.__init__(self, None, **APP_CONFIG)
        self.panel = wx.Panel(self)
        self.sizer = wx.GridBagSizer(vgap=2, hgap=1)
        self.SetupLayout()
        self.panel.SetSizerAndFit(self.sizer)
        self.CreateStatusBar()
        self.Show(True)

    def SetupLayout(self):
        self.CreatePacInput()
        self.CreateEnableBtn()
        self.CreateDisableBtn()

    def CreatePacInput(self):
        self.pacLinkInput = wx.TextCtrl(self.panel, size=(200, -1))
        self.pacLinkInput.SetValue(ProxyHelper.read_proxy())
        self.sizer.Add(self.pacLinkInput, pos=(0 ,0), **self.input_style)

    def CreateEnableBtn(self):
        enableProxyBtn = wx.Button(self.panel, **self.enable_btn_style)
        enableProxyBtn.SetDefault()
        self.sizer.Add(enableProxyBtn, pos=(1, 0), **self.input_style)
        self.Bind(wx.EVT_BUTTON, self._enableProxyCb, enableProxyBtn)

    def CreateDisableBtn(self):
        disableProxyBtn = wx.Button(self.panel, **self.disable_btn_style)
        self.Bind(wx.EVT_BUTTON, self._disableProxyCb, disableProxyBtn)
        self.sizer.Add(disableProxyBtn, pos=(2, 0), **self.input_style)

    def _enableProxyCb(self, event):
        link = self.pacLinkInput.GetValue()
        if not validate_pac_url(link):
            self.alertDialog(INVALID_URL)
            return
        ok, err = ProxyHelper.backup()
        if not ok:
            ProxyHelper.last_error = BACKUP_ERR.format(err)
        else:
            self._invokeProxyHelper(ProxyHelper.installPacFile, link)
        self.alertDialog()

    def _disableProxyCb(self, event):
        self._invokeProxyHelper(ProxyHelper.restoreDefaults)
        self.alertDialog()

    def _invokeProxyHelper(self, cb: Callable, *args: str) -> str:
        if cb(*args).save() is not OK:
            return ProxyHelper.last_error
        return ProxyHelper.last_status

    def alertDialog(self, message: str=""):
        if message == ProxyHelper.EMPTY_STRING:
            message = ProxyHelper.last_status
        alert = wx.MessageDialog(self, message, *self.dialog_props)
        alert.ShowModal()
        alert.Destroy()
