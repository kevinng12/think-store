# think-store
Testing store for TT BHS

## GitHub Pages deployment
This project is static and is ready to deploy to GitHub Pages.

### Setup
1. Push this repository to GitHub.
2. Open the repository settings and go to Pages.
3. Set Source to GitHub Actions.
4. Ensure the default branch is `main`.

The workflow in `.github/workflows/deploy-pages.yml` automatically publishes the site whenever changes are pushed to `main`.

### Public Google Sheet config
This version reads from a public Google Sheet by CSV export. Keep the real values out of the repo by setting GitHub repository secrets:

- `PUBLIC_SHEET_URL`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

The workflow in `.github/workflows/deploy-pages.yml` generates a local `config.js` file during deployment from those secrets, so the committed source does not include the real values.

For local testing, create a `config.js` file in the project root with the same shape as the generated file.

### Local preview
Serve the folder with a simple local web server so the browser can fetch the data correctly.

Example:

```bash
python -m http.server 8000
```

Then open:

- http://localhost:8000/
- http://localhost:8000/sheet.html

### Notes
- Public Google Sheets can be fetched directly from the browser via CSV export.
- Credentials or sensitive values should stay in a local `config.js` file or in GitHub Actions secrets, not in the committed source code.
- For private Google Sheets, you still need a backend or serverless function to protect credentials.
