import unittest
from flask import url_for
from rsshub import create_app


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app('testing')
        self.context = app.test_request_context()
        self.context.push()
        self.client = app.test_client()
        self.runner = app.test_cli_runner()

    def tearDown(self):
        self.context.pop()
