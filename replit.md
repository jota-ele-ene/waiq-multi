# WAIQ Full - Hugo Blog with TinaCMS

## Overview
This is a multilingual (English/Spanish) blog website built with Hugo static site generator and TinaCMS for content management. The site features articles about technology topics including AI, quantum computing, and web3, organized by areas such as technology, innovation, business, legal, and ethics.

## Project Architecture

### Technology Stack
- **Hugo Extended** (v0.152.2): Static site generator with SCSS support
- **TinaCMS**: Headless CMS for content management
- **Node.js**: Runtime for TinaCMS and build tools
- **Theme**: blog-story (custom Hugo theme)

### Key Features
- Multilingual support (English and Spanish)
- Password-protected access (gate feature)
- Content categorized by topics (ai, quantum, web3) and areas
- TinaCMS admin interface for content editing
- Search functionality
- Gallery and profile pictures
- Responsive design

### Directory Structure
- `content/`: Markdown content files (organized by language: en/es)
  - `article/`: Blog articles
  - `banner/`: Banner content
  - `picture/`: Profile pictures
  - `legal/`: Legal pages (privacy, cookies, notice)
  - `topics/`, `areas/`: Taxonomy pages
- `themes/blog-story/`: Hugo theme
- `static/`: Static assets (CSS, JS, images, fonts)
- `config/`: Hugo configuration files (default, development, production)
- `tina/`: TinaCMS configuration
- `public/`: Generated static site (build output)

## Development Setup

### Running Locally
The project is configured to run on port 5000 with the Hugo development server:
```bash
npm run dev
```

This command:
1. Starts TinaCMS dev server on port 4001
2. Runs Hugo server on 0.0.0.0:5000
3. Enables live reload and draft content

### TinaCMS Admin
Access the CMS admin interface at `/admin/index.html` when the dev server is running.

### Environment Variables
TinaCMS requires:
- `TINA_PUBLIC_CLIENT_ID`: TinaCMS public client ID
- `TINA_TOKEN`: TinaCMS authentication token

## Build and Deployment

### Build Command
```bash
npm run build
```

This builds:
1. TinaCMS admin interface (output to `static/admin/`)
2. Hugo static site (output to `public/`)

### Deployment Configuration
- **Type**: Static site
- **Build**: `npm run build`
- **Output directory**: `public/`

The site generates a fully static output that can be deployed to any static hosting platform.

## Recent Changes (December 1, 2025)

### Replit Environment Setup
1. Replaced `hugo-bin` with `hugo-extended` package to support SCSS compilation
2. Configured Hugo dev server to bind to `0.0.0.0:5000` for Replit proxy compatibility
3. Updated development configuration to use `baseURL = "/"` for relative URLs
4. Set up workflow for "Start Hugo with TinaCMS"
5. Configured static deployment with build command

### Configuration Updates
- `package.json`: Updated dev script with proper Hugo server flags
- `config/development/config.toml`: Changed baseURL from `http://localhost:1313` to `/`
- Added deployment configuration for static site publishing

## Notes
- The site uses relativeURLs to ensure proper asset loading through Replit's proxy
- Hugo extended version is required for SCSS/SASS compilation
- TinaCMS generates admin interface and GraphQL client files automatically
- Content is organized with Hugo's taxonomy system (topics and areas)
- The site includes a password gate feature for access control
