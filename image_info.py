import csv
import os
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor

EXT = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.gif': 'GIF', '.tif': 'TIFF', '.tiff': 'TIFF',
       '.bmp': 'BMP', '.png': 'PNG', '.pcx': 'PCX'}
CH = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
BC = {0: 'BI_RGB', 1: 'BI_RLE8', 2: 'BI_RLE4', 3: 'BI_BITFIELDS', 4: 'BI_JPEG', 5: 'BI_PNG'}
TC = {1: 'None', 2: 'CCITT RLE', 3: 'CCITT G3', 4: 'CCITT G4', 5: 'LZW', 6: 'JPEG old',
      7: 'JPEG', 8: 'Deflate', 32773: 'PackBits', 32946: 'Deflate'}
SZ = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8}
TF = {1: 'B', 2: 'B', 3: 'H', 4: 'I', 5: 'II', 6: 'b', 7: 'B', 8: 'h', 9: 'i', 10: 'ii'}
SOF = {0xc0: 'Baseline', 0xc1: 'Extended', 0xc2: 'Progressive', 0xc3: 'Lossless'}
HEAD = ('Файл', 'Формат', 'Размер, px', 'DPI', 'Бит', 'Сжатие', 'Доп.', 'Статус')
F = '{:<34}{:<8}{:<14}{:<12}{:<6}{:<14}{:<28}{}'
IEND = b'\x00\x00\x00\x00IEND\xaeB`\x82'


class Bad(Exception):
    pass


def rd(f, n):
    d = f.read(n)
    if len(d) < n:
        raise Bad
    return d


def dpi(x, y):
    return '{:g}x{:g}'.format(round(x, 1), round(y, 1)) if x and y else '-'


def png(f, sz):
    d = rd(f, 33)
    if d[12:16] != b'IHDR':
        raise Bad
    w, h, bd, ct, cm, fl, il = struct.unpack('>IIBBBBB', d[16:29])
    if ct not in CH:
        raise Bad
    f.seek(sz - 12)
    if rd(f, 12) != IEND:
        raise Bad
    dp = '-'
    pos = 33
    while pos + 12 <= sz:
        f.seek(pos)
        n, t = struct.unpack('>I4s', rd(f, 8))
        if pos + 12 + n > sz:
            raise Bad
        if t == b'pHYs':
            x, y, u = struct.unpack('>IIB', rd(f, 9))
            if u == 1:
                dp = dpi(x * 0.0254, y * 0.0254)
        if t in (b'IDAT', b'IEND'):
            break
        pos += 12 + n
    else:
        raise Bad
    return w, h, dp, bd * CH[ct], 'Deflate' if cm == 0 else str(cm), 'filter {}, interlace {}'.format(fl, il)


def res(t):
    u = t.get(296, (2,))[0]
    x, y = t.get(282), t.get(283)
    if u not in (2, 3) or not x or not y or not x[1] or not y[1]:
        return '-'
    k = 1 if u == 2 else 2.54
    return dpi(x[0] / x[1] * k, y[0] / y[1] * k)


def tags(f, base):
    f.seek(base)
    h = rd(f, 8)
    bo = {b'II': '<', b'MM': '>'}.get(h[:2])
    if not bo or struct.unpack(bo + 'H', h[2:4])[0] != 42:
        raise Bad
    f.seek(base + struct.unpack(bo + 'I', h[4:])[0])
    n = struct.unpack(bo + 'H', rd(f, 2))[0]
    e = rd(f, 12 * n)
    t = {}
    for i in range(n):
        tg, ty, c = struct.unpack(bo + 'HHI', e[i * 12:i * 12 + 8])
        raw = e[i * 12 + 8:i * 12 + 12]
        if ty not in SZ or SZ[ty] * c > 1 << 22:
            continue
        k = SZ[ty] * c
        if k <= 4:
            d = raw[:k]
        else:
            f.seek(base + struct.unpack(bo + 'I', raw)[0])
            d = rd(f, k)
        t[tg] = struct.unpack(bo + TF[ty] * c, d)
    return bo, t


def jpg(f, sz):
    f.seek(max(sz - 64, 0))
    if not f.read().rstrip(b'\x00').endswith(b'\xff\xd9'):
        raise Bad
    f.seek(2)
    jf = xf = None
    while True:
        if rd(f, 1) != b'\xff':
            raise Bad
        m = rd(f, 1)[0]
        while m == 0xff:
            m = rd(f, 1)[0]
        if m in (0xd9, 0xda):
            raise Bad
        if m == 1 or 0xd0 <= m <= 0xd8:
            continue
        n = struct.unpack('>H', rd(f, 2))[0] - 2
        if n < 0:
            raise Bad
        q = f.tell()
        if m == 0xe0:
            d = f.read(n)
            if d[:5] == b'JFIF\x00' and len(d) >= 12:
                u, x, y = struct.unpack('>BHH', d[7:12])
                if u in (1, 2):
                    k = 1 if u == 1 else 2.54
                    jf = dpi(x * k, y * k)
        elif m == 0xe1 and n > 14 and rd(f, 6) == b'Exif\x00\x00':
            try:
                xf = res(tags(f, f.tell())[1])
            except Exception:
                pass
        elif 0xc0 <= m <= 0xcf and m not in (0xc4, 0xc8, 0xcc):
            p, h, w, c = struct.unpack('>BHHB', rd(f, 6))
            return w, h, jf or xf or '-', p * c, 'JPEG (DCT)', SOF.get(m, 'Other')
        f.seek(q + n)


