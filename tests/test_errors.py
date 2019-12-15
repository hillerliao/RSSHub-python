from flask import current_app, abort
from tests.base import BaseTestCase


class ErrorsTestCase(BaseTestCase):
    def test_400(self):
        @current_app.route('/400')
        def bad_request():
            abort(400)

        response = self.client.get('/400')
        data = response.get_data(as_text=True)
        self.assertIn('400 Bad Request', data)
        self.assertEqual(response.status_code, 400)

    def test_404(self):
        response = self.client.get('/nothing')
        data = response.get_data(as_text=True)
        self.assertIn('404 Not Found', data)
        self.assertEqual(response.status_code, 404)

    def test_500(self):
        @current_app.route('/500')
        def internal_server_error_for_test():
            abort(500)

        response = self.client.get('/500')
        data = response.get_data(as_text=True)
        self.assertIn('服务器出错', data)
        self.assertEqual(response.status_code, 500)
