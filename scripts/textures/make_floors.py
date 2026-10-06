"""Self-authored, tileable floor texture sets (albedo / normal / roughness) for oak, stone and carpet.

Deterministic (fixed seeds), numpy + Pillow only. No third-party imagery.
Output: public/textures/{oak,stone,carpet}-{albedo,normal,rough}.jpg  (1024 x 1024, tileable)
Run:    python3 scripts/textures/make_floors.py [oak|stone|carpet ...]
Tile sizes (world meters per repeat) must match src/scene/lookdev/floorSurfaces.ts:
  oak 1.6 m, stone 1.2 m, carpet 0.5 m.

Normal-map encoding
-------------------
Floor.ts builds the tangent frame as T = world +X, B = world -Z and samples uv = worldXZ / tileSize.
With three.js' default flipY, image row 0 lands at v = 1 (largest Z), so moving DOWN the image is
moving toward -Z = +B. The green channel therefore has to store the normal component pointing toward
the bottom of the image ("green-down"). If Floor.ts ever switches B to world +Z, set GREEN_DOWN = False.

Roughness is stored as greyscale (read through .g) as 0..1 and remapped by roughMin..roughMax.
Heights are authored in millimetres so slopes are physical; normalStrength in floorSurfaces.ts is a
final artistic gain.
"""
import os
import sys
import numpy as np
from PIL import Image

N = 1024
GREEN_DOWN = True
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'public', 'textures')
os.makedirs(OUT, exist_ok=True)


# ----------------------------------------------------------------------------------------- helpers

def fnoise(rng, fx=8.0, fy=8.0, power=2.0, n=N):
    """Tileable filtered noise via FFT; fx/fy are characteristic frequencies (cycles per tile) along x/y."""
    F = np.fft.fft2(rng.standard_normal((n, n)))
    ky = np.fft.fftfreq(n)[:, None] * n
    kx = np.fft.fftfreq(n)[None, :] * n
    r = np.sqrt((kx / fx) ** 2 + (ky / fy) ** 2)
    filt = 1.0 / (1.0 + r ** power)
    filt[0, 0] = 0
    out = np.real(np.fft.ifft2(F * filt))
    out -= out.mean()
    return out / (out.std() + 1e-9)


