# Judith Schreiber's Gallery

Static Jekyll site for GitHub Pages, converted from the old Singapore PHP gallery.

The site keeps the original gallery names, image order, metadata, thumbnails, and image navigation. View counters and PHP runtime behavior were removed.

## Directory layout

- `content/galleries/` — source photos and `metadata.csv` files.
- `assets/gallery/` — generated copies of originals and thumbnails used by the site.
- `_data/gallery.json` — generated gallery manifest.
- `galleries/` — generated Markdown page front matter.
- `_layouts/` and `_includes/` — Jekyll templates.
- `tools/build_static.py` — rebuild script.

Do not edit generated files in `assets/gallery/`, `_data/gallery.json`, or `galleries/` directly. Edit the source content and rebuild instead.

## Build

From the `judithschreiber` directory:

```bash
python3 tools/build_static.py
```

The builder scans every gallery directory, preserves the order in `metadata.csv`, copies existing Singapore thumbnails, and generates missing thumbnail sizes with ImageMagick. If ImageMagick is unavailable, new photos are copied as fallback images instead of failing the build.

## Adding photos

1. Copy the original photo into the appropriate directory:

   ```text
   content/galleries/<Gallery Name>/
   ```

2. Optionally add a row to that gallery's `metadata.csv` to provide a title and metadata.
3. Run the build command.
4. Commit the updated generated files and assets.

Photos listed in `metadata.csv` appear in that file's order. Photos not listed in metadata are appended alphabetically and receive a title inferred from the filename. To add a new gallery, create a new directory under `content/galleries/`; it will be discovered automatically.

## GitHub Pages

Use the repository root as the GitHub Pages source. GitHub Pages will process `_config.yml` and build the Jekyll site automatically.

For a project site hosted below a subpath, set `baseurl` in `_config.yml` to that repository path, for example:

```yaml
baseurl: "/my-gallery"
```

For a custom domain or user site, leave `baseurl` empty.

## Local preview

After generating the site, a local Jekyll installation can preview it with:

```bash
jekyll serve
```

Then open the URL printed by Jekyll.
