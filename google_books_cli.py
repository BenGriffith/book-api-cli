import urllib.parse
from time import sleep
from typing import Optional

import typer
import requests
from decouple import config
from fastapi import status

SERVER_IP = config("SERVER_IP")
PORT = config("PORT")
SERVER_URL = f"http://{SERVER_IP}:{PORT}"


BASE_URL = 'https://www.googleapis.com/books/v1/volumes'
SEARCH_URL = BASE_URL + "?{}"
BOOK_URL = BASE_URL + '/{}'
SEARCH_RESULTS = 8
NOT_FOUND = 'Not found'
DEFAULT_LANGUAGE = "en"
SLEEP_BETWEEN_REQUESTS = 2


def create_user(username, password):

    user_email = typer.prompt("What is your email address?")
    user_first_name = typer.prompt("What is your first name?")
    user_last_name = typer.prompt("What is your last name?")

    user = {
        "username": username,
        "email": user_email,
        "first_name": user_first_name,
        "last_name": user_last_name,
        "password": password,
    }

    response = requests.post(f"{SERVER_URL}/users", json=user)

    if response.status_code == status.HTTP_201_CREATED:
        message_user_created = typer.style(f"Congratulations! {username} has been created!", fg=typer.colors.GREEN)
        typer.echo(message_user_created)
        return True

    typer.echo(f"{response.json()['detail']}.")


def user_auth(username: str, password: str):

    response = requests.post(
            f"{SERVER_URL}/token",
            data={"username": username, "password": password},
            headers={"content-type": "application/x-www-form-urlencoded"}
            )

    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        typer.echo(f"{response.json()['detail']}. Please try again.")
        return None, None
    else:
        access_token = {"Authorization": f"Bearer {response.json()['access_token']}"}
        user = requests.get(f"{SERVER_URL}/users/me", headers=access_token)

    return user, access_token


def search_phrase_request(search_phrase, search_index):

    params = {
        "q": search_phrase,
        "startIndex": search_index,
        "maxResults": SEARCH_RESULTS,
        "langRestrict": DEFAULT_LANGUAGE
    }

    query_string = urllib.parse.urlencode(params)
    query = SEARCH_URL.format(query_string)
    response = requests.get(query).json()

    return response


def book_request(book_id):
    query = BOOK_URL.format(book_id)
    return requests.get(query).json()


def print_books_to_create(books):
    books_to_create = {}
    for i, book in enumerate(books, start=1):
        message_book_details = typer.style(f"{i}. {book.get('title')}, Written By {book.get('authors')}", fg=typer.colors.MAGENTA)
        typer.echo(message_book_details)
        books_to_create[str(i)] = book
    return books_to_create


def _filter_non_digit_books(books):
    return  [book for book in books if str(book).isdigit()]


def _has_books_outside_of_maxrange(books) -> list[str]:
    return [idx for idx in books if int(idx) > SEARCH_RESULTS]


class WrongBookSelectedException(Exception):
    pass


def choose_books_to_create(books):
    books_to_create = _filter_non_digit_books(books)
    out_of_range_digits = _has_books_outside_of_maxrange(books_to_create)
    if out_of_range_digits:
        error = f"{', '.join(out_of_range_digits)} are out of range, please try again."
        message_value_error = typer.style(error, fg=typer.colors.RED)
        typer.echo(message_value_error)
        raise WrongBookSelectedException(error)

    return books_to_create


def process_search_phrase_response(response, user):

    books = []
    for book in response["items"]:

        book_id = book.get("id")
        book_response = book_request(book_id)

        book_info = book_response.get("volumeInfo")
        book_title = book_info.get("title")
        book_authors = NOT_FOUND if book_info.get("authors", NOT_FOUND) == NOT_FOUND else ", ".join(book_info.get("authors"))
        #book_authors =
        book_publisher = book_info.get("publisher", NOT_FOUND).strip('"')
        book_published_date = book_info.get("publishedDate", NOT_FOUND)
        book_description = book_info.get("description", NOT_FOUND)
        book_page_count = book_info.get("pageCount", 0)
        book_average_rating = book_info.get("averageRating", 0)
        book_language = book_info.get("language", NOT_FOUND)

        if book_language != DEFAULT_LANGUAGE:
            continue

        user_id = user.json().get("id")

        book_create = {
            "title": book_title,
            "authors": book_authors,
            "publisher": book_publisher,
            "published_date": book_published_date,
            "description": book_description,
            "page_count": book_page_count,
            "average_rating": book_average_rating,
            "google_books_id": book_id,
            "user_id": user_id,
        }

        books.append(book_create)

    return books


def books_to_create_request(books_dict, user_selected_books, access_token):

    for book in user_selected_books:

        if book in books_dict:
            book_response = requests.post(f"{SERVER_URL}/books", json=books_dict[book], headers=access_token)

            if book_response.status_code == status.HTTP_201_CREATED:
                message_book_created = typer.style(f"-> {book}. {books_dict[book]['title']}, By {books_dict[book]['authors']} was created", fg=typer.colors.BLUE)
                typer.echo(message_book_created)
            else:
                message_book_failed = typer.style(f"{book_response.status_code}: {book_response.json()['detail']}", fg=typer.colors.RED)
                typer.echo(message_book_failed)

    return


def continue_creating_books_prompt():
    message_continue_prompt = typer.style("Would you like to continue creating books?", fg=typer.colors.GREEN)
    continue_prompt = typer.prompt(message_continue_prompt, default="yes", type=str)
    continue_prompt = continue_prompt.lower()

    if continue_prompt not in ["y", "yes", "n", "no"]:
        return continue_creating_books_prompt()

    return continue_prompt


def user_logged_in(search_phrase, user, access_token):

    if search_phrase is None:
        message_search_phrase = typer.style("What books would you like to search for?", fg=typer.colors.GREEN)
        search_phrase = typer.prompt(message_search_phrase)

    search_index = 0
    search_phrase_response = search_phrase_request(search_phrase, search_index)

    while True:

        books_to_create = process_search_phrase_response(search_phrase_response, user)

        books_to_create_dict = print_books_to_create(books_to_create)

        while True:
            message_create_prompt = typer.style("What books would you like to create?", fg=typer.colors.GREEN)
            books_selected_by_user = typer.prompt(message_create_prompt, type=str)
            books_to_create = set(books_selected_by_user.split(","))
            try:
                user_selected_books = choose_books_to_create(books_to_create)
                break
            except WrongBookSelectedException as exc:
                print(exc)
                continue

        books_to_create_request(books_to_create_dict, user_selected_books, access_token)

        search_index += SEARCH_RESULTS
        sleep(SLEEP_BETWEEN_REQUESTS)

        continue_prompt = continue_creating_books_prompt()
        if continue_prompt in ["n", "no"]:
            break

        search_phrase_response = search_phrase_request(search_phrase, search_index)

    return


def main(
        new_user: Optional[bool] = typer.Option(default=False, prompt=True),
        username: Optional[str] = typer.Option(default=None, prompt=True),
        password: Optional[str] = typer.Option(default=None, prompt=True, confirmation_prompt=True, hide_input=True),
        search_phrase: Optional[str] = typer.Option(default=None)):

    is_user_logged_in = False
    user_created = False

    if new_user:
        user_created = create_user(username, password)

    # TODO: only repeat pw for signup
    if user_created or (not new_user and (username and password)):
        user, access_token = user_auth(username, password)
        is_user_logged_in = True if user else False

    if is_user_logged_in:
        user_logged_in(search_phrase, user, access_token)


if __name__ == "__main__":
    typer.run(main)
