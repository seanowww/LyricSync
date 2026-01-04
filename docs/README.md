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

### Generating Architecture Diagram

The architecture diagram is defined in PlantUML format at `docs/assets/architecture.puml`.

1. Install PlantUML:
   ```bash
   # macOS
   brew install plantuml
   
   # Or download JAR from http://plantuml.com/download
   # Then run: java -jar plantuml.jar docs/assets/architecture.puml -o docs/assets/
   ```

2. Generate the PNG image:
   ```bash
   plantuml docs/assets/architecture.puml -o docs/assets/
   ```
   
   This creates `docs/assets/architecture.png` from the PlantUML source file.

3. The diagram uses the LyricSync dark theme colors (#0E0E11 background, #6D5AE6 accent) for visual consistency with the application.

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
  - PlantUML architecture diagram with dark theme
  - Key engineering decisions with rationale
  - Local run instructions
  - Realistic roadmap
- Applied LyricSync dark theme styling (inline CSS)
- Configured Jekyll theme (minimal) for clean presentation
- Updated root README with link to docs site

### Architecture Diagram Improvements

- Replaced ASCII art with professional PlantUML diagram
- Industry-standard layer separation (Presentation, Application, Data)
- Clear component grouping and service boundaries
- Labeled data flow with protocol/format information
- Comprehensive annotations for key features
- Dark theme color scheme matching application (#0E0E11, #6D5AE6)
- Professional styling with proper typography and spacing

### Design Principles

- **High signal, low noise**: Focus on technical depth and engineering decisions
- **Recruiter-friendly**: Clear value propositions and system design maturity
- **Static only**: No backend deployment, Markdown + images only
- **Minimal dependencies**: Uses GitHub Pages default Jekyll theme

