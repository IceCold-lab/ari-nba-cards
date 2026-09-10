# Ari NBA Cards — Image Review Tool

Put `image-review.html` beside `players.json` in the repository.

Open:
`https://icecold-lab.github.io/ari-nba-cards/image-review.html`

Press **Load players**. The tool searches Wikimedia Commons for technically suitable candidates and shows them in a phone-friendly review grid.

- **KEEP** = approve this candidate
- **MAYBE** = flag it for another look
- **OPEN** = inspect the Commons file page
- **Export approvals** = create `image-approvals.json`

Decisions are stored in browser localStorage. The tool does not alter `players.json` or download/publish images.

MediaWiki's Imageinfo API provides image URLs, dimensions, MIME type and thumbnail URLs, which is what the tool uses for candidate discovery.
