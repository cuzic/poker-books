#!/usr/bin/env python3
"""GTO Wizard ブログから flop 関連記事の本文画像を一括取得する.

article URL → HTML → 本文画像 URL → 画像ダウンロード を一気に行う。
著者写真・サムネ・装飾画像は除外し、本文の図表のみを保存。
"""
from __future__ import annotations
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
HTML_DIR = ROOT / "html"
IMG_DIR = ROOT / "images"
HTML_DIR.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"

ARTICLES = [
    ("01_ip_cbet_cash", "https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/"),
    ("02_ip_cbet_mtt", "https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-mtts/"),
    ("03_oop_cbet_mtt", "https://blog.gtowizard.com/flop-heuristics-oop-c-betting-in-mtts/"),
    ("04_bb_defense_mtt", "https://blog.gtowizard.com/flop-heuristics-for-defending-the-blinds-in-mtts/"),
    ("05_cbet_sizing_mechanics", "https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/"),
    ("06_oop_cbet_raiser", "https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/"),
    ("07_oop_3bet_pots", "https://blog.gtowizard.com/c-betting-oop-in-3-bet-pots/"),
    ("08_sb_srp_aggregate", "https://blog.gtowizard.com/aggregate-flop-strategy-sb-c-betting-in-srp/"),
    ("09_monotone_value", "https://blog.gtowizard.com/maximizing-value-on-monotone-flops/"),
    ("10_paired_bb_attack", "https://blog.gtowizard.com/attacking-paired-flops-from-the-bb/"),
    ("11_exploit_ip_excessive", "https://blog.gtowizard.com/exploiting-excessive-c-betting-by-ip/"),
    ("12_exploit_oop_excessive", "https://blog.gtowizard.com/exploiting-excessive-c-betting-by-oop/"),
    ("13_paired_xr_defense", "https://blog.gtowizard.com/defending-vs-bb-check-raise-on-paired-flops/"),
    ("14_geometric_bet", "https://blog.gtowizard.com/why-so-much-an-exploration-of-larger-than-geometric-bet-sizing/"),
    ("15_donk_betting", "https://blog.gtowizard.com/is-donk-betting-for-donkeys/"),
]

EXCLUDE_PATTERNS = ["logo", "avatar", "favicon", "GTO-Wizard-1", "GTO-Wizard-3", "GTO-Wizard-6", "GTO-Wizard-7", "GTO-Wizard-9", "120x120"]


def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def extract_content_images(html: str) -> list[str]:
    m = re.search(r'<div class="entry-content[^"]*">(.*?)<div class="entry-footer', html, re.DOTALL)
    if not m:
        m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
    if not m:
        return []
    content = m.group(1)
    imgs = re.findall(r'src="(https://[^"]+\.(?:png|jpg|jpeg|webp))', content)
    out = []
    for u in imgs:
        if any(p in u for p in EXCLUDE_PATTERNS):
            continue
        if "thumbnail" in u or "768x432" in u or "1152x648" in u:
            continue
        if "header-" in u and ("768x432" in u or "1152x648" in u):
            continue
        out.append(u)
    return sorted(set(out))


def main():
    manifest = []
    for slug, url in ARTICLES:
        html_path = HTML_DIR / f"{slug}.html"
        try:
            if not html_path.exists():
                print(f"[fetch] {slug} ...")
                html_bytes = fetch(url)
                html_path.write_bytes(html_bytes)
            html = html_path.read_text(errors="replace")
        except Exception as e:
            print(f"[skip] {slug}: HTML fetch failed: {e}")
            continue

        imgs = extract_content_images(html)
        print(f"  {slug}: {len(imgs)} content images")
        for i, img_url in enumerate(imgs, 1):
            ext = Path(urlparse(img_url).path).suffix
            local = IMG_DIR / f"{slug}_img{i:02d}{ext}"
            if not local.exists():
                try:
                    data = fetch(img_url, timeout=20)
                    local.write_bytes(data)
                except Exception as e:
                    print(f"    [skip] img{i}: {e}")
                    continue
            manifest.append({
                "article_slug": slug,
                "article_url": url,
                "image_index": i,
                "image_url": img_url,
                "local_path": str(local.relative_to(ROOT)),
                "size_bytes": local.stat().st_size if local.exists() else 0,
            })

    manifest_path = ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nTotal images: {len(manifest)}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
