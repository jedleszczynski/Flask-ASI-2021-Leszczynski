import requests
import json
import os
COLLEGIUM_ALTUM_LAT=52.40482616077729
COLLEGIUM_ALTUM_LON=16.921709180476395
OPEN_WEATHER_API_KEY=os.environ['OPEN_WEATHER_API_KEY']

def pobierzpogode():
  url = 'http://api.openweathermap.org/data/2.5/weather?lat={0}&lon={1}&appid={2}'.format(
  COLLEGIUM_ALTUM_LAT,
  COLLEGIUM_ALTUM_LON,
  OPEN_WEATHER_API_KEY)
  r = requests.get(url)
  loc_weather = r.content.strip()

  temp,humid,weathertype,rain,pressure = zwroc_elementy_pogody(loc_weather)
  return temp, humid, weathertype, rain, pressure



def zwroc_elementy_pogody(wynik_pogody):
  json_pogody = json.loads(wynik_pogody)
  temp_k = json_pogody["main"]["temp"]
  temp_c = konwertuj_do_c(temp_k)
  humid = json_pogody["main"]["humidity"]
  pressure = json_pogody["main"]["pressure"]
  weathertype = json_pogody["weather"][0]["main"]
  rain = "Opady" if weathertype=="rain" else "Brak"
  return temp_c, humid, weathertype, rain, pressure


def konwertuj_do_c(k):
  return str(round(float(k) - 273.15,2))