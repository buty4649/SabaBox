import sababox
from machine import I2C, Pin

class Sensor(sababox.SensorBase):

  def __init__(self):
    self.name = 'dht12'
    self.metrics = ['temperature', 'humidity']
    self.i2c = I2C(sda=21, scl=22)
    self.addr = 0x5c

  def extract(self):
    buf = bytearray(5)
    self.i2c.readfrom_mem_into(self.addr, 0, buf)
    if (buf[0] + buf[1] + buf[2] + buf[3]) & 0xff != buf[4]:
      raise Exception("checksum error")

    t = buf[2] + (buf[3] & 0x7f) * 0.1
    if buf[3] & 0x80:
      t = -t
    self.val['temperature'] = t
    self.val['humidity'] = buf[0] + buf[1] * 0.1
