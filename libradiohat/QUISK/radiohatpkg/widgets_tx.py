# This module is used to add extra Radiohat widgets to the QUISK screen.

import wx
import _quisk as QS
import math

class BottomWidgets:	# Add extra widgets to the bottom of the screen
  def __init__(self, app, hardware, conf, frame, gbs, vertBox):
    self.config = conf
    self.hardware = hardware
    self.application = app
    self.start_row = app.widget_row			# The first available row
    self.start_col = app.button_start_col	# The start of the button columns
    self.Widgets_0x06(app, hardware, conf, frame, gbs, vertBox)
    self.UpdateText(0,0,0)

  def Widgets_0x06(self, app, hardware, conf, frame, gbs, vertBox):
    self.num_rows_added = 1
    start_row = self.start_row
    if conf.button_layout == "Small screen":
      # Display three data items in a single window
      self.text_pa_voltage = app.QuiskText1(frame, '', bh)
      self.text_fwd_power = app.QuiskText1(frame, '', bh)
      self.text_swr = app.QuiskText1(frame, '', bh)
      self.text_pa_voltage.Hide()
      self.text_fwd_power.Hide()
      self.text_swr.Hide()
      b = app.QuiskPushbutton(frame, self.OnTextDataMenu, '..')
      szr = self.data_sizer = wx.BoxSizer(wx.HORIZONTAL)
      szr.Add(self.text_data, 1, flag=wx.ALIGN_CENTER_VERTICAL)
      szr.Add(b, 0, flag=wx.ALIGN_CENTER_VERTICAL)
      gbs.Add(szr, (start_row, self.start_col + 10), (1, 2), flag=wx.EXPAND)
      # Make a popup menu for the data window
      self.text_data_menu = wx.Menu()
      item = self.text_data_menu.Append(-1, 'Battery')
      app.Bind(wx.EVT_MENU, self.OnDataPaVoltage, item)
      item = self.text_data_menu.Append(-1, 'Fwd Power')
      app.Bind(wx.EVT_MENU, self.OnDataFwdPower, item)
      item = self.text_data_menu.Append(-1, 'SWR')
      app.Bind(wx.EVT_MENU, self.OnDataSwr, item)
    else:
      szr = wx.BoxSizer(wx.HORIZONTAL)
#      gbs.Add(szr, (start_row, self.start_col + 10), (1, 18), flag=wx.EXPAND)
      gbs.Add(szr, (start_row, self.start_col + 10), (1,18), flag=wx.ALIGN_RIGHT)
#      text_pa_voltage = wx.StaticText(frame, -1, ' Temp 100DC XX', style=wx.ST_NO_AUTORESIZE)
      text_pa_voltage = wx.StaticText(frame, -1, ' Batt: XX.X v ', style=wx.ST_NO_AUTORESIZE)
      size = text_pa_voltage.GetBestSize()
      text_pa_voltage.Destroy()
      self.text_pa_voltage = wx.StaticText(frame, -1, '', size=size, style=wx.ST_NO_AUTORESIZE)
      self.text_fwd_power = wx.StaticText(frame, -1, '', size=size, style=wx.ST_NO_AUTORESIZE)
      self.text_swr = wx.StaticText(frame, -1, '', size=size, style=wx.ST_NO_AUTORESIZE)
      flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL
      szr.Add(self.text_pa_voltage, 0, flag=flag)
      szr.Add(self.text_fwd_power, 0, flag=flag)
      szr.Add(self.text_swr, 0, flag=flag)

  def UpdateVoltageText(self, voltage):
    volts = " Batt: %2.1f v" % (voltage)
    self.text_pa_voltage.SetLabel(volts)

  def UpdateFwdText(self, fwd):
    text = " Pwr: %3.1f w" % fwd
    self.text_fwd_power.SetLabel(text)

  def UpdateVswrText(self, vswr):
    if vswr < 9.95:
        text = " Vswr: %4.2f" % vswr
    else:
        text = " Vswr: %4.0f" % vswr
    self.text_swr.SetLabel(text)

  def UpdateText(self,voltage,fwd,vswr):
    self.UpdateVoltageText(0)
    self.UpdateVswrText(0)
    self.UpdateFwdText(0)
    
  def OnTextDataMenu(self, event):
    btn = event.GetEventObject()
    btn.PopupMenu(self.text_data_menu, (0,0))

  def OnDataPaVoltage(self, event):
    self.data_sizer.Replace(self.text_data, self.text_pa_voltage)
    self.text_data.Hide()
    self.text_data = self.text_pa_voltage
    self.text_data.Show()
    self.data_sizer.Layout()

  def OnDataFwdPower(self, event):
    self.data_sizer.Replace(self.text_data, self.text_fwd_power)
    self.text_data.Hide()
    self.text_data = self.text_fwd_power
    self.text_data.Show()
    self.data_sizer.Layout()

  def OnDataSwr(self, event):
    self.data_sizer.Replace(self.text_data, self.text_swr)
    self.text_data.Hide()
    self.text_data = self.text_swr
    self.text_data.Show()
    self.data_sizer.Layout()
