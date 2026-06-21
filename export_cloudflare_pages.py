from __future__ import annotations

import shutil
from pathlib import Path

from app import app
from flask import render_template


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "frontend_dist"
STATIC_SRC = ROOT / "static"
STATIC_DST = OUTPUT_DIR / "static"
HEADERS_FILE = OUTPUT_DIR / "_headers"

API_BASE_URL = "https://cinema-book-backend-654c83941de1.herokuapp.com"


def build_index_html() -> str:
    with app.test_request_context("/app/"):
        html = render_template("spa.html")

    injection = (
        '  <script>\n'
        f'    window.__CINEMABOOK_API_BASE_URL__ = "{API_BASE_URL}";\n'
        '  </script>\n'
    )
    if "window.__CINEMABOOK_API_BASE_URL__" not in html:
        html = html.replace('<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>', injection + '<script src="/static/js/vue.global.js"></script>', 1)
    html = html.replace(
        '<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>',
        '<script src="/static/js/vue.global.js"></script>',
    )
    html = html.replace(
        '<script src="https://unpkg.com/vue-router@4/dist/vue-router.global.js"></script>',
        '<script src="/static/js/vue-router.global.js"></script>',
    )
    return html


def sync_static_assets() -> None:
    if STATIC_DST.exists():
        shutil.rmtree(STATIC_DST)
    shutil.copytree(STATIC_SRC, STATIC_DST, dirs_exist_ok=True)
    uploads_dir = STATIC_DST / "uploads"
    if uploads_dir.exists():
        shutil.rmtree(uploads_dir)


def write_headers_file() -> None:
    HEADERS_FILE.write_text(
        "/index.html\n"
        "  Cache-Control: no-store, no-cache, must-revalidate\n"
        "\n"
        "/app\n"
        "  Cache-Control: no-store, no-cache, must-revalidate\n"
        "\n"
        "/app/*\n"
        "  Cache-Control: no-store, no-cache, must-revalidate\n",
        encoding="utf-8",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.html").write_text(build_index_html(), encoding="utf-8")
    sync_static_assets()
    write_headers_file()
    print(f"Exported Cloudflare Pages site to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()