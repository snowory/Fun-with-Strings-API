Fun with Strings API

## What to do
We are running a service which allows to have a lot of fun with strings.
To gain more customers we want to create an API to allow others to integrate it in their own applications.

The service supports following operations on strings which we want to expose over a RESTful API:
  - get a random word (via Public API http://www.setgetgo.com/randomword/)
  - return content of Wikipedia article about given word
(https://www.mediawiki.org/wiki/API:Main_page)
  - collect statistic for most popular words submitted to previous operation and return top N, where N is provided by user
  - (optional) given a first and/or a last name as parameter, return a random joke from external API (http://www.icndb.com/api/),
    if no name is provided, a Chuck Norris joke is returned
  - (optional) perform a spell check on a given string via calling some external API for spell checking

Scope of the task:
  - provide the implementation for the operations on strings
  - create API endpoint(s) to expose all the operations
  - design corresponding request/response format (XML, JSON etc.)
  - it is enough to use simple data structure for statistic collection, no need to involve any data-store
  - API should handle errors properly and return meaningful response to the user
  - (optional) user authorization for our API

No frameworks are allowed except for flask (http://flask.pocoo.org/) and requests (http://docs.python-requests.org/en/master/) libraries

## About the implementation

Python 3.4.3 is used.

How to start:
```
python app.py --port=5000 --host='127.0.0.1'
```
