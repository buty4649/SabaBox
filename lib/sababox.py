from m5stack import lcd
from m5stack import buttonB
import config
import network
import time
import machine
import mackerel
import binascii
import sys

class SabaBox:

  LOGO_FILE='logo.jpg'
  LOGO_SIZE_X=48
  LOGO_SIZE_Y=32
  LOGO_BG_COLOR=0x4EBDDB
  LOGO_TITLE="SabaBox"

  def __init__(self):
    self.wifi = ""
    self.ssid = ""
    self.ip = ""
    self.status = "Initializing"
    self.name = 'sababox-' + binascii.hexlify(machine.unique_id()).decode('utf-8')
    self.lastupdate = ""
    self.plugins = []
    self.wlan = network.WLAN(network.STA_IF)
    self.wlan.active(True)

    self.rtc = machine.RTC()

    self.mc = None

  def init(self):
    lcd.resetwin()
    lcd.clearwin(lcd.WHITE)
    self.draw_logo()

    self.load_config()
    self.update_display()
    if self.status == "Error":
      return

    self.wifi_connect()
    if self.status == "Error":
      self.update_display()
      time.sleep(30)

    if not self.rtc.synced():
      self.rtc.ntp_sync(server="ntp.jst.mfeed.ad.jp", tz="JST-9")
      self.update_display()
      while not self.rtc.synced():
        time.sleep_ms(100)
      self.update_time()
      self.update_display()

    if self.mc is None:
      self.status = "Initializing(Mackerel)"
      self.update_time()
      self.update_display()

      self.mc = mackerel.Mackerel(self.config.mackerel['apikey'])
      self.mc.init(self.name)

      self.status = "Sleeping"
      self.update_time()
      self.update_display()

    # load sernsor plugins
    self.status = "Load plugins"
    self.update_time()
    self.update_display()
    for plugin in self.config.plugins:
      exec("import plugins.%s" % plugin)
      p = eval("plugins.%s.Sensor()" % plugin)
      p.prepare()
      self.plugins.append(p)

  def start(self):
    self.timer = machine.Timer(0)
    self.timer.init(period=60*1000, mode=machine.Timer.PERIODIC, callback=self.on_update)

    self.lcd_off_timer = machine.Timer(1)
    if self.config.autodisplayoff > 0:
      self.lcd_off_timer.init(period=self.config.autodisplayoff*1000, mode=machine.Timer.ONE_SHOT, callback=self.on_lcd_off)

    buttonB.wasPressed(callback=self.on_buttonB_pressed)

    self.on_update(None)

  def on_update(self, timer):
    self.wifi_connect()

    for p in self.plugins:
      p.extract()
      for m in p.metrics:
        n = '%s.%s' %(p.name, m)
        v = p.val[m]
        self.mc.post(n, v)
      self.status = "Updated"

    self.update_time()
    self.update_display()

  def on_lcd_off(self,timer):
    lcd.tft_writecmd(0x28)  # ILI9341_DISPOFF
    lcd.setBrightness(0)

  def on_buttonB_pressed(self):
    lcd.tft_writecmd(0x29)  # ILI9341_DISPON
    lcd.setBrightness(1000)
    if self.lcd_off_timer.isrunning():
      self.lcd_off_timer.deinit()
    self.lcd_off_timer.init(period=10*1000, mode=machine.Timer.ONE_SHOT, callback=self.on_lcd_off)

  def update_display(self):
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(color=lcd.BLACK, bcolor=lcd.WHITE)

    lcd.setCursor(0, 36)
    offset = lcd.textWidth("HostID ")
    lcd.print("Name");   lcd.println(self.name, offset, lcd.LASTY)
    lcd.print("WiFi");   lcd.println(self.wifi, offset, lcd.LASTY, lcd.GREEN)
    lcd.print("SSID");   lcd.println(self.ssid, offset, lcd.LASTY)
    lcd.print("IP");     lcd.println(self.ip, offset, lcd.LASTY)
    lcd.print("NTP");    lcd.println(self.ntp_status(), offset, lcd.LASTY, lcd.GREEN)
    lcd.print("HostID"); lcd.println(self.hostid(), offset, lcd.LASTY, lcd.GREEN)
    lcd.print("Status"); lcd.println(self.status, offset, lcd.LASTY, lcd.GREEN)
    lcd.println(self.lastupdate, offset, lcd.LASTY)

  def draw_logo(self):
    lcd.rect(0, 0, 320, self.LOGO_SIZE_Y, self.LOGO_BG_COLOR, self.LOGO_BG_COLOR)

    lcd.font(lcd.FONT_DejaVu24)
    fw, fh = lcd.fontSize()
    sw, sh = lcd.screensize()
    tw = lcd.textWidth(self.LOGO_TITLE)

    offset = int((320 - self.LOGO_SIZE_X - tw)/2)
    offset_y = int((self.LOGO_SIZE_Y - fh)/2)

    lcd.image(offset, 0, self.LOGO_FILE)

    lcd.setTextColor(color=lcd.WHITE, bcolor=self.LOGO_BG_COLOR)
    lcd.text(offset + self.LOGO_SIZE_X, offset_y, self.LOGO_TITLE)

  def load_config(self):
    try:
      self.config = config.Config()
    except:
      self.status = "Error"

  def ntp_status(self):
    if self.rtc.synced():
      return "OK"
    return "NG"

  def hostid(self):
    if self.mc is not None:
      return self.mc.hostid
    return ""

  def wifi_connect(self):
    if self.wlan.isconnected():
      return

    while not self.wlan.isconnected():
      self.wifi = "Scanning"
      self.ssid = ""
      self.update_display()

      for net in self.wlan.scan():
        ssid = net[0].decode('utf-8')

        if ssid in self.config.wifi:
          self.wlan.connect(ssid, self.config.wifi[ssid])

          self.wifi = "Connecting"
          self.ssid = ssid
          self.update_display()

          retry_count = 0
          retry_max = 50

          while not self.wlan.isconnected() and retry_count < retry_max:
            retry_count += 1
            time.sleep_ms(100)

          if self.wlan.isconnected():
            self.wifi = "Connected"
            self.ip = self.wlan.ifconfig()[0]
            self.update_display()
            return

      self.wifi = "Error"
      self.update_display()
      time.sleep(3)

  def update_time(self):
    self.lastupdate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class SensorBase:
  name = ''
  metrics = None

  def prepare(self):
    self.val = {}
    for m in self.metrics:
      self.val[m] = 0

  def extract(self):
    raise NotImplementedError()
