import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


OPEN_LIBRARY_BOOKS_URL = "https://openlibrary.org/api/books"
OPEN_LIBRARY_COVER_URL = "https://covers.openlibrary.org/b/isbn"


def normalize_barcode(value):
    return "".join(character for character in value.upper() if character.isdigit() or character == "X")


def is_valid_isbn10(isbn):
    if len(isbn) != 10:
        return False

    total = 0
    for index, character in enumerate(isbn):
        if character == "X" and index == 9:
            digit = 10
        elif character.isdigit():
            digit = int(character)
        else:
            return False
        total += digit * (10 - index)

    return total % 11 == 0


def is_valid_isbn13(isbn):
    if len(isbn) != 13 or not isbn.isdigit():
        return False

    total = 0
    for index, character in enumerate(isbn):
        multiplier = 1 if index % 2 == 0 else 3
        total += int(character) * multiplier

    return total % 10 == 0


def is_valid_isbn(isbn):
    return is_valid_isbn10(isbn) or is_valid_isbn13(isbn)


def get_cover_url_for_isbn(isbn, size="M"):
    normalized_isbn = normalize_barcode(isbn)
    return f"{OPEN_LIBRARY_COVER_URL}/{normalized_isbn}-{size}.jpg"


def parse_publish_date(value):
    if not value:
        return ""

    parts = value.split()
    if len(parts) == 1 and parts[0].isdigit():
        return f"{parts[0]}-01-01"

    return ""


def extract_book_data(payload, isbn):
    book_data = payload.get(f"ISBN:{isbn}", {})
    details = book_data.get("details", {})
    authors = details.get("authors", [])

    return {
        "isbn": isbn,
        "title": details.get("title", ""),
        "publish_date": parse_publish_date(details.get("publish_date", "")),
        "authors": [author.get("name", "") for author in authors if author.get("name")],
        "cover_url": get_cover_url_for_isbn(isbn),
    }


def lookup_book_by_isbn(value, timeout=10):
    isbn = normalize_barcode(value)
    if not is_valid_isbn(isbn):
        return None, "Invalid ISBN barcode."

    url = (
        f"{OPEN_LIBRARY_BOOKS_URL}"
        f"?bibkeys=ISBN:{isbn}"
        "&format=json"
        "&jscmd=details"
    )

    try:
        with urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return None, f"OpenLibrary request failed with status {error.code}."
    except URLError:
        return None, "OpenLibrary could not be reached."
    except json.JSONDecodeError:
        return None, "OpenLibrary returned invalid JSON."

    if not payload.get(f"ISBN:{isbn}"):
        return {
            "isbn": isbn,
            "title": "",
            "publish_date": "",
            "authors": [],
            "cover_url": get_cover_url_for_isbn(isbn),
        }, "No book metadata found for this ISBN."

    return extract_book_data(payload, isbn), None
