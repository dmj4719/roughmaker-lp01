# -*- coding: utf-8 -*-
"""白背景イラストを透過PNG化して assets/illust/ に書き出す（python3 make-illust.py）。ネットワーク通信なし・ローカル処理のみ。

・外周から繋がった白だけを背景とみなす（シャツ・書類・ホワイトボード等の内側の白は残す）
・境界のアンチエイリアス部は「白との混色」とみなしてアルファを逆算し、白フチを出さない
"""
import os
import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.expanduser("~/Downloads")   # 元イラストの置き場
DST = os.path.join(BASE, "assets", "illust")
os.makedirs(DST, exist_ok=True)

# 元ファイル名 -> 出力名（用途がわかる名前に）
MAP = {
    "ChatGPT Image 2026年9月14日 20_29_27 (3).png": "growth.png",    # 実績：右肩上がり
    "ChatGPT Image 2026年9月14日 20_25_54 (2).png": "worry.png",     # お悩み：？を浮かべる
    "ChatGPT Image 2026年9月14日 20_25_54 (3).png": "matching.png",  # Wの答え：決裁者を繋ぐ
    "ChatGPT Image 2026年9月14日 20_29_26 (1).png": "hearing.png",   # サービス概要：ヒアリング
    "ChatGPT Image 2026年9月14日 20_29_26 (2).png": "meeting.png",   # 3つの理由：説明・商談
    "ChatGPT Image 2026年9月14日 20_29_28 (4).png": "banso.png",     # 保証内容：伴走
    "ChatGPT Image 2026年9月14日 20_25_55 (4).png": "guide.png",     # 対象商材：案内
    "ChatGPT Image 2026年9月14日 20_25_54 (1).png": "handshake.png", # CTA：握手
}

TARGET_W = 900      # 表示は最大450px想定なので2倍解像度
MIN_CH   = 246      # これ以上明るく
SAT_MAX  = 8        # かつ彩度が低ければ背景候補


def outer_fill(mask):
    """外周に繋がっている mask 領域だけ True を返す（走査線フラッドフィル）。"""
    h, w = mask.shape
    seen = np.zeros_like(mask)
    gaps = [None] * h                       # 行ごとの「背景でない位置」をキャッシュ
    stack = []

    def push(y, x):
        if 0 <= y < h and mask[y, x] and not seen[y, x]:
            stack.append((y, x))

    for x in range(w):
        push(0, x); push(h - 1, x)
    for y in range(h):
        push(y, 0); push(y, w - 1)

    while stack:
        y, x = stack.pop()
        if seen[y, x] or not mask[y, x]:
            continue
        if gaps[y] is None:
            gaps[y] = np.flatnonzero(~mask[y])
        g = gaps[y]
        i = np.searchsorted(g, x)
        x1 = int(g[i - 1]) + 1 if i > 0 else 0          # 連続する背景ランの左端
        x2 = int(g[i]) - 1 if i < g.size else w - 1     # 同・右端
        seen[y, x1:x2 + 1] = True

        for ny in (y - 1, y + 1):                       # 上下の行へ伝播
            if not (0 <= ny < h):
                continue
            run = mask[ny, x1:x2 + 1] & ~seen[ny, x1:x2 + 1]
            idx = np.flatnonzero(run)
            if idx.size == 0:
                continue
            starts = np.concatenate(([idx[0]], idx[np.flatnonzero(np.diff(idx) > 1) + 1]))
            for s in starts:
                stack.append((ny, x1 + int(s)))
    return seen


def bleed(rgb, known_in, rounds=6):
    """未知領域のRGBを既知側の色で埋める（縮小時の白フチ防止・境界色の推定）。"""
    rgb = rgb.astype(np.float32).copy()
    known = known_in.copy()
    for _ in range(rounds):
        acc = np.zeros_like(rgb)
        cnt = np.zeros(known.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            acc += np.roll(rgb, (dy, dx), (0, 1)) * np.roll(known, (dy, dx), (0, 1)).astype(np.float32)[..., None]
            cnt += np.roll(known, (dy, dx), (0, 1)).astype(np.float32)
        fill = (~known) & (cnt > 0)
        rgb[fill] = acc[fill] / cnt[fill][..., None]
        known |= fill
        if known.all():
            break
    return rgb


for src_name, out_name in MAP.items():
    im = Image.open(os.path.join(SRC, src_name)).convert("RGB")
    a = np.asarray(im).astype(np.int16)

    mn = a.min(axis=2)
    cand = (mn >= MIN_CH) & ((a.max(axis=2) - mn) <= SAT_MAX)
    bg = outer_fill(cand)                 # 外周に繋がった白だけが背景
    opaque = ~bg

    # 余白を詰める（周囲に少しだけマージンを残す）
    ys, xs = np.where(opaque)
    pad = 8
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, a.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, a.shape[1])
    a, opaque = a[y0:y1, x0:x1], opaque[y0:y1, x0:x1]

    # --- 境界2pxの帯は P = α*F + (1-α)*白 とみなして α を逆算 ---
    core = opaque.copy()
    for _ in range(2):
        nb = np.zeros_like(core)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb |= np.roll(~core, (dy, dx), (0, 1))
        core &= ~nb
    band = opaque & ~core

    F = bleed(a, core, rounds=6)          # 帯の「本来の色」を内側から推定
    W = 254.0
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(W - F > 18, (W - a.astype(np.float32)) / np.maximum(W - F, 1e-6), 0.0)
    est = np.clip(ratio.max(axis=2), 0.0, 1.0)

    alpha = opaque.astype(np.float32)
    alpha[band] = est[band]
    alpha *= 255.0

    rgb = bleed(a, core)
    rgb[band] = F[band]

    # プリマルチプライして縮小 → 白フチが出ない
    pm = np.dstack([rgb * (alpha[..., None] / 255.0), alpha]).astype(np.float32)
    h, w = alpha.shape
    tw = min(TARGET_W, w)
    th = max(1, round(h * tw / w))
    pm_img = Image.fromarray(np.clip(pm, 0, 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)

    out = np.asarray(pm_img).astype(np.float32)
    al = out[..., 3:4]
    with np.errstate(divide="ignore", invalid="ignore"):
        un = np.where(al > 0, out[..., :3] / np.maximum(al / 255.0, 1e-6), 0)
    final = np.dstack([np.clip(un, 0, 255), al[..., 0]]).astype(np.uint8)

    dst = os.path.join(DST, out_name)
    # フラットなイラストなのでパレット化（透明度を保ったまま約1/8に軽量化）
    Image.fromarray(final).quantize(colors=192, method=Image.FASTOCTREE, dither=Image.NONE).save(dst, optimize=True)
    print("%-14s %4dx%-4d  %6.1f KB  透過 %.0f%%" % (
        out_name, tw, th, os.path.getsize(dst) / 1024, 100 * (1 - opaque.mean())))
