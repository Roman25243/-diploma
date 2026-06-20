from __future__ import annotations

import shutil
from pathlib import Path

from app import app
from flask import render_template


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "frontend_dist"
STATIC_SRC = ROOT / "static"
STATIC_DST = OUTPUT_DIR / "static"

API_BASE_URL = "https://cinema-book-backend-654c83941de1.herokuapp.com"


def build_index_html() -> str:
    with app.test_request_context("/app/"):
        html = render_template("spa.html")

    injection = (
        '  <script>\n'
        f'    window.__CINEMABOOK_API_BASE_URL__ = "{API_BASE_URL}";\n'
        '  </script>\n'
    )
    marker = '<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>'
    if "window.__CINEMABOOK_API_BASE_URL__" not in html:
        html = html.replace(marker, injection + marker, 1)
    return html


def sync_static_assets() -> None:
    if STATIC_DST.exists():
        shutil.rmtree(STATIC_DST)
    shutil.copytree(STATIC_SRC, STATIC_DST, dirs_exist_ok=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.html").write_text(build_index_html(), encoding="utf-8")
    sync_static_assets()
    print(f"Exported Cloudflare Pages site to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()