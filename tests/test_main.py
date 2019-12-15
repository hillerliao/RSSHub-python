from flask import url_for
from tests.base import BaseTestCase


class MainTestCase(BaseTestCase):
    def test_index(self):
        response = self.client.get(url_for('main.index'))
        self.assertEqual(response.status_code, 200)
