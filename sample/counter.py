import sababox

class Sensor(sababox.SensorBase):

  def __init__(self):
    self.name = 'sample'
    self.metrics = ['value']
    self.value = 0

  def extract(self):
    self.val['value'] = self.value
    self.value += 1
