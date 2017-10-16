import requests
from requests.utils import quote
from flask import Flask, jsonify, abort
from flask import make_response
from flask import request
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

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


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)


@app.route('/')
@auth.login_required
def index():
    return "Hello, %s!" % auth.username()

##########################
# Fun with string API
##########################
RANDOM_WORD_API_PATH = 'http://setgetgo.com/randomword/get.php'
WIKIPEDIA_API_PATH = 'https://en.wikipedia.org/w/api.php'
JOKES_API_PATH = 'http://api.icndb.com/jokes/random'
MICROSOFT_SPELL_CHECK_API_PATH = 'https://api.cognitive.microsoft.com/bing/v5.0/spellcheck'
MISROSOFT_KEY = '46e7afda55eb4d26adf3a72c02b8e1c3'
requested_words = {}


@app.route('/api/v1.0/random_word', methods=['GET'])
@auth.login_required
def get_random_word():
    word = requests.get(RANDOM_WORD_API_PATH).text
    return jsonify({'word': word})


@app.route('/api/v1.0/wikipedia/<word>', methods=['GET'])
@auth.login_required
def get_wiki_article_for_given_word(word):
    if not word:
        return abort(400)

    # Put word into the dictionary of requested words
    if requested_words.get(word) is None:
        requested_words[word] = 0
    requested_words[word] += 1

    params = {
        'format': 'json',
        'action': 'query',
        'prop': 'extracts',
        'titles': quote(word)
    }

    response = requests.get(WIKIPEDIA_API_PATH, params=params)
    article = ''
    for page_id in response.json().get('query', {}).get('pages', []):
        page = response.json()['query']['pages'][page_id]
        if word.lower() == page['title'].lower():
            article = response.json()['query']['pages'][page_id]['extract']

    return jsonify({'article': article})


@app.route('/api/v1.0/most_popular_words/<int:number>', methods=['GET'])
@auth.login_required
def get_most_popular_n_words(number):
    most_popular_words = sorted(requested_words.items(),
                                key=lambda x: x[1],
                                reverse=True)[:number]

    result = []
    for word, request_num in most_popular_words:
        result.append({
            'word': word,
            'requested': request_num
        })
    return jsonify({'words': result})


@app.route('/api/v1.0/jokes', methods=['GET'])
@auth.login_required
def get_joke():
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    if not (first_name or last_name):
        first_name = 'Chuck'
        last_name = 'Norris'

    params = {
        'firstName': first_name,
        'lastName': last_name
    }
    response = requests.get(JOKES_API_PATH, params=params)
    joke = 'No jokes today'
    if response.json().get('value', {}).get('joke'):
        joke = response.json()['value']['joke']

    return jsonify({'joke': joke})


@app.route('/api/v1.0/spell_check', methods=['POST'])
@auth.login_required
def post_spell_check():
    if not request.json:
        abort(400)

    if 'text' not in request.json:
        abort(400)

    text = request.json.get('text')
    params = {
        'mode': 'proof',
        'mkt': 'en-us'
    }
    headers = {'Ocp-Apim-Subscription-Key': MISROSOFT_KEY}
    data = {'text': text}

    response = requests.post(MICROSOFT_SPELL_CHECK_API_PATH,
                             data=data,
                             params=params,
                             headers=headers)

    result = {'tokens': []}
    for token in response.json().get('flaggedTokens', []):
        token_local = {'token': token['token'],
                       'offset': token['offset'],
                       'suggestions': []}
        for suggestion in token.get('suggestions'):
            token_local['suggestions'].append({'suggestion': suggestion['suggestion']})
        result['tokens'].append(token_local)

    return jsonify(result)


if __name__ == '__main__':
    app.run()
