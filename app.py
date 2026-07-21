from datetime import date
import json

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
import os
from sqlalchemy import inspect
from sqlalchemy.sql import text
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from data.data_models import Author, Book, db
from book_lookup import get_cover_url_for_isbn, lookup_book_by_isbn


app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'data/library.sqlite')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'
app.config['RAPIDAPI_HOST'] = 'language-complexity-layering.p.rapidapi.com'
app.config['RAPIDAPI_URL'] = 'https://language-complexity-layering.p.rapidapi.com/api/language-complexity-layering'

db.init_app(app)


def check_tables():
    with app.app_context():
        if app.config.get('TESTING', False):
            db.drop_all()
            return False

        inspector = inspect(db.engine)
        tables_are_missing = any(
            not inspector.has_table(table.name)
            for table in db.metadata.sorted_tables
        )

        if tables_are_missing:
            db.create_all()
            return True

        book_columns = [column['name'] for column in inspector.get_columns('book')]
        if 'rating' not in book_columns:
            db.session.execute(text('ALTER TABLE book ADD COLUMN rating INTEGER'))
            db.session.commit()

        return False


check_tables()


def load_local_env():
    for filename in ('.env.local', '.env'):
        path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(path):
            continue

        with open(path, encoding='utf-8') as env_file:
            for line in env_file:
                clean_line = line.strip()
                if not clean_line or clean_line.startswith('#') or '=' not in clean_line:
                    continue

                key, value = clean_line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()


def parse_optional_date(value):
    if not value:
        return None
    return date.fromisoformat(value)


def get_cover_url(isbn):
    return get_cover_url_for_isbn(isbn)


def parse_optional_rating(value):
    if not value:
        return None

    rating = int(value)
    if rating < 1 or rating > 10:
        raise ValueError("Rating must be between 1 and 10.")
    return rating


def build_library_prompt():
    books = Book.query.join(Author).order_by(Author.name, Book.title).all()
    if not books:
        return ""

    book_lines = []
    for book in books:
        rating = book.rating if book.rating else "not rated"
        book_lines.append(f"- {book.title} by {book.author.name}; rating: {rating}/10")

    return (
        "Based on this fantasy library, recommend one next book to read. "
        "Use the ratings if available and explain the recommendation briefly.\n\n"
        + "\n".join(book_lines)
    )


def parse_rapidapi_response(response_body):
    try:
        payload = json.loads(response_body)
    except json.JSONDecodeError:
        return response_body

    if isinstance(payload, dict):
        for key in ('recommendation', 'result', 'text', 'data', 'message'):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        return json.dumps(payload, indent=2, ensure_ascii=False)

    return str(payload)


def get_book_recommendation():
    api_key = os.environ.get('RAPIDAPI_KEY')
    if not api_key:
        return None, "RAPIDAPI_KEY is missing. Add it to .env.local or your environment."

    library_prompt = build_library_prompt()
    if not library_prompt:
        return None, "No books found. Add books before requesting a recommendation."

    request_data = urlencode({
        'data': library_prompt,
        'version': os.environ.get('RAPIDAPI_VERSION', ''),
    }).encode('utf-8')
    api_request = Request(
        app.config['RAPIDAPI_URL'],
        data=request_data,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-rapidapi-host': app.config['RAPIDAPI_HOST'],
            'x-rapidapi-key': api_key,
        },
        method='POST',
    )

    try:
        with urlopen(api_request, timeout=20) as response:
            response_body = response.read().decode('utf-8')
    except HTTPError as error:
        return None, f"RapidAPI request failed with status {error.code}."
    except URLError:
        return None, "RapidAPI request failed because the API could not be reached."

    return parse_rapidapi_response(response_body), None


