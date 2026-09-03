# think-store
Testing store for TT BHS

## GitHub Pages deployment
This project is a static website and is ready to deploy to GitHub Pages.

### Setup
1. Push this repository to GitHub.
2. In the repository settings, open Pages.
3. Set Source to GitHub Actions.
4. Make sure the default branch is `main`.

The workflow in `.github/workflows/deploy-pages.yml` will automatically publish the site whenever changes are pushed to `main`.

### Local preview
Open `index.html` in a browser, or serve the folder with a simple local web server if you want a browser preview that matches deployment behavior.
