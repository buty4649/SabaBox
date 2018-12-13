import json

class Config:

  def __init__(self, filename="settings.json"):
    f = open(filename, "r")
    self.__json = json.loads(f.read())
    f.close()

  def __getattr__(self, name):
    return self.__json[name]

