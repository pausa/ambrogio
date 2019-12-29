import json
import requests
import datetime as dt

API_TEMPLATE='https://api.darksky.net/forecast'
API_QUERY={
        'exclude':'minutely,hourly,alerts,flags,currently',
        'lang':'it',
        'units':'ca'
        }
SUMMARY={
        'clear-day':'sereno',
        'clear-night':'sereno',
        'clear':'sereno',
        'rain':'piovoso',
        'snow':'nevicoso',
        'sleet':'grandinoso',
        'wind':'ventoso',
        'fog':'nebbioso',
        'cloudy':'nuvoloso',
        'partly-cloudy-day':'parzialmente nuvoloso',
        'partly-cloudy-night':'parzialmente nuvoloso',
        'partly-cloudy':'parzialmente nuvoloso',
        }
api_key = None
with open('private/darksky.json') as json_file:
    api_key = json.load(json_file)['api_key']

def call_api(wreq):
    req="{},{}".format(wreq.lat, wreq.lon)
    if wreq.day:
        req = req + ",{}T00:00:00Z".format(wreq.day)
    res = requests.get(
            "{}/{}/{}".format(API_TEMPLATE, api_key, req),
            params=API_QUERY
            )
    res.raise_for_status()
    daily = res.json()['daily']['data'][0]
    return WeatherResponse(
            dt.datetime.fromtimestamp(daily['time']),
            daily['icon'],
            dt.datetime.fromtimestamp(daily['temperatureLowTime']),
            daily['temperatureLow'],
            daily['apparentTemperatureLow'],
            dt.datetime.fromtimestamp(daily['temperatureHighTime']),
            daily['temperatureHigh'],
            daily['apparentTemperatureHigh']
            )

class WeatherRequest:
    def __init__(self, latitude, longitude, day=None):
        self.lat=latitude
        self.lon=longitude
        self.day=day

class WeatherResponse:
    def __init__ (self, 
            time,
            summary,
            tempLowTime,
            tempLow,
            tempLowFelt,
            tempHighTime,
            tempHigh,
            tempHighFelt):
        self.time = time
        self.summary = summary
        self.summaryHuman = SUMMARY.get(summary, summary)
        self.tempLowTime = tempLowTime
        self.tempLow = tempLow
        self.tempLowFelt = tempLowFelt
        self.tempHighTime = tempHighTime
        self.tempHigh = tempHigh
        self.tempHighFelt = tempHighFelt

if __name__ == "__main__":
    day = dt.date.today() + dt.timedelta(days=1)
    day = None
    def_coordinates={
            'latitude': 52.3873878, 
            'longitude': 4.6462194,
            'day': day
            }
    res = call_api(WeatherRequest(**def_coordinates))
    print ('time: {}'.format(res.tempLowTime))
    print ('time: {}'.format(res.tempHighTime))
    print ('human: {}'.format(res.summaryHuman))
    print ('summary: {}'.format(res.summary))
    print ('templow: {}'.format(res.tempLow))
    print ('temphigh: {}'.format(res.tempHigh))
