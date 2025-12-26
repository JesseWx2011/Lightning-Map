import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os

# Configuration
IMAGE_URL = "https://panhandlewx.altervista.org/wp-content/Latest.jpg"
API_URL = "https://api.ambientweather.net/v1/devices?applicationKey=40b33f6a63754b5fb70a4d5fe557c64efcdd693597924c21986b47e71e1e68eb&apiKey=c5cc20bfdc0446aaaddd4543eb04c64c4852dcd72d1f4d5d8c7f207c1d21036a"
SAVE_PATH = "./docs/latest_weather_stamped.jpg"

def main():
    # Ensure directory exists
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    try:
        # 1. Fetch Temperature Data
        response = requests.get(API_URL)
        data = response.json()
        # Based on the JSON structure provided: first device -> lastData -> tempf
        temp_f = data[0]['lastData']['tempf']
        weather_text = f"Temp: {temp_f}°F"

        # 2. Fetch the Image
        img_response = requests.get(IMAGE_URL)
        img = Image.open(io.BytesIO(img_response.content))
        draw = ImageDraw.Draw(img)

        # 3. Define Fonts and Content
        # Using default font if custom font isn't available
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 4. Add Text to Image
        # Bottom Left: Temperature
        width, height = img.size
        draw.text((20, height - 40), weather_text, fill="white", font=font, stroke_width=2, stroke_fill="black")
        
        # Top Left: Timestamp
        draw.text((20, 20), timestamp, fill="white", font=font, stroke_width=2, stroke_fill="black")

        # 5. Save the image
        img.save(SAVE_PATH)
        print(f"Successfully saved stamped image to {SAVE_PATH}")
        print(f"Recorded Temperature: {temp_f}°F")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
