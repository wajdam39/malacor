from PIL import Image
import os

SRC = r'c:\Users\wajda\.cline\data\workspaces\chat\malcor\8a5bb98a-13e7-4903-bc98-6943410c3e53.jfif'
OUT = r'c:\Users\wajda\.cline\data\workspaces\chat\malcor\logo-gold.png'

im = Image.open(SRC).convert('RGBA')
w, h = im.size
px = im.load()

# 1. Build gold mask: keep gold, drop white and green
mask = bytearray(w * h)
for y in range(h):
    for x in range(w):
        r, g, b, a = px[x, y]
        is_white = r > 235 and g > 235 and b > 235
        is_green = g > r + 10 and g > b + 10   # green dominates
        is_gold = (r > 150 and g > 110 and b < 135 and r >= g - 30
                   and not is_white and not is_green)
        if is_gold:
            mask[y * w + x] = 1

# 2. Connected components (4-connectivity)
visited = bytearray(w * h)
comps = []
for start in range(w * h):
    if mask[start] == 1 and visited[start] == 0:
        stack = [start]
        visited[start] = 1
        cnt = 0
        minx, miny, maxx, maxy = w, h, 0, 0
        while stack:
            idx = stack.pop()
            x = idx % w
            y = idx // w
            cnt += 1
            if x < minx: minx = x
            if x > maxx: maxx = x
            if y < miny: miny = y
            if y > maxy: maxy = y
            if x > 0:
                n = idx - 1
                if mask[n] and not visited[n]:
                    visited[n] = 1; stack.append(n)
            if x < w - 1:
                n = idx + 1
                if mask[n] and not visited[n]:
                    visited[n] = 1; stack.append(n)
            if y > 0:
                n = idx - w
                if mask[n] and not visited[n]:
                    visited[n] = 1; stack.append(n)
            if y < h - 1:
                n = idx + w
                if mask[n] and not visited[n]:
                    visited[n] = 1; stack.append(n)
        area = (maxx - minx + 1) * (maxy - miny + 1)
        density = cnt / area if area else 0
        comps.append((cnt, minx, miny, maxx, maxy, density))

# Keep dense gold components (the emblem), drop sparse noise + tiny specks
keep = [c for c in comps if c[0] >= 500 and c[5] >= 0.1]
print('kept components:', len(keep))
for c in keep:
    print('  size', c[0], 'bbox', c[1], c[2], c[3], c[4], 'density', round(c[5], 3))

if not keep:
    raise SystemExit('No gold components found')

minx = min(c[1] for c in keep)
miny = min(c[2] for c in keep)
maxx = max(c[3] for c in keep)
maxy = max(c[4] for c in keep)

# 3. Build transparent image keeping only kept components
keep_mask = bytearray(w * h)
# re-label to know which component each pixel belongs to
comp_id = [-1] * (w * h)
cid = 0
comp_meta = []
for start in range(w * h):
    if mask[start] == 1 and comp_id[start] == -1:
        stack = [start]
        comp_id[start] = cid
        cnt = 0
        minx2, miny2, maxx2, maxy2 = w, h, 0, 0
        while stack:
            idx = stack.pop()
            x = idx % w
            y = idx // w
            cnt += 1
            if x < minx2: minx2 = x
            if x > maxx2: maxx2 = x
            if y < miny2: miny2 = y
            if y > maxy2: maxy2 = y
            for n in (idx - 1, idx + 1, idx - w, idx + w):
                # bounds check
                pass
            # neighbors with bounds
            x = idx % w
            if x > 0:
                n = idx - 1
                if mask[n] and comp_id[n] == -1:
                    comp_id[n] = cid; stack.append(n)
            if x < w - 1:
                n = idx + 1
                if mask[n] and comp_id[n] == -1:
                    comp_id[n] = cid; stack.append(n)
            if idx >= w:
                n = idx - w
                if mask[n] and comp_id[n] == -1:
                    comp_id[n] = cid; stack.append(n)
            if idx < w * (h - 1):
                n = idx + w
                if mask[n] and comp_id[n] == -1:
                    comp_id[n] = cid; stack.append(n)
        area = (maxx2 - minx2 + 1) * (maxy2 - miny2 + 1)
        density = cnt / area if area else 0
        comp_meta.append((cid, cnt, minx2, miny2, maxx2, maxy2, density))
        cid += 1

keep_ids = {m[0] for m in comp_meta if m[1] >= 500 and m[6] >= 0.1}

out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
for y in range(h):
    for x in range(w):
        idx = y * w + x
        if mask[idx] == 1 and comp_id[idx] in keep_ids:
            r, g, b, a = px[x, y]
            out.putpixel((x, y), (r, g, b, 255))

# 4. Crop to bounding box
cropped = out.crop((minx, miny, maxx + 1, maxy + 1))
print('cropped size', cropped.size)

# 5. Enlarge to current logo size: scale so height = 400px (high-res), keep aspect
target_h = 400
scale = target_h / cropped.height
new_w = int(cropped.width * scale)
new_h = target_h
enlarged = cropped.resize((new_w, new_h), Image.LANCZOS)
enlarged.save(OUT)
print('saved', OUT, enlarged.size)