def pconv(a, k):
    """Periodic convolution of a (n x n) with a small kernel k centred at k.shape//2."""
    n = a.shape[0]
    K = np.zeros((n, n))
    kh, kw = k.shape
    K[:kh, :kw] = k
    K = np.roll(K, (-(kh // 2), -(kw // 2)), (0, 1))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * np.fft.fft2(K)))


def down2(a):
    return 0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def blur(a, r=1):
    out = a.copy()
    for _ in range(r):
        out = (out + np.roll(out, 1, 0) + np.roll(out, -1, 0) + np.roll(out, 1, 1) + np.roll(out, -1, 1)) / 5
    return out


def normal_map(h_mm, px_mm, sx=0.0, sy=0.0):
    """h in millimetres, px_mm = pixel size in millimetres, sx/sy extra slopes (dh/dx, dh/dy down).
    Returns uint8 RGB (see GREEN_DOWN)."""
    dhdx = (np.roll(h_mm, -1, 1) - np.roll(h_mm, 1, 1)) / (2 * px_mm) + sx  # toward image-right
    dhdy = (np.roll(h_mm, -1, 0) - np.roll(h_mm, 1, 0)) / (2 * px_mm) + sy  # toward image-down
    nx = -dhdx
    n_down = -dhdy
    ny = n_down if GREEN_DOWN else -n_down
    n = np.stack([nx, ny, np.ones_like(h_mm)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.round((n * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)


def to8(a):
    return np.round(np.clip(a, 0, 255)).astype(np.uint8)


def save(kind, alb, nrm, rough, q_alb=84, q_nrm=86, q_rgh=80, rough_size=N):
    p = lambda s: os.path.join(OUT, f'{kind}-{s}.jpg')
    Image.fromarray(to8(alb)).save(p('albedo'), quality=q_alb, optimize=True, progressive=True)
    # 4:4:4 keeps the X/Y slopes from bleeding into each other through chroma subsampling
    Image.fromarray(nrm).save(p('normal'), quality=q_nrm, optimize=True, progressive=True, subsampling=0)
    r = Image.fromarray(to8(rough * 255))
    if rough_size != N:
        r = r.resize((rough_size, rough_size), Image.LANCZOS)
    r.save(p('rough'), quality=q_rgh, optimize=True, progressive=True)


# ----------------------------------------------------------------------------------------- oak

def oak():
    """Light Scandinavian oak, 200 mm boards, matte lacquer. Rendered at 2x and box-filtered down."""
    rng = np.random.default_rng(11)
    S = 2 * N
    px = 1600.0 / S  # mm per (supersampled) pixel
    rows = 8
    rh = S // rows  # 200 mm
    X = np.arange(S, dtype=float)[None, :]
    W = (np.arange(rh, dtype=float)[:, None] + 0.5) * px  # across-board coordinate, mm

    # Tile-periodic fields shared by all boards (each board reads a different strip of them)
    warp_lo = fnoise(rng, 3, 10, 2.2, S)  # slow ring wander
    warp_hi = fnoise(rng, 8, 30, 2.4, S)  # small ring wobble
    streak = fnoise(rng, 2, 50, 2.0, S)  # long colour streaks along the grain
    blotch = fnoise(rng, 5, 10, 2.0, S)
    pores = fnoise(rng, 110, 700, 1.6, S)  # short dashes elongated along the board
    flecks = fnoise(rng, 70, 420, 1.8, S)  # medullary ray flakes (rift boards)
    dashes = fnoise(rng, 260, 900, 1.6, S)  # tiny ray dashes (flat boards)
    lacq = fnoise(rng, 6, 6, 2.0, S)

    alb = np.zeros((S, S, 3))
    hgt = np.zeros((S, S))
    rgh = np.zeros((S, S))
    slx = np.zeros((S, S))
    sly = np.zeros((S, S))

    base = np.array([220, 191, 152], float)  # sRGB, light oak under matte clear lacquer
    early = np.array([0.83, 0.76, 0.67])  # earlywood (pore band) tint multiplier

    for r in range(rows):
        ys = slice(r * rh, (r + 1) * rh)
        if rng.random() < 0.5:
            lengths = [float(S)]
        else:
            a = rng.uniform(0.38, 0.62) * S
            lengths = [a, S - a]
        start = rng.uniform(0, S)
        for L in lengths:
            t = (X - start) % S  # along-board pixel coordinate, continuous across the tile wrap
            inb = (t < L)[0]
            tm = t * px  # mm
            Lmm = L * px
            sp = rng.uniform(3.6, 6.0)  # growth-ring spacing (mm)
            wl = warp_lo[ys] * rng.uniform(4, 9)
            wh = warp_hi[ys] * rng.uniform(0.15, 0.35)
            flat = rng.random() < 0.64
            if flat:
                # flat-sawn: the face cuts the rings at a slight tilt -> cathedral arches
                yc = rng.uniform(-30, 230)
                z0 = rng.uniform(45, 150)
                tilt = rng.choice([-1, 1]) * rng.uniform(0.015, 0.04)
                bend = rng.normal(0, 2.5e-5)
                c = tm - Lmm / 2
                dz = np.maximum(z0 + tilt * c + bend * c * c, 4.0)
                dy = W - yc + wl
                ring = (np.sqrt(dy * dy + dz * dz) + wh) / sp
            else:
                # rift / quarter-sawn: straight-ish wandering lines plus ray flecks
                ang = rng.normal(0, 0.006)
                ring = (W + tm * ang + wl * 1.6 + wh) / (sp * rng.uniform(0.7, 1.0))
            f = ring % 1.0
            e = sstep(0.0, 0.03, f) * np.exp(-f / 0.2)  # earlywood: abrupt start, soft decay
            late = sstep(0.55, 1.0, f)

            tone = np.clip(rng.normal(0, 0.032), -0.06, 0.06)
            warm = np.clip(rng.normal(0.003, 0.01), -0.014, 0.018)
            cup = rng.normal(0, 0.004, 2)  # boards are never perfectly coplanar
            v = 1 + tone + streak[ys] * 0.022 + blotch[ys] * 0.014 - late * 0.025
            pore = np.clip(pores[ys] - 1.0, 0, None) * (0.15 + 1.6 * e)
            if flat:
                ray_l = 0 * f
                ray_d = np.clip(dashes[ys] - 2.7, 0, None) * 1.5
            else:
                ray_l = np.clip(flecks[ys] - 1.8, 0, None) * rng.uniform(0.9, 1.6)
                ray_d = 0 * f
            v = v + ray_l * 0.10 - ray_d * 0.10 - pore * 0.12

            col = base[None, None, :] * v[..., None]
            ek = np.clip(e * rng.uniform(0.75, 1.05), 0, 1)[..., None]
            col = col * (1 - ek + ek * early[None, None, :])
            col[..., 0] *= 1 + warm
            col[..., 2] *= 1 - 1.8 * warm

            # board edges: 2.4 mm micro-bevel each side, 0.3 mm dark gap at the joint
            d = np.minimum(np.minimum(W, rh * px - W), np.minimum(tm + 0.5 * px, Lmm - tm - 0.5 * px))
            bev = 1 - sstep(0.0, 2.4, d)
            gap = 1 - sstep(0.15, 0.55, d)
            col *= (1 - 0.10 * bev - 0.45 * gap)[..., None]
            h = -0.9 * bev ** 1.4 - 0.4 * gap - 0.05 * e - 0.08 * np.clip(pore, 0, 1.5)
            g = 0.32 + 0.10 * e + 0.05 * lacq[ys] + 0.35 * np.clip(pore, 0, 1) + 0.25 * bev + 0.4 * gap - 0.18 * np.clip(ray_l, 0, 1)

            m = np.broadcast_to(inb[None, :], (rh, S))
            alb[ys][m] = col[m]
            hgt[ys][m] = h[m]
            rgh[ys][m] = g[m]
            slx[ys][m] = cup[0]
            sly[ys][m] = cup[1]
            start += L

    alb = np.stack([down2(alb[..., i]) for i in range(3)], -1)
    hgt = down2(hgt)
    rgh = down2(rgh)
    nrm = normal_map(hgt, 1600.0 / N, down2(slx), down2(sly))
    save('oak', alb, nrm, np.clip(rgh, 0, 1), q_alb=86, q_nrm=84, q_rgh=78)


# ----------------------------------------------------------------------------------------- stone

def stone():
    """Honed neutral limestone, 600 mm rectified tiles, 2 mm grout. Each tile reads its own patch."""
    rng = np.random.default_rng(23)
    S = N
    px = 1200.0 / S
    tiles = 2
    tw = S // tiles
    yy, xx = np.mgrid[0:S, 0:S].astype(float)

    fields = dict(
        cloud=fnoise(rng, 2.2, 2.2, 2.2),
        bed=fnoise(rng, 1.3, 7.0, 2.2),  # sedimentary bedding, anisotropic
        mid=fnoise(rng, 14, 14, 2.0),
        fine=fnoise(rng, 300, 300, 1.0),
        shell=fnoise(rng, 80, 80, 1.7),
        calc=fnoise(rng, 120, 120, 1.7),
        vein=fnoise(rng, 3.0, 3.0, 2.6),
        vwarp=fnoise(rng, 10, 10, 2.0),
        hue=fnoise(rng, 4, 4, 2.0),
    )
    pits_r = rng.random((S, S))

    out = {k: np.zeros((S, S)) for k in fields}
    tone = np.zeros((S, S))
    warm = np.zeros((S, S))
    vein_on = np.zeros((S, S))
    for ty in range(tiles):
        for tx in range(tiles):
            sl = (slice(ty * tw, (ty + 1) * tw), slice(tx * tw, (tx + 1) * tw))
            oy, ox = rng.integers(0, S, 2)
            rot = (ty + tx) % 2 == 1  # alternate bedding direction like a real lay
            for k, f in fields.items():
                g = np.roll(f, (oy, ox), (0, 1))
                if rot:
                    g = g.T
                out[k][sl] = g[: tw, : tw]
            tone[sl] = rng.normal(0, 0.012)
            warm[sl] = rng.normal(0.004, 0.005)
            vein_on[sl] = rng.uniform(0.3, 1.0)

    # mineral body
    v = 1 + tone + out['cloud'] * 0.013 + out['bed'] * 0.014 + out['mid'] * 0.012 + out['fine'] * 0.028
    shell = np.clip(out['shell'] - 2.0, 0, None)
    calc = np.clip(out['calc'] - 2.5, 0, None)
    vw = np.abs(out['vein'] + 0.35 * out['vwarp'])
    vein = (1 - sstep(0.0, 0.06, vw)) * vein_on
    pits = blur((pits_r < 0.0009).astype(float), 1) * 4
    v = v - shell * 0.09 + calc * 0.10 - vein * 0.07 - pits * 0.12

    base = np.array([207, 203, 195], float)
    alb = base[None, None, :] * v[..., None]
    w = warm + out['hue'] * 0.004
    alb[..., 0] *= 1 + w
    alb[..., 2] *= 1 - 1.5 * w
    # shell fragments slightly warmer/browner
    alb[..., 2] *= 1 - shell * 0.04

    # grout + tile edge
    lx = (xx % tw) + 0.5
    ly = (yy % tw) + 0.5
    d = np.minimum(np.minimum(lx, tw - lx), np.minimum(ly, tw - ly)) * px  # mm from tile edge line
    grout = 1 - sstep(0.7, 1.3, d)
    edge = 1 - sstep(1.0, 2.6, d)
    gcol = np.array([176, 172, 165], float) * (1 + out['fine'][..., None] * 0.03)
    alb = alb * (1 - edge * 0.05)[..., None]
    alb = alb * (1 - grout[..., None]) + gcol * grout[..., None]

    h = -1.2 * grout - 0.35 * edge ** 2 + out['fine'] * 0.012 + out['mid'] * 0.02 - pits * 0.12 - shell * 0.03
    nrm = normal_map(h, px)
    rgh = 0.42 + out['mid'] * 0.04 + out['fine'] * 0.04 + shell * 0.15 - calc * 0.2 + pits * 0.3 + grout * 0.5
    save('stone', alb, nrm, np.clip(rgh, 0, 1), q_alb=84, q_nrm=82, q_rgh=74)


# ----------------------------------------------------------------------------------------- carpet

def carpet():
    """Chunky ribbed woven rug (like the user's frames 1664-1667): oatmeal/cream yarn in raised horizontal ribs
    (~8 mm pitch) built from twisted loops (~5 mm), with heathered yarn tones and deep grooves between ribs so the
    structure reads at the ~1.3 m play-camera distance. 0.5 m tile, tileable (all periods divide the tile)."""
    rng = np.random.default_rng(37)
    S = N
    y, x = np.mgrid[0:S, 0:S].astype(float)
    rib_n = 62            # ribs per 0.5 m tile -> 8.1 mm pitch
    loop_n = 100          # loops per rib along x -> 5 mm
    ry = S / rib_n
    # gentle hand-woven waviness of the rib lines (tileable: integer cycles)
    wav = 0.9 * np.sin(2 * np.pi * x / S * 3 + 0.7) + 0.5 * np.sin(2 * np.pi * x / S * 7 + 2.1)
    v = ((y + wav) / ry) % 1.0                      # 0..1 across one rib
    rib_idx = np.floor((y + wav) / ry).astype(int) % rib_n
    # rib cross-section: rounded hump with a narrow deep groove between ribs
    hump = np.clip(np.sin(np.pi * v), 0, 1) ** 0.6
    # twisted loops along the rib, alternating phase per rib (woven look)
    phase = (rib_idx % 2) * 0.5
    u = (x / (S / loop_n) + phase) % 1.0
    twist = 0.5 + 0.5 * np.cos(2 * np.pi * (u - 0.35 * v))  # slanted ply highlights
    loops = 0.55 + 0.45 * np.clip(np.sin(np.pi * u), 0, 1) ** 0.8
    fuzz = fnoise(rng, fx=300, fy=300, power=1.2) * 0.08
    height = hump * (0.75 + 0.25 * loops) + 0.12 * twist * hump + fuzz
    # yarn colour: oatmeal/cream heather with per-rib and per-ply variation
    base = np.array([214, 206, 192], float)
    rib_tone = rng.normal(0, 0.025, rib_n)[rib_idx]
    heather = fnoise(rng, fx=120, fy=40, power=1.3) * 0.035
    fleck = (rng.random((S, S)) < 0.012).astype(float)
    shade = 0.70 + 0.30 * hump                        # grooves darker (occlusion baked lightly)
    ply = 0.94 + 0.08 * twist
    val = shade * ply * (1 + rib_tone + heather)
    alb = base[None, None, :] * val[..., None]
    alb = alb * (1 - 0.18 * fleck[..., None]) + np.array([150, 140, 126])[None, None, :] * 0.18 * fleck[..., None]
    nrm = normal_map(height * 2.6, 500.0 / S)   # ~2.6 mm rib relief
    rough = np.clip(0.88 + 0.08 * (1 - hump), 0, 1)
    save('carpet', alb, nrm, rough, rough_size=512)


if __name__ == '__main__':
    which = sys.argv[1:] or ['oak', 'stone', 'carpet']
    for k in which:
        globals()[k]()
    tot = 0
    for f in sorted(os.listdir(OUT)):
        s = os.path.getsize(os.path.join(OUT, f))
        tot += s
        print(f'{f:22s} {s // 1024:5d} KB')
    print(f'{"total":22s} {tot // 1024:5d} KB')
