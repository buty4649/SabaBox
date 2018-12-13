import binascii
import machine
import urequests
import json
import time

class Mackerel:

  API_BASE_URL = 'https://api.mackerelio.com'

  def __init__(self, apikey):
    self.apikey = apikey
    self.hostid = None

  def init(self, name, hostid=None):
    if hostid:
      self.hostid = hostid
      return

    if self.is_initiazlied():
      return

    try:
      f = open('hostid', 'r')
      self.hostid = f.read()
      f.close()
    except OSError:
      # ファイルがない場合APIを叩いてhostidを登録する
      meta = {
          'agent-name': 'sababox-1.0.0',
          'agent-version': '1.0.0',
          'cpu': [{
            'mhz': int(machine.freq() / 1000 / 1000),
            'model_name': 'ESP32'
          }],
      }
      req = self.request('POST', '/api/v0/hosts', {'name': name, 'meta': meta})
      self.hostid = json.loads(req.text)['id']
      f = open('hostid', 'w')
      f.write(self.hostid)
      f.close()

  def is_initiazlied(self):
    if self.hostid is not None:
      return True
    return False

  def post(self, name, value):
    r = self.request('POST', '/api/v0/tsdb', [{'hostId': self.hostid, 'name': name, 'time': int(time.time()), 'value': value}])
    j = r.json()
    r.close()
    return j


  def request(self, method, path, data):
    header = {'X-Api-Key': self.apikey}
    return urequests.request(method, self.API_BASE_URL + path, json=data, headers=header)

