import optparse

import requests
from flask import Flask, jsonify
from flask import make_response
from flask import request
from flask_httpauth import HTTPBasicAuth
from requests.utils import quote, unquote

app = Flask(__name__)
auth = HTTPBasicAuth()

###############################
# Configure the option parser
###############################
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 5000

usage = 'usage: %prog [options]'
parser = optparse.OptionParser(usage)
parser.add_option('', '--host', dest='host', default=DEFAULT_HOST,
                  help='Host.')
parser.add_option('', '--port', dest='port', default=DEFAULT_PORT,
                  help='Port')
(options, args) = parser.parse_args()


#########################
# Authentication
#########################
USERNAME = 'snake'
PASSWORD = 'python'


@auth.get_password
def get_password(username):
    """
    A callback function used to obtain the password for a given user.
    In a more complex system this function could check a user database.
    :param username: name of the user
    :return: password string
    """
    if username == USERNAME:
        return PASSWORD
    return None


#########################
# Error page handlers
#########################
def handle_error(msg, response_code):
    return jsonify({'error': msg}), response_code


@app.errorhandler(ValueError)
def bad_request(e):
    return handle_error(str(e), 400)


@app.errorhandler(Exception)
def unhandled_exception(e):
    return handle_error(str(e), 500)


@app.errorhandler(404)
def page_not_found(e):
    return handle_error(str(e), 404)


@app.errorhandler(500)
def internal_server_error(e):
    return handle_error(str(e), 500)


@auth.error_handler
def unauthorized():
    return handle_error('Unauthorized access', 403)

##########################
# Fun with string API
##########################
RANDOM_WORD_API_PATH = 'http://setgetgo.com/randomword/get.php'
WIKIPEDIA_API_PATH = 'https://en.wikipedia.org/w/api.php'
JOKES_API_PATH = 'http://api.icndb.com/jokes/random'
MICROSOFT_SPELL_CHECK_API_PATH = 'https://api.cognitive.microsoft.com/bing/v5.0/spellcheck'
MISROSOFT_KEY = '46e7afda55eb4d26adf3a72c02b8e1c3'


class FunWithStringsAPI:
    def __init__(self):
        self.requested_words = {}

    def validate_response(self, response):
        if not response:
            raise RuntimeError('Received no response')

        if not response.ok:
            raise RuntimeError('Remote host responded with status: {}'.format(
                response.status_code))

        if not (response.text or response.json()):
            raise RuntimeError('Received empty response body from remote server')

        return response

    def get_response(self, method, url, **kwargs):
        return self.validate_response(requests.request(method, url, **kwargs))

    def get_random_word(self):
        """Get a random word via public API"""
        response = self.get_response('get', RANDOM_WORD_API_PATH)

        return jsonify({'word': response.text})

    def get_wiki_article_for_given_word(self, word):
        """Return content of Wikipedia article about given word"""
        # Collect statistics of requested words
        self.requested_words.setdefault(word, 0)
        self.requested_words[word] += 1

        params = {
            'format': 'json',
            'action': 'query',
            'prop': 'extracts',
            'titles': quote(word)
        }

        response = self.get_response('get', WIKIPEDIA_API_PATH, params=params)

        article = ''
        for page_id in response.json().get('query', {}).get('pages', []):
            page = response.json()['query']['pages'][page_id]
            if word.lower() == page['title'].lower():
                article = response.json()['query']['pages'][page_id]['extract']

        return article.encode()  # utf-8 encoding is used by default

    def get_most_popular_n_words(self, number):
        """Collect statistics for most popular words,
        submitted to previous operation and return top n number,
        where number is provided by user"""
        result = []
        for word in sorted(self.requested_words,
                           key=self.requested_words.get,
                           reverse=True)[:number]:
            result.append({
                'word': word,
                'requested': self.requested_words[word]
            })
        return jsonify({'words': result})

    def get_joke(self):
        """Given a first and/or a last name as parameter,
        return a random joke from external API.
        if no name is provided, a Chuck Norris joke is returned"""
        first_name = request.args.get('first_name')
        last_name = request.args.get('last_name')
        if not (first_name or last_name):
            first_name = 'Chuck'
            last_name = 'Norris'

        params = {
            'firstName': first_name,
            'lastName': last_name
        }
        response = self.get_response('get', JOKES_API_PATH, params=params)
        joke = 'No jokes today'
        if response.json().get('value', {}).get('joke'):
            joke = unquote(response.json()['value']['joke'])

        return jsonify({'joke': joke})

    def post_spell_check(self):
        """Perform a spell check on a given string
        via calling Microsoft Bing spell checking API"""
        if not request.json:
            raise ValueError('Empty request body')

        if 'text' not in request.json:
            raise ValueError('Request body must be as following: {}'.format(
                {'text': 'Read a boook'}
            ))

        text = request.json.get('text')
        params = {
            'mode': 'proof',
            'mkt': 'en-us'
        }
        headers = {'Ocp-Apim-Subscription-Key': MISROSOFT_KEY}
        data = {'text': text}

        response = self.get_response('post', MICROSOFT_SPELL_CHECK_API_PATH,
                                     data=data,
                                     params=params,
                                     headers=headers)

        result = {'tokens': []}
        for token in response.json().get('flaggedTokens', []):
            token_local = {'token': token['token'],
                           'offset': token['offset'],
                           'suggestions': []}
            for suggestion in token.get('suggestions'):
                token_local['suggestions'].append(
                    {'suggestion': suggestion['suggestion']})
            result['tokens'].append(token_local)

        return jsonify(result)


api = FunWithStringsAPI()
login_required = auth.login_required
app.add_url_rule('/api/v1.0/random_word',
                 view_func=login_required(api.get_random_word),
                 methods=['GET'])
app.add_url_rule('/api/v1.0/wikipedia/<word>',
                 view_func=login_required(api.get_wiki_article_for_given_word),
                 methods=['GET'])
app.add_url_rule('/api/v1.0/most_popular_words/<int:number>',
                 view_func=login_required(api.get_most_popular_n_words),
                 methods=['GET'])
app.add_url_rule('/api/v1.0/jokes',
                 view_func=login_required(api.get_joke),
                 methods=['GET'])
app.add_url_rule('/api/v1.0/spell_check',
                 view_func=login_required(api.post_spell_check),
                 methods=['POST'])


if __name__ == '__main__':
    try:
        app.run(host=options.host, port=options.port)
    except Exception as e:
        print('Server failed to start: {}'.format(e))
