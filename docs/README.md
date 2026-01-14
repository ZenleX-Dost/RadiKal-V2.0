# RadiKal V2.0 Documentation

This directory contains the complete Read the Docs documentation for RadiKal V2.0.

## Documentation Structure

- **index.md** - Main landing page
- **getting-started.md** - Quick start guide
- **installation.md** - Complete installation instructions
- **user-guide.md** - Comprehensive user manual
- **api-reference.md** - Complete API documentation
- **architecture.md** - System architecture and design
- **deployment.md** - Production deployment guide
- **testing.md** - Testing and quality assurance
- **troubleshooting.md** - Common issues and solutions
- **sam2-guide.md** - SAM2 segmentation guide
- **xai-methods.md** - Explainable AI methods
- **RIAWELC_DATASET_INFO.md** - Dataset information

## Building the Documentation

### Local Development

Install dependencies:
```bash
pip install -r requirements.txt
```

Serve documentation locally:
```bash
mkdocs serve
```

Then visit: http://localhost:8000

### Build Static Site

```bash
mkdocs build
```

Output will be in `site/` directory.

### Deploy to Read the Docs

1. Push to GitHub repository
2. Import project on Read the Docs (https://readthedocs.org)
3. The `.readthedocs.yaml` file will configure the build
4. Documentation will be available at: https://radikal-v2.readthedocs.io

## Configuration

- **mkdocs.yml** - MkDocs configuration (root directory)
- **.readthedocs.yaml** - Read the Docs build configuration (root directory)
- **requirements.txt** - Documentation dependencies

## Theme

Documentation uses the Material for MkDocs theme with:
- Light/dark mode toggle
- Navigation tabs
- Search functionality
- Code syntax highlighting
- Responsive design

## Contributing to Documentation

1. Edit markdown files in this directory
2. Test changes locally with `mkdocs serve`
3. Ensure no broken links
4. Follow existing formatting style
5. Submit pull request

## Documentation Standards

- Use clear, concise language
- Include code examples where applicable
- Add diagrams for complex concepts
- Keep navigation structure logical
- Maintain consistent formatting
- No emojis in technical documentation

## Support

For documentation issues:
- Check the [Troubleshooting Guide](troubleshooting.md)
- Open GitHub issue
- Contact documentation team
