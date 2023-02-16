from ctypes import cast
from decouple import config

SERVER_IP = config("SERVER_IP", cast=str)
SERVER_URL = f"https://{SERVER_IP}"

BASE_URL = 'https://www.googleapis.com/books/v1/volumes'
SEARCH_URL = BASE_URL + "?{}"
BOOK_URL = BASE_URL + '/{}'
NUM_SEARCH_RESULTS = 8
NOT_FOUND = 'Not found'
DEFAULT_LANGUAGE = "en"
SLEEP_BETWEEN_REQUESTS = 2