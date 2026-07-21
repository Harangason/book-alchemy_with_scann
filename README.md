# Book Alchemy Scan

Flask library app for managing fantasy books and authors. This scan variant includes all base library features plus ISBN barcode scanning on the add-book page.

## Features

- Add, edit, and delete books.
- Add and delete authors, including cascade-deleting their books.
- Store ISBN, title, publication date, author, and rating from 1 to 10.
- Scan ISBN barcodes on `/add_book` with a phone or tablet camera when the browser supports the `BarcodeDetector` API.
- Show book covers from OpenLibrary based on ISBN.
- Search books by title using a SQL `LIKE` query.
- Sort books by title or author.
- Open dynamic detail pages for books and authors.
- Generate a book recommendation through RapidAPI when `RAPIDAPI_KEY` is configured.

## Project Structure

```text
book-alchemy-de-scan/
  app.py
  data/
    data_models.py
    library.sqlite
  static/
    css/
      add_author.css
      add_book.css
      detail.css
      edit_book.css
      home.css
    js/
      barcode_scanner.js
  templates/
    add_author.html
    add_book.html
    author_detail.html
    book_detail.html
    edit_book.html
    home.html
    recommendation.html
  test_app.py
```

## Run

This copy currently reuses the virtual environment from the original project:

```powershell
..\book-alchemy-de\.venv\Scripts\python.exe app.py
```

If you create a separate virtual environment in this folder, use that environment instead.

## Important Routes

- `/` — library home page.
- `/add_author` — add an author.
- `/add_book` — add a book, optionally by scanning an ISBN barcode.
- `/book/<book_id>` — book detail page.
- `/book/<book_id>/edit` — edit a book.
- `/book/<book_id>/delete` — delete a book with `POST`.
- `/author/<author_id>` — author detail page.
- `/author/<author_id>/delete` — delete an author and their books with `POST`.
- `/recommendation` — generate a recommendation through RapidAPI.

## ISBN Lookup

- Python lookup functions live in `book_lookup.py`.
- `/api/books/lookup?isbn=...` validates the scanned barcode/ISBN.
- The lookup fetches book metadata from OpenLibrary and returns title, publish date, authors, and cover URL as JSON.
- The add-book page can fill title/date fields and show a cover preview after scanning or manual ISBN entry.

## Barcode Scanning

- The scanner is implemented in `static/js/barcode_scanner.js`.
- It uses the browser-native `BarcodeDetector` API.
- Camera access usually requires `https` or `localhost`.
- Browser support is best in Chrome/Edge on Android.
- Unsupported browsers can still enter ISBN manually.

## RapidAPI Recommendation

The recommendation page is available at `/recommendation`.

Set the key outside Git before generating recommendations:

```powershell
$env:RAPIDAPI_KEY = "your-key"
```

Alternatively, create an ignored `.env.local` file:

```text
RAPIDAPI_KEY=your-key
```

Do not commit API keys.

## Tests

```powershell
..\book-alchemy-de\.venv\Scripts\python.exe -m unittest -q
```

## Notes

- The local SQLite database is stored at `data/library.sqlite`.
- Runtime files, cache files, local databases, and env files are ignored by Git.
- This repository is the scan-enabled version. The non-camera version remains in `book-alchemy-de`.

