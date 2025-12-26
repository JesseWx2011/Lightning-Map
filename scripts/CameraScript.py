import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io
import os

# Configuration
IMAGE_URL = "https://panhandlewx.altervista.org/wp-content/Latest.jpg"
API_URL = "https://api.ambientweather.net/v1/devices?applicationKey=40b33f6a63754b5fb70a4d5fe557c64efcdd693597924c21986b47e71e1e68eb&apiKey=c5cc20bfdc0446aaaddd4543eb04c64c4852dcd72d1f4d5d8c7f207c1d21036a"
SAVE_PATH = "./docs/latest_weather_stamped.jpg"

def draw_text_with_halo(draw, position, text, font, text_color="white", halo_color="black"):
    """Draws text with a thick outline for maximum visibility."""
    x, y = position
    # Draw halo/outline
    for adj in range(-2, 3):
        for bdy in range(-2, 3):
            draw.text((x + adj, y + bdy), text, font=font, fill=halo_color)
    # Draw main text
    draw.text(position, text, font=font, fill=text_color)

def main() -> None:
    # Ensure directory exists
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

    try:
        # 1. Fetch Temperature Data
        api_res = requests.get(API_URL, timeout=15)
        api_res.raise_for_status()
        weather_data = api_res.json()[0]['lastData']
        temp_string = f"{weather_data['tempf']}°F"

        # 2. Fetch the Image
        img_res = requests.get(IMAGE_URL, timeout=20)
        img_res.raise_for_status()
        img = Image.open(io.BytesIO(img_res.content)).convert("RGB")
        draw = ImageDraw.Draw(img)

        # 3. Font Setup (Handles Ubuntu/GitHub Actions environment)
        font_size = 35
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "arial.ttf"
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        if not font:
            font = ImageFont.load_default()

        # 4. Generate Timestamp and Overlay
        # Using 12-hour format with AM/PM for clarity
        timestamp = datetime.now().strftime("%b %d, %Y - %I:%M:%S %p")
        width, height = img.size

        # Top Left: Precise Timestamp
        draw_text_with_halo(draw, (20, 20), timestamp, font)
        
        # Bottom Left: Temperature from "Proverbs 3:5-6" Station
        draw_text_with_halo(draw, (20, height - 60), temp_string, font)

        # 5. Save locally (for GitHub Actions to pick up)
        img.save(SAVE_PATH, "JPEG", quality=90)
        print(f"Success: Stamped {timestamp} and {temp_string}")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()
