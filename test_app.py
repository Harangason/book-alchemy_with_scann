import unittest

from app import app


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


if __name__ == '__main__':
    unittest.main()