def gif(f, sz):
    d = rd(f, 13)
    w, h, p = struct.unpack('<HHB', d[6:11])
    f.seek(sz - 1)
    if rd(f, 1) != b';':
        raise Bad
    if p & 0x80:
        n = (p & 7) + 1
        return w, h, '-', n, 'LZW', 'палитра {} цв.'.format(1 << n)
    return w, h, '-', '-', 'LZW', 'нет глобальной палитры'


def bmp(f, sz):
    d = rd(f, 26)
    fs, off = struct.unpack('<I4xI', d[2:14])
    hs = struct.unpack('<I', d[14:18])[0]
    if hs == 12:
        w, h, pl, bits = struct.unpack('<HHHH', d[18:26])
        c, dp, cl = 0, '-', 0
    elif hs >= 40:
        d += rd(f, 28)
        w, h, pl, bits, c, isz, xp, yp, cl = struct.unpack('<iiHHIIiiI', d[18:50])
        dp = dpi(xp * 0.0254, yp * 0.0254)
    else:
        raise Bad
    w, h = abs(w), abs(h)
    if (fs and fs > sz) or off >= sz or not w or not h:
        raise Bad
    if c == 0 and off + (w * bits + 31) // 32 * 4 * h > sz:
        raise Bad
    ex = 'палитра {} цв.'.format(cl or 1 << bits) if bits <= 8 else 'без палитры'
    return w, h, dp, bits, BC.get(c, str(c)), ex


def pcx(f, sz):
    d = rd(f, 128)
    ver, enc, bp, pl = d[1], d[2], d[3], d[65]
    x0, y0, x1, y1, hx, hy = struct.unpack('<6H', d[4:16])
    if x1 < x0 or y1 < y0 or not pl:
        raise Bad
    bits = bp * pl
    if bits == 8 and ver == 5:
        if sz < 897:
            raise Bad
        f.seek(sz - 769)
        if rd(f, 1) != b'\x0c':
            raise Bad
    return x1 - x0 + 1, y1 - y0 + 1, dpi(hx, hy), bits, 'RLE' if enc == 1 else 'None', 'версия {}'.format(ver)


def tif(f, sz):
    bo, t = tags(f, 0)
    w, h = t[256][0], t[257][0]
    c = t.get(259, (1,))[0]
    for a, b in ((273, 279), (324, 325)):
        if t.get(a) and t.get(b) and max(o + n for o, n in zip(t[a], t[b])) > sz:
            raise Bad
    ex = '{} photo={}'.format('LE' if bo == '<' else 'BE', t.get(262, (-1,))[0])
    return w, h, res(t), sum(t.get(258, (1,))), TC.get(c, str(c)), ex


P = {'PNG': png, 'JPEG': jpg, 'GIF': gif, 'BMP': bmp, 'TIFF': tif, 'PCX': pcx}


def kind(h):
    if h[:8] == b'\x89PNG\r\n\x1a\n':
        return 'PNG'
    if h[:2] == b'\xff\xd8':
        return 'JPEG'
    if h[:6] in (b'GIF87a', b'GIF89a'):
        return 'GIF'
    if h[:2] == b'BM':
        return 'BMP'
    if h[:4] in (b'II*\x00', b'MM\x00*'):
        return 'TIFF'
    if len(h) > 2 and h[0] == 10 and h[1] in (0, 2, 3, 4, 5) and h[2] == 1:
        return 'PCX'


def work(e):
    ex = EXT[os.path.splitext(e.name)[1].lower()]
    try:
        with open(e.path, 'rb') as f:
            k = kind(f.read(8))
            if not k:
                raise Bad
            f.seek(0)
            r = P[k](f, os.fstat(f.fileno()).st_size)
        s = 'OK' if k == ex else 'OK, расширение не совпадает с форматом'
        return (e.name, k, '{}x{}'.format(r[0], r[1]), r[2], str(r[3]), r[4], r[5], s)
    except Exception:
        return (e.name, '-', '-', '-', '-', '-', '-', 'Файл повреждён')


def bar(i, n):
    k = 30 * i // n
    sys.stderr.write('\r[{}{}] {}/{}'.format('#' * k, '.' * (30 - k), i, n))
    sys.stderr.flush()


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else input('Папка: ').strip('"')
    out = sys.argv[2] if len(sys.argv) > 2 else None
    fs = [e for e in os.scandir(d) if e.is_file() and os.path.splitext(e.name)[1].lower() in EXT]
    n = len(fs)
    rows = []
    t = time.time()
    with ThreadPoolExecutor(32) as ex:
        for i, r in enumerate(ex.map(work, fs), 1):
            rows.append(r)
            if i % 50 == 0 or i == n:
                bar(i, n)
    sys.stderr.write('\nВремя: {:.2f} с\n'.format(time.time() - t))
    if out:
        with open(out, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f, delimiter=';')
            w.writerow(HEAD)
            w.writerows(rows)
    else:
        print(F.format(*HEAD))
        for r in rows:
            print(F.format(r[0][:32], *r[1:]))
    print('Файлов:', n, '| повреждённых:', sum(r[7] == 'Файл повреждён' for r in rows))


main()