@app.route('/')
def home():
    sort_by = request.args.get('sort', 'title')
    search_query = request.args.get('q', '').strip()
    query = Book.query

    if search_query:
        query = query.filter(Book.title.like(f"%{search_query}%"))

    if sort_by == 'author':
        books = query.join(Author).order_by(Author.name, Book.title).all()
    else:
        sort_by = 'title'
        books = query.order_by(Book.title).all()

    book_data = [
        {
            'id': book.id,
            'title': book.title,
            'author_id': book.author.id if book.author else None,
            'author_name': book.author.name if book.author else 'Unknown author',
            'cover_url': get_cover_url(book.isbn),
            'rating': book.rating,
        }
        for book in books
    ]
    return render_template(
        'home.html',
        books=book_data,
        sort_by=sort_by,
        search_query=search_query,
    )


@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template(
        'book_detail.html',
        book=book,
        cover_url=get_cover_url(book.isbn),
    )


@app.route('/author/<int:author_id>')
def author_detail(author_id):
    author = Author.query.get_or_404(author_id)
    books = Book.query.filter_by(author_id=author.id).order_by(Book.title).all()
    return render_template('author_detail.html', author=author, books=books)


@app.route('/author/<int:author_id>/delete', methods=['POST'])
def delete_author(author_id):
    author = Author.query.get_or_404(author_id)
    author_name = author.name

    db.session.delete(author)
    db.session.commit()
    flash(f"Author '{author_name}' and their books were deleted successfully.")
    return redirect(url_for('home'))


@app.route('/recommendation', methods=['GET', 'POST'])
def recommendation():
    recommendation_text = None
    error_message = None

    if request.method == 'POST':
        recommendation_text, error_message = get_book_recommendation()

    return render_template(
        'recommendation.html',
        recommendation_text=recommendation_text,
        error_message=error_message,
    )


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    author = book.author
    title = book.title
    author_has_other_books = (
        author
        and Book.query.filter(Book.author_id == author.id, Book.id != book.id).count() > 0
    )

    db.session.delete(book)

    if author and not author_has_other_books:
        db.session.delete(author)

    db.session.commit()
    flash(f"Book '{title}' was deleted successfully.")
    return redirect(url_for('home'))


@app.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    authors = Author.query.order_by(Author.name).all()

    if request.method == 'POST':
        old_author = book.author
        old_author_id = book.author_id

        book.isbn = request.form['isbn']
        book.title = request.form['title']
        book.date_published = parse_optional_date(request.form.get('date_published'))
        book.rating = parse_optional_rating(request.form.get('rating'))
        book.author_id = int(request.form['author_id'])

        if old_author and old_author_id != book.author_id:
            old_author_has_books = Book.query.filter(
                Book.author_id == old_author.id,
                Book.id != book.id,
            ).count() > 0
            if not old_author_has_books:
                db.session.delete(old_author)

        db.session.commit()
        flash(f"Book '{book.title}' was updated successfully.")
        return redirect(url_for('edit_book', book_id=book.id))

    return render_template('edit_book.html', book=book, authors=authors)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    success_message = None

    if request.method == 'POST':
        author = Author(
            name=request.form['name'],
            birth_date=parse_optional_date(request.form.get('birth_date')),
            date_of_death=parse_optional_date(request.form.get('date_of_death')),
        )
        db.session.add(author)
        db.session.commit()
        success_message = f"Author '{author.name}' was added successfully."

    return render_template('add_author.html', success_message=success_message)


@app.route('/api/books/lookup')
def lookup_book():
    isbn = request.args.get('isbn', '')
    book_data, error_message = lookup_book_by_isbn(isbn)
    status_code = 404 if book_data and error_message else 400 if error_message else 200

    return jsonify({
        'book': book_data,
        'error': error_message,
    }), status_code


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    success_message = None
    authors = Author.query.order_by(Author.name).all()

    if request.method == 'POST':
        book = Book(
            isbn=request.form['isbn'],
            title=request.form['title'],
            date_published=parse_optional_date(request.form.get('date_published')),
            rating=parse_optional_rating(request.form.get('rating')),
            author_id=int(request.form['author_id']),
        )
        db.session.add(book)
        db.session.commit()
        success_message = f"Book '{book.title}' was added successfully."

    return render_template(
        'add_book.html',
        authors=authors,
        success_message=success_message,
    )
