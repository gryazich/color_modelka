def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def rgb_clip(r, g, b):
    warn = not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255)
    return clamp(round(r), 0, 255), clamp(round(g), 0, 255), clamp(round(b), 0, 255), warn

def rgb_to_cmyk(r, g, b):
    rn, gn, bn = r / 255, g / 255, b / 255
    k = 1 - max(rn, gn, bn)
    if k >= 1:
        return 0.0, 0.0, 0.0, 1.0, False
    c = (1 - rn - k) / (1 - k)
    m = (1 - gn - k) / (1 - k)
    y = (1 - bn - k) / (1 - k)
    return c, m, y, k, False

def cmyk_to_rgb(c, m, y, k):
    warn = not all(0 <= v <= 1 for v in (c, m, y, k))
    c, m, y, k = (clamp(v, 0, 1) for v in (c, m, y, k))
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    r, g, b, w2 = rgb_clip(r, g, b)
    return r, g, b, warn or w2

def rgb_to_hls(r, g, b):
    rn, gn, bn = r / 255, g / 255, b / 255
    mx, mn = max(rn, gn, bn), min(rn, gn, bn)
    l = (mx + mn) / 2
    if mx == mn:
        return 0.0, l, 0.0, False
    d = mx - mn
    s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
    if mx == rn:
        h = (gn - bn) / d + (6 if gn < bn else 0)
    elif mx == gn:
        h = (bn - rn) / d + 2
    else:
        h = (rn - gn) / d + 4
    h = (h / 6) % 1
    return h * 360, l, s, False

def hue(p, q, t):
    if t < 0: t += 1
    if t > 1: t -= 1
    if t < 1 / 6: return p + (q - p) * 6 * t
    if t < 1 / 2: return q
    if t < 2 / 3: return p + (q - p) * (2 / 3 - t) * 6
    return p

def hls_to_rgb(h, l, s):
    warn = not (0 <= h <= 360 and 0 <= l <= 1 and 0 <= s <= 1)
    h = clamp(h, 0, 360) / 360
    l = clamp(l, 0, 1)
    s = clamp(s, 0, 1)
    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue(p, q, h + 1 / 3)
        g = hue(p, q, h)
        b = hue(p, q, h - 1 / 3)
    r, g, b, w2 = rgb_clip(r * 255, g * 255, b * 255)
    return r, g, b, warn or w2
