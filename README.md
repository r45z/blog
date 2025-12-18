# CoreBlog

> Clarity through simplicity

CoreBlog is a minimalist, content-focused blogging platform built with Python, Flask, and SQLite3.

## Features

- **Clean, Readable Design**: Optimized typography and spacing for the best reading experience
- **Markdown Content**: Write posts in Markdown format with syntax highlighting
- **Fast & Lightweight**: Minimal dependencies, quick page loads
- **Automatic Post Discovery**: New Markdown files are automatically detected and published
- **Newsletter Subscription**: Simple subscription system integrated
- **Infinite Scroll**: Smooth loading experience for readers

## Design Philosophy

CoreBlog emphasizes readability and content clarity by:

- Using optimal line length (around 42rem/66 characters)
- Providing adequate spacing between paragraphs (1.5em)
- Setting comfortable line height (1.8)
- Using clear typography with proper hierarchy
- Eliminating unnecessary distractions

## Customization

You can easily customize CoreBlog by editing `config.py`:

```python
# Theme colors
BACKGROUND_COLOR = "#FFFFFF"
ACCENT_COLOR = "#3B82F6" 
TEXT_COLOR = "#1F2937"

# Typography
BODY_FONT = "Arial, sans-serif"
HEADING_FONT = "Arial, sans-serif"
BODY_FONT_SIZE = "1.1rem"
BODY_LINE_HEIGHT = 1.8
```

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the development server: `./dev.sh`
4. Add Markdown files to the `posts/` directory

## License

MIT 