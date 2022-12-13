from ctypes import cast
from decouple import config

SERVER_IP = config("SERVER_IP", cast=str)
PORT = config("PORT", cast=str)
SERVER_URL = f"http://{SERVER_IP}:{PORT}"

BASE_URL = 'https://www.googleapis.com/books/v1/volumes'
SEARCH_URL = BASE_URL + "?{}"
BOOK_URL = BASE_URL + '/{}'
NUM_SEARCH_RESULTS = 8
NOT_FOUND = 'Not found'
DEFAULT_LANGUAGE = "en"
SLEEP_BETWEEN_REQUESTS = 2