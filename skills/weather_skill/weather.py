import json
import urllib.parse
import urllib.request


class WeatherService:

    GEO_URL = 'https://geocoding-api.open-meteo.com/v1/search'
    WEATHER_URL = 'https://api.open-meteo.com/v1/forecast'

    def _geocode(self, location):
        url = f'{self.GEO_URL}?name={urllib.parse.quote(location)}&count=1'
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
            if data.get('results'):
                return data['results'][0]['latitude'], \
                    data['results'][0]['longitude']
        except Exception:
            pass
        return None, None

    def get_current(self, location):
        lat, lon = self._geocode(location)
        if lat is None:
            return {'error': 'Location not found'}
        url = (f'{self.WEATHER_URL}?latitude={lat}&longitude={lon}'
               f'&current_weather=true')
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read())
        except Exception as e:
            return {'error': str(e)}

    def get_forecast(self, location, days=7):
        lat, lon = self._geocode(location)
        if lat is None:
            return {'error': 'Location not found'}
        url = (f'{self.WEATHER_URL}?latitude={lat}&longitude={lon}'
               f'&daily=temperature_2m_max,temperature_2m_min,'
               f'precipitation_sum&forecast_days={days}')
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read())
        except Exception as e:
            return {'error': str(e)}

    def get_alerts(self, region):
        return {'error': 'Weather alerts not available via free tier'}


def run(action, **kwargs):
    ws = WeatherService()
    method = getattr(ws, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
