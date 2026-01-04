# Updating the GitHub Pages Site

This directory contains the static documentation site for LyricSync, hosted on GitHub Pages.

## File Structure

- `index.md` - Main landing page
- `assets/` - Screenshots and images
- `_config.yml` - Jekyll theme configuration

## How to Update

### Adding or Updating Content

1. Edit `docs/index.md` to update the landing page content
2. Add new screenshots to `docs/assets/` directory
3. Update image references in `index.md` to use relative paths: `./assets/filename.png`

### Adding Screenshots

1. Place image files in `docs/assets/`
2. Reference them in `index.md`:
   ```markdown
   ![Description](./assets/filename.png)
   ```

### GitHub Pages Setup

1. Go to repository Settings → Pages
2. Under "Source", select "Deploy from a branch"
3. Choose branch (usually `main` or `master`)
4. Select `/docs` as the folder
5. Save

The site will be available at `https://YOUR_USERNAME.github.io/LyricSync/`

## Recent Changes

### Initial Setup (Current Version)

- Created `docs/` folder structure
- Moved screenshots from `images/` to `docs/assets/`
- Created high-signal landing page with:
  - Hero section with key value propositions
  - Demo screenshots with technical captions
  - Architecture diagram using ASCII art
  - Key engineering decisions with rationale
  - Local run instructions
  - Realistic roadmap
- Configured Jekyll theme (cayman) for clean presentation
- Updated root README with link to docs site

### Design Principles

- **High signal, low noise**: Focus on technical depth and engineering decisions
- **Recruiter-friendly**: Clear value propositions and system design maturity
- **Static only**: No backend deployment, Markdown + images only
- **Minimal dependencies**: Uses GitHub Pages default Jekyll theme

