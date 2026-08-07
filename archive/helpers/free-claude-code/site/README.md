# Staff Claude Code — static site

Zero-token learning UI for the curriculum in `../lessons/`.

## Run locally

```bash
cd archive/helpers/free-claude-code/site
npm install
npm run dev
```

Open the URL Astro prints (default `http://localhost:4321`).

## How content stays in sync

Markdown source of truth: `../lessons/`.

```bash
npm run sync   # also runs automatically before dev/build
```

Templates are copied to `public/templates/<module>/` for download from module pages.

## Deploy

```bash
npm run build
# publish dist/
```

Project-pages style base path:

```bash
SITE_URL=https://you.github.io SITE_BASE=/your-repo/ npm run build
```

## Design

Ink + teal instrument theme (`src/styles/custom.css`). Search via Pagefind is built into Starlight.
