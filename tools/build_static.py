#!/usr/bin/env python3
"""Prepare the Singapore gallery for GitHub Pages/Jekyll.
Put new images in content/galleries/<album>/ and run this script. Existing
metadata.csv rows keep their order and titles; unlisted files are appended in
filename order and get a title from their filename.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "content" / "galleries"
DATA_ROOT = ROOT / "_data"
ASSET_ROOT = ROOT / "assets"
IMAGE_ASSET_ROOT = ASSET_ROOT / "gallery"
PAGE_ROOT = ROOT / "galleries"
IMAGE_EXTENSIONS = {".jpeg", ".jpg", ".jpe", ".png", ".gif", ".bmp", ".tif", ".tiff"}


def slugify(value: str, fallback: str = "item") -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or fallback


def unique_slug(value: str, used: set[str], fallback: str) -> str:
    base = slugify(value, fallback)
    slug = base
    suffix = 2
    while slug in used:
        slug = f"{base}-{suffix}"
        suffix += 1
    used.add(slug)
    return slug


def image_files(directory: Path) -> list[Path]:
    return sorted(
        (p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS),
        key=lambda p: p.name,
    )


def value(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


def inferred_name(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").strip()


def read_metadata(directory: Path) -> tuple[list[str], list[list[str]]]:
    path = directory / "metadata.csv"
    if not path.exists():
        return [], []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        rows = list(csv.reader(handle))
    return (rows[1] if len(rows) > 1 else []), rows[2:]


def make_image(filename: str, row: list[str] | None, used: set[str]) -> dict:
    row = row or []
    return {
        "filename": filename,
        "slug": unique_slug(Path(filename).stem, used, "image"),
        "name": value(row, 6) or inferred_name(filename),
        "artist": value(row, 7),
        "copyright": value(row, 9),
        "description": value(row, 10),
        "location": value(row, 11),
        "date": value(row, 12),
        "camera": value(row, 13),
        "lens": value(row, 14),
        "film": value(row, 15),
        "darkroom": value(row, 16),
        "digital": value(row, 17),
    }


def load_gallery(directory: Path, used_gallery_slugs: set[str]) -> dict:
    gallery_row, image_rows = read_metadata(directory)
    slug = unique_slug(directory.name, used_gallery_slugs, "gallery")
    images_by_name = {path.name: path for path in image_files(directory)}
    rows_by_name: dict[str, list[str]] = {}
    ordered_names: list[str] = []
    for row in image_rows:
        filename = value(row, 0)
        if filename in images_by_name and filename not in rows_by_name:
            rows_by_name[filename] = row
            ordered_names.append(filename)
    ordered_names.extend(name for name in sorted(images_by_name) if name not in rows_by_name)
    image_slugs: set[str] = set()
    images = [make_image(name, rows_by_name.get(name), image_slugs) for name in ordered_names]
    return {
        "slug": slug,
        "source": str(directory.relative_to(ROOT)),
        "name": value(gallery_row, 6) or directory.name.replace("_", " "),
        "artist": value(gallery_row, 7),
        "description": value(gallery_row, 10),
        "summary": value(gallery_row, 11),
        "date": value(gallery_row, 12),
        "filename": value(gallery_row, 0),
        "images": images,
    }


def prepare_thumbnails(source: Path, thumbs: Path, destination: Path, prefix: str, size: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    existing = thumbs / f"{prefix}-{source.name}"
    if existing.exists():
        shutil.copy2(existing, destination)
        return
    try:
        subprocess.run(
            ["magick", str(source), "-auto-orient", "-thumbnail", f"{size}>", str(destination)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        shutil.copy2(source, destination)


def add_assets(gallery: dict, directory: Path) -> None:
    gallery_dir = IMAGE_ASSET_ROOT / gallery["slug"]
    thumbs = directory / "_thumbs"
    for image in gallery["images"]:
        source = directory / image["filename"]
        suffix = source.suffix.lower()
        base = f"{image['slug']}{suffix}"
        original = gallery_dir / base
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, original)
        image["path"] = f"/assets/gallery/{gallery['slug']}/{base}"
        for key, prefix, size in (("thumb50", "50x50", "50x50"), ("thumb80", "80x80", "80x80"), ("thumb100", "100x100", "100x100"), ("display", "700x500", "700x500")):
            output = gallery_dir / key / base
            prepare_thumbnails(source, thumbs, output, prefix, size)
            image[key] = f"/assets/gallery/{gallery['slug']}/{key}/{base}"


def write_front_matter(path: Path, layout: str, **fields: str) -> None:
    lines = ["---", f"layout: {layout}"]
    lines.extend(f"{key}: {value}" for key, value in fields.items())
    lines.extend(["---", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build() -> None:
    shutil.rmtree(PAGE_ROOT, ignore_errors=True)
    shutil.rmtree(IMAGE_ASSET_ROOT, ignore_errors=True)
    galleries: list[dict] = []
    used_gallery_slugs: set[str] = set()
    for directory in sorted(p for p in SOURCE_ROOT.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        gallery = load_gallery(directory, used_gallery_slugs)
        add_assets(gallery, directory)
        galleries.append(gallery)

    for index, gallery in enumerate(galleries):
        gallery["thumbnail"] = next((image for image in gallery["images"] if image["filename"] == gallery["filename"]), None) or (gallery["images"][0] if gallery["images"] else None)
        gallery["previous"] = galleries[index - 1]["slug"] if index else ""
        gallery["next"] = galleries[index + 1]["slug"] if index + 1 < len(galleries) else ""
        gallery_page = PAGE_ROOT / gallery["slug"] / "index.md"
        write_front_matter(gallery_page, "gallery", gallery=gallery["slug"])
        for image in gallery["images"]:
            write_front_matter(PAGE_ROOT / gallery["slug"] / "images" / image["slug"] / "index.md", "image", gallery=gallery["slug"], image=image["slug"])

    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    (DATA_ROOT / "gallery.json").write_text(json.dumps({"name": "Judith Schreiber's Gallery", "galleries": galleries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared {len(galleries)} galleries and {sum(len(gallery['images']) for gallery in galleries)} images")

if __name__ == "__main__":
    build()
