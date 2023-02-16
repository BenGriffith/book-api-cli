import urllib.parse
import requests
import typer
from fastapi import status

from yourbooks import config
from yourbooks.exceptions import WrongBookSelectedException


def search_phrase_request(search_phrase, search_index):

    params = {
        "q": search_phrase,
        "startIndex": search_index,
        "maxResults": config.NUM_SEARCH_RESULTS,
        "langRestrict": config.DEFAULT_LANGUAGE
    }

    query_string = urllib.parse.urlencode(params)
    query = config.SEARCH_URL.format(query_string)
    response = requests.get(query).json()

    return response


def book_request(book_id):

    query = config.BOOK_URL.format(book_id)
    return requests.get(query).json()


def print_books_to_create(books):

    books_to_create = {}

    for i, book in enumerate(books, start=1):
        message_book_details = typer.style(f"{i}. {book.get('title')}, Written By {book.get('authors')}", fg=typer.colors.MAGENTA)
        typer.echo(message_book_details)
        books_to_create[str(i)] = book

    return books_to_create


def _non_digit_books_entries(books):
    return [book for book in books if not str(book).isdigit()]


def _books_outside_of_range(books) -> list[str]:
    return [idx for idx in books if int(idx) > config.NUM_SEARCH_RESULTS]


def choose_books_to_create(books):

    non_digit_entries = _non_digit_books_entries(books)

    if non_digit_entries:
        singular_plural = "are not digits" if len(non_digit_entries) > 1 else "is not a digit"
        error = f"{', '.join(non_digit_entries)} {singular_plural}, please try again."
        raise WrongBookSelectedException(error)

    out_of_range_digits = _books_outside_of_range(books)

    if out_of_range_digits:
        singular_plural = "are" if len(out_of_range_digits) > 1 else "is"
        error = f"{', '.join(out_of_range_digits)} {singular_plural} out of range, please try again."
        raise WrongBookSelectedException(error)

    return sorted([book for book in books])
        

def process_search_phrase_response(response, user):

    books = []
    for book in response["items"]:

        book_id = book.get("id")
        book_response = book_request(book_id)

        book_info = book_response.get("volumeInfo")
        book_title = book_info.get("title")
        book_authors = config.NOT_FOUND if book_info.get("authors", config.NOT_FOUND) == config.NOT_FOUND else ", ".join(book_info.get("authors"))
        book_publisher = book_info.get("publisher", config.NOT_FOUND).strip('"')
        book_published_date = book_info.get("publishedDate", config.NOT_FOUND)
        book_description = book_info.get("description", config.NOT_FOUND)
        book_page_count = book_info.get("pageCount", 0)
        book_average_rating = book_info.get("averageRating", 0)
        book_language = book_info.get("language", config.NOT_FOUND)
        
        if book_language != config.DEFAULT_LANGUAGE:
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
            book_response = requests.post(f"{config.SERVER_URL}/books/", json=books_dict[book], headers=access_token)

            if book_response.status_code == status.HTTP_201_CREATED:
                message_book_created = typer.style(f"CREATED: {book}. {books_dict[book]['title']}, By {books_dict[book]['authors']}", fg=typer.colors.CYAN)
                typer.echo(message_book_created)
            else:
                message_book_failed = typer.style(f"{book_response.status_code}: {book_response.json()['detail']}", fg=typer.colors.RED)
                typer.echo(message_book_failed)
    
    return