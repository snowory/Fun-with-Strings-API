import base64
import json
import unittest
from requests.utils import quote

import requests_mock

from app import (
    app, USERNAME, PASSWORD,
    RANDOM_WORD_API_PATH, WIKIPEDIA_API_PATH, JOKES_API_PATH
)


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def open_with_auth(self, url, method='GET', username=USERNAME, password=PASSWORD):
        auth = base64.b64encode((username + ':' + password).encode()).decode()
        return self.client.open(url,
                                method=method,
                                headers={'Authorization': 'Basic ' + auth})

    @requests_mock.mock()
    def test_random_word(self, mock):
        mock.get(RANDOM_WORD_API_PATH, text='data')
        response = self.open_with_auth('/api/v1.0/random_word')
        self.assertEqual(json.loads(response.get_data().decode()),
                         {'word': 'data'})

    @requests_mock.mock()
    def test_get_wiki_article_for_given_word(self, mock):
        url = WIKIPEDIA_API_PATH
        mock.get(url, text=json.dumps({
            'query': {
                'pages': {
                    '21721040': {
                        'pageid': 21721040,
                        'ns': 0,
                        'title': 'W3C',
                        'extract': 'World Wide Web Consortium'
                    }}}}))

        response = self.open_with_auth('/api/v1.0/wikipedia/W3C')
        self.assertEqual(json.loads(response.get_data().decode()),
                         {'article': 'World Wide Web Consortium'})

    @requests_mock.mock()
    def test_get_most_popular_n_words(self, mock):
        url = WIKIPEDIA_API_PATH
        mock.get(url, text=json.dumps({
            'query': {
                'pages': {
                    '21721040': {
                        'pageid': 21721040,
                        'ns': 0,
                        'title': 'Python_(programming_language)',
                        'extract': 'Python is a widely used high-level programming language for general-purpose programming, created by Guido van Rossum and first released in 1991'
                    }}}}))
        response = self.open_with_auth('/api/v1.0/wikipedia/Python_(programming_language)')

        mock.get(url, text=json.dumps({
            'query': {
                'pages': {
                    '21721040': {
                        'pageid': 21721040,
                        'ns': 0,
                        'title': 'W3C',
                        'extract': 'World Wide Web Consortium'
                    }}}}))
        response = self.open_with_auth('/api/v1.0/wikipedia/W3C')
        response = self.open_with_auth('/api/v1.0/wikipedia/W3C')

        response = self.open_with_auth('/api/v1.0/most_popular_words/5')
        self.assertEqual(json.loads(response.get_data().decode()),
                         {'words': [{'word': 'W3C', 'requested': 2},
                                    {'word': 'Python_(programming_language)', 'requested': 1}]})

    @requests_mock.mock()
    def test_get_joke(self, mock):
        mock.get(JOKES_API_PATH, text=json.dumps({
            'type': "success",
            'value': {
                'id': 13,
                'joke': 'Bruce Willis once challenged Lance Armstrong in a &quot;Who has more testicles?&quot; contest. Bruce Willis won by 5.',
                'categories': [
                    'explicit'
                ]}}))
        response = self.open_with_auth('/api/v1.0/jokes?first_name=Bruce&last_name=Willis')
        self.assertEqual(json.loads(response.get_data().decode()),
                         {'joke': 'Bruce Willis once challenged Lance Armstrong in a &quot;Who has more testicles?&quot; contest. Bruce Willis won by 5.'})

    def test_get_spell_check(self):
        response = self.open_with_auth('/api/v1.0/spell_check?string=' + quote('Miszpelled string'))
        self.assertEqual(json.loads(response.get_data().decode()),
                         {'correct': True})

if __name__ == '__main__':
    unittest.main()
