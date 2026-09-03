"""Create a small scanned-style image for testing the OCR upload path."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "sample" / "scanned_demo.png"

LINES = [
    "SYNTHETIC OCR DEMO",
    "Product Name: Wattle Life Essentials",
    "Provider: Wattle Life (Fictitious)",
    "Cover Types: Life Cover",
    "Entry Age: 18 to 65",
    "Expiry Age: 90",
    "Sum Insured: AUD $50,000 to AUD $1,500,000",
    "Waiting Period: 0 days",
    "Benefit Period: Lump-sum benefit",
    "Premium Structure: Stepped premiums",
    "Key Exclusions: Fraudulent claim; recorded exclusions",
]

image = Image.new("RGB", (1600, 1000), "white")
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("DejaVuSans.ttf", 35)
for index, line in enumerate(LINES):
    draw.text((90, 70 + index * 75), line, fill=(20, 25, 30), font=font)
image.save(OUTPUT, quality=95)
print(OUTPUT)
