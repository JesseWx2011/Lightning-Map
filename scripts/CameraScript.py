import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os
import time

# Configuration
# Added a timestamp parameter to the URL to bypass any server-side caching
IMAGE_URL = f"https://panhandlewx.altervista.org/wp-content/Latest.jpg?v={int(time.time())}"
API_URL = "https://api.ambientweather.net/v1/devices?applicationKey=40b33f6a63754b5fb70a4d5fe557c64efcdd693597924c21986b47e71e1e68eb&apiKey=c5cc20bfdc0446aaaddd4543eb04c64c4852dcd72d1f4d5d8c7f207c1d21036a"
SAVE_PATH = "./docs/latest_weather_stamped.jpg"

def draw_text_with_halo(draw, position, text, font, text_color="white", halo_color="black"):
    x, y = position
    for adj in range(-2, 3):
        for bdy in range(-2, 3):
            draw.text((x + adj, y + bdy), text, font=font, fill=halo_color)
    draw.text(position, text, font=font, fill=text_color)

def main() -> None:
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    try:
        # 1. Fetch Temperature Data
        api_res = requests.get(API_URL, timeout=15)
        api_res.raise_for_status()
        weather_data = api_res.json()[0]['lastData']
        temp_string = f"Temp: {weather_data['tempf']}°F"

        # 2. Fetch the Image with Cache Busting
        img_res = requests.get(IMAGE_URL, timeout=20, headers={'Cache-Control': 'no-cache'})
        img_res.raise_for_status()
        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
        draw = ImageDraw.Draw(img)

        # 3. Font Setup
        font_size = 30
        font_paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "arial.ttf"]
        font = next((ImageFont.truetype(p, font_size) for p in font_paths if os.path.exists(p)), ImageFont.load_default())

        # 4. Content and Positioning
        # This timestamp proves when the SCRIPT ran
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        width, height = img.size

        # Overlay Script Timestamp (Top Left)
        draw_text_with_halo(draw, (20, 20), f"Processed: {timestamp}", font)
        
        # Overlay Temperature (Bottom Left)
        draw_text_with_halo(draw, (20, height - 50), temp_string, font)

        # 5. Save
        img.save(SAVE_PATH, "JPEG", quality=95)
        print(f"Update Successful: {timestamp} | {temp_string}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
