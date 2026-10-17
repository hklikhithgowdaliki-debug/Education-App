"""Generate the launcher icons and Play Store graphics."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BLUE, DARK, WHITE, GOLD = (21, 101, 192), (13, 71, 161), (255, 255, 255), (255, 193, 7)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def icon(size):
    img = Image.new("RGB", (size, size), BLUE)
    d = ImageDraw.Draw(img)
    s = size / 512
    d.rectangle([0, size * 0.72, size, size], fill=DARK)
    d.rounded_rectangle([140 * s, 70 * s, 372 * s, 370 * s], radius=18 * s, fill=WHITE)
    d.polygon([(312 * s, 70 * s), (372 * s, 130 * s), (312 * s, 130 * s)], fill=(200, 215, 235))
    for i, y in enumerate(range(165, 320, 36)):
        d.rounded_rectangle([175 * s, y * s, (337 if i % 2 else 300) * s, (y + 14) * s], radius=7 * s, fill=(160, 185, 220))
    d.rounded_rectangle([120 * s, 300 * s, 392 * s, 420 * s], radius=22 * s, fill=GOLD)
    f = ImageFont.truetype(BOLD, int(70 * s))
    d.text((256 * s, 360 * s), "QP", font=f, fill=DARK, anchor="mm")
    return img


def main():
    res = ROOT / "app" / "android" / "app" / "src" / "main" / "res"
    for name, px in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
        icon(512).resize((px, px), Image.LANCZOS).save(res / f"mipmap-{name}" / "ic_launcher.png")
    store = ROOT / "store"
    store.mkdir(exist_ok=True)
    icon(512).save(store / "icon-512.png")
    fg = Image.new("RGB", (1024, 500), BLUE)
    fg.paste(icon(300), (60, 100))
    d = ImageDraw.Draw(fg)
    d.text((400, 170), "KSEAB Papers", font=ImageFont.truetype(BOLD, 64), fill=WHITE)
    d.text((402, 260), "SSLC • 2nd PUC • VTU Engineering", font=ImageFont.truetype(BOLD, 30), fill=GOLD)
    d.text((402, 310), "Previous year question papers, offline", font=ImageFont.truetype(BOLD, 26), fill=WHITE)
    fg.save(store / "feature-graphic.png")


if __name__ == "__main__":
    main()
