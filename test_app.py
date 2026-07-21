import unittest
from unittest.mock import patch

from app import app
from book_lookup import get_cover_url_for_isbn, is_valid_isbn, normalize_barcode


class BookAlchemyTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_page_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Book Library', response.data)

    def test_add_author_page_loads(self):
        response = self.client.get('/add_author')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Author', response.data)

    def test_add_book_page_loads(self):
        response = self.client.get('/add_book')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Book', response.data)
        self.assertIn(b'Buchdaten suchen', response.data)

    def test_isbn_helpers(self):
        self.assertEqual(normalize_barcode('978-0-261-10357-3'), '9780261103573')
        self.assertTrue(is_valid_isbn('9780261103573'))
        self.assertIn('9780261103573-M.jpg', get_cover_url_for_isbn('9780261103573'))

    def test_book_lookup_route(self):
        book_data = {
            'isbn': '9780261103573',
            'title': 'The Lord of the Rings',
            'publish_date': '1954-01-01',
            'authors': ['J. R. R. Tolkien'],
            'cover_url': 'https://covers.openlibrary.org/b/isbn/9780261103573-M.jpg',
        }

        with patch('app.lookup_book_by_isbn', return_value=(book_data, None)):
            response = self.client.get('/api/books/lookup?isbn=9780261103573')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['book']['title'], 'The Lord of the Rings')


if __name__ == '__main__':
    unittest.main()
