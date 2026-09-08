# Ari NBA Cards — phone-friendly GitHub workflow

This version is designed so image files do **not** need to be manually uploaded, renamed or processed.

## How it works

1. `image-manifest.json` contains the approved image sources.
2. GitHub Actions downloads only entries with an explicit `download_url`.
3. Images are automatically rotated, resized and compressed into `images/<player-id>.jpg`.
4. Validation runs before deployment.
5. GitHub Pages publishes the resulting app.

The workflow runs on pushes to `main` and can also be started manually from the GitHub Actions tab.

## Adding an image from your phone

Edit `image-manifest.json` in GitHub's web interface and add/update:

```json
"download_url": "https://commons.wikimedia.org/wiki/Special:Redirect/file/EXACT_FILE_NAME.jpg",
"required": true
```

The next workflow run downloads and processes it. No JPEG file management is required.

For copyrighted images, only add a direct URL when we have established that the image is legitimately reusable under its stated licence. Keep `source`, `license`, and `notes` in the manifest.

## Pilot

The pilot contains explicitly selected reusable sources. Players without `download_url` continue to use the app's existing network fallback until an approved local source is added.
