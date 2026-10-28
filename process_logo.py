from PIL import Image

SRC = r"8a5bb98a-13e7-4903-bc98-6943410c3e53.jfif"
OUT = r"logo-gold.png"

im = Image.open(SRC).convert("RGBA")
w, h = im.size
px = im.load()

out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
gold_xs=[]; gold_ys=[]
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        is_white = r > 235 and g > 235 and b > 235
        is_green = g > r + 25 and g > b + 25
        is_gold = (r > 120 and (r - b) > 60 and g > 80 and not is_white and not is_green)
        if is_gold:
            out.putpixel((x, y), (r, g, b, 255))
            gold_xs.append(x); gold_ys.append(y)

minx, maxx = min(gold_xs), max(gold_xs)
miny, maxy = min(gold_ys), max(gold_ys)
cropped = out.crop((minx, miny, maxx + 1, maxy + 1))

target_h = 400
scale = target_h / cropped.height
new_w = int(cropped.width * scale)
enlarged = cropped.resize((new_w, target_h), Image.LANCZOS)
enlarged.save(OUT)
print("saved", OUT, enlarged.size)
