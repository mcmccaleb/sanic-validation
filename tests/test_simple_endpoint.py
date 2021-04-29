import unittest

from cerberus import Validator
from sanic import Sanic
from sanic.response import json

from sanic_validation import validate_json, validate_args


class TestSimpleEndpointJsonValidation(unittest.TestCase):
    _endpoint_schema = {'name': {'type': 'string', 'required': True}}
    _app = None

    def setUp(self):
        self._app = Sanic('test-app')

        @self._app.route('/', methods=["POST"])
        @validate_json(self._endpoint_schema)
        async def _simple_endpoint(request):
            return json({'status': 'ok'})

    def test_should_fail_validation(self):
        _, response = self._app.test_client.post('/', json={})
        self.assertEqual(response.status, 400)
        self.assertEqual(response.json['error']['message'],
                         'Validation failed.')
        self.assertEqual(response.json['error']['type'], 'validation_failed')

    def test_should_pass_validation(self):
        _, response = self._app.test_client.post('/', json={'name': 'john'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.json['status'], 'ok')


class TestSimpleEndpointArgsValidation(unittest.TestCase):
    _endpoint_schema = {'name': {'type': 'string', 'required': True}}
    _app = None

    def setUp(self):
        self._app = Sanic('test-app')

        @self._app.route('/')
        @validate_args(self._endpoint_schema)
        async def _simple_endpoint(request):
            return json({'status': 'ok'})

    def test_should_fail_for_empty_validation(self):
        _, response = self._app.test_client.get('/')
        self.assertEqual(response.status, 400)
        self.assertEqual(response.json['error']['message'],
                         'Validation failed.')
        self.assertEqual(response.json['error']['type'], 'validation_failed')

    def test_should_pass_validation(self):
        _, response = self._app.test_client.get('/', params={'name': 'john'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.json['status'], 'ok')


class TestSimpleEndpointArgsTypeNormalizationValidation(unittest.TestCase):
    _endpoint_schema = {
        'val': {'type': 'integer', 'required': True, 'coerce': int}}
    _app = None

    def setUp(self):
        self._app = Sanic('test-app')

        @self._app.route('/')
        @validate_args(self._endpoint_schema)
        async def _simple_endpoint(request):
            return json({'status': 'ok'})

    def test_should_fail_for_empty_validation(self):
        _, response = self._app.test_client.get('/')
        self.assertEqual(response.status, 400)
        self.assertEqual(response.json['error']['message'],
                         'Validation failed.')
        self.assertEqual(response.json['error']['type'], 'validation_failed')

    def test_should_pass_with_string_validation(self):
        _, response = self._app.test_client.get('/', params={'val': '420'})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.json['status'], 'ok')

    def test_should_pass_with_int_validation(self):
        _, response = self._app.test_client.get('/', params={'val': 420})
        self.assertEqual(response.status, 200)
        self.assertEqual(response.json['status'], 'ok')

    def test_should_fail_for_wrong_type_validation(self):
        _, response = self._app.test_client.get('/', params={'val': 'True'})
        self.assertEqual(response.json['error']['message'],
                         'Validation failed.')
        self.assertEqual(response.json['error']['type'], 'validation_failed')


class TestSimpleEndpointSubclassValidator(unittest.TestCase):
    _endpoint_schema = {
        'name': {'type': 'string', 'required': True},
        'reversed': {'type': 'string', 'required': True, 'reversed_string': 'name'},
    }
    _app = None

    class ExtendedValidator(Validator):
        def _validate_reversed_string(self, test, field, _value):
            print(test, field, _value)
            reversed_field = self.document.get('name')
            if reversed_field != _value[::-1]:
                self._error(field, "field is not reversed")

    def setUp(self):
        self._app = Sanic('test-app')

        @self._app.route('/', methods=["POST"])
        @validate_json(self._endpoint_schema, validator_class=ExtendedValidator)
        async def _simple_endpoint(request):
            return json({'status': 'ok'})

    def test_should_fail_validation(self):
        _, response = self._app.test_client.post(
            '/', json={'name': 'john', 'reversed': 'john'}
        )
        self.assertEqual(response.status, 400)
        self.assertEqual(response.json['error']['message'], 'Validation failed.')
        self.assertEqual(response.json['error']['type'], 'validation_failed')

    def test_should_pass_validation(self):
        _, response = self._app.test_client.post(
            '/', json={'name': 'john', 'reversed': 'nhoj'}
        )
        self.assertEqual(response.status, 200)
        self.assertEqual(response.json['status'], 'ok')
