import requests

# Ambient Weather API endpoint
AMBIENT_URL = "https://api.ambientweather.net/v1/devices"
AMBIENT_PARAMS = {
    "applicationKey": "40b33f6a63754b5fb70a4d5fe557c64efcdd693597924c21986b47e71e1e68eb",
    "apiKey": "c5cc20bfdc0446aaaddd4543eb04c64c4852dcd72d1f4d5d8c7f207c1d21036a"
}

# WeatherCloud API base URL
WEATHERCLOUD_BASE = "https://api.weathercloud.net/v01/set/wid/59bd237aa2bae7e1/key/e81026c3402660b317450a9dde943c6b"

def convert_temp(temp_f):
    """Convert temperature from Fahrenheit to Celsius × 10"""
    # °C = (°F - 32) × 5/9
    temp_c = (temp_f - 32) * 5 / 9
    return int(temp_c * 10)

def convert_speed(speed_mph):
    """Convert wind speed from mph to m/s × 10"""
    # 1 mph = 0.44704 m/s
    speed_ms = speed_mph * 0.44704
    return int(speed_ms * 10)

def convert_pressure(pressure_inhg):
    """Convert pressure from inHg to hPa × 10"""
    # 1 inHg = 33.8639 hPa
    hpa = pressure_inhg * 33.8639
    return int(hpa * 10)

def convert_rain(rain_in):
    """Convert rain from inches to mm × 10"""
    # 1 inch = 25.4 mm
    mm = rain_in * 25.4
    return int(mm * 10)

def convert_solarrad(solarrad):
    """Convert solar radiation to W/m² × 10"""
    return int(solarrad * 10)

def fetch_ambient_weather():
    """Fetch weather data from Ambient Weather API"""
    try:
        response = requests.get(AMBIENT_URL, params=AMBIENT_PARAMS)
        response.raise_for_status()
        data = response.json()
        return data[0]['lastData'] if data else None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Ambient Weather data: {e}")
        return None

def build_weathercloud_url(weather_data):
    """Build WeatherCloud API URL from Ambient Weather data"""
    url = (
        f"{WEATHERCLOUD_BASE}"
        f"/temp/{convert_temp(weather_data['tempf'])}"
        f"/tempin/{convert_temp(weather_data['tempinf'])}"
        f"/chill/{convert_temp(weather_data['feelsLike'])}"
        f"/heat/{convert_temp(weather_data['feelsLike'])}"
        f"/hum/{int(weather_data['humidity'])}"
        f"/humin/{int(weather_data['humidityin'])}"
        f"/wspd/{convert_speed(weather_data['windspeedmph'])}"
        f"/wspdhi/{convert_speed(weather_data['windgustmph'])}"
        f"/wspdavg/{convert_speed(weather_data['windspeedmph'])}"
        f"/wdir/{int(weather_data['winddir'])}"
        f"/wdiravg/{int(weather_data['winddir_avg10m'])}"
        f"/bar/{convert_pressure(weather_data['baromrelin'])}"
        f"/rain/{convert_rain(weather_data['dailyrainin'])}"
        f"/solarrad/{convert_solarrad(weather_data['solarradiation'])}"
        f"/uvi/{int(weather_data['uv'] * 10)}"
        f"/ver/1.2"
        f"/type/201"
    )
    
    return url

def main():
    print("Fetching weather data from Ambient Weather...")
    weather_data = fetch_ambient_weather()
    
    if not weather_data:
        print("Failed to fetch weather data.")
        return
    
    print("\nWeather Data Retrieved:")
    print(f"Temperature: {weather_data['tempf']}°F → {convert_temp(weather_data['tempf'])} (°C×10)")
    print(f"Indoor Temperature: {weather_data['tempinf']}°F → {convert_temp(weather_data['tempinf'])} (°C×10)")
    print(f"Feels Like: {weather_data['feelsLike']}°F → {convert_temp(weather_data['feelsLike'])} (°C×10)")
    print(f"Humidity: {weather_data['humidity']}%")
    print(f"Indoor Humidity: {weather_data['humidityin']}%")
    print(f"Wind Speed: {weather_data['windspeedmph']} mph → {convert_speed(weather_data['windspeedmph'])} (m/s×10)")
    print(f"Wind Gust: {weather_data['windgustmph']} mph → {convert_speed(weather_data['windgustmph'])} (m/s×10)")
    print(f"Wind Direction: {weather_data['winddir']}°")
    print(f"Wind Direction Avg: {weather_data['winddir_avg10m']}°")
    print(f"Pressure: {weather_data['baromrelin']} inHg → {convert_pressure(weather_data['baromrelin'])} (hPa×10)")
    print(f"Daily Rain: {weather_data['dailyrainin']} in → {convert_rain(weather_data['dailyrainin'])} (mm×10)")
    print(f"Solar Radiation: {weather_data['solarradiation']} W/m² → {convert_solarrad(weather_data['solarradiation'])} (W/m²×10)")
    print(f"UV Index: {weather_data['uv']} → {int(weather_data['uv'] * 10)} (index×10)")
    
    print("\nBuilding WeatherCloud URL...")
    weathercloud_url = build_weathercloud_url(weather_data)
    
    print(f"\nWeatherCloud URL:\n{weathercloud_url}")
    
    print("\nSending request to WeatherCloud...")
    try:
        response = requests.get(weathercloud_url)
        print(f"Response Status: {response.status_code}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            print("\n✓ Weather data successfully sent to WeatherCloud!")
        else:
            print(f"\n✗ Error: Received status code {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Error sending to WeatherCloud: {e}")
    
    print("Done! Script ran successfully.")

if __name__ == "__main__":
    main()
