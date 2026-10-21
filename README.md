# aiengineeringnotes.com

Source for [aiengineeringnotes.com](https://aiengineeringnotes.com) — notes from building AI systems.

Plain static HTML/CSS served by GitHub Pages from the `main` branch root. `CNAME` binds the custom domain.

## Navigation

Every page shares a sidebar (grouped notes in reading order), an "On this page" rail, and Previous / Next links. These are generated, not hand-written. The grouping and order live in one place, `tools/build_site.py`. After adding or moving a page:

    python3 tools/build_site.py

The script rewrites only the text between `<!-- site:... -->` markers on each page; article bodies are never touched.
