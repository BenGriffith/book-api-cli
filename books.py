import urllib.parse
import requests
import typer
from fastapi import status

import config

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


def validate_books(books):

    for book_id in books:
        try:
            book_id = int(book_id)
        except ValueError:
            raise
        
        if book_id > config.NUM_SEARCH_RESULTS:
            raise ValueError()


def choose_books_to_create(message):

    books_to_create = sorted([book for book in message if book not in [" ", ","]])

    try:
        validate_books(books_to_create)
    except ValueError:
        message_value_error = typer.style("Invalid value. Please use numeric values from the list of books above.", fg=typer.colors.RED)
        typer.echo(message_value_error)

    return books_to_create
        

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
            book_response = requests.post(f"{config.SERVER_URL}/books", json=books_dict[book], headers=access_token)

            if book_response.status_code == status.HTTP_201_CREATED:
                message_book_created = typer.style(f"-> {book}. {books_dict[book]['title']}, By {books_dict[book]['authors']} was created", fg=typer.colors.CYAN)
                typer.echo(message_book_created)
            else:
                message_book_failed = typer.style(f"{book_response.status_code}: {book_response.json()['detail']}", fg=typer.colors.RED)
                typer.echo(message_book_failed)
    
    return


def continue_creating_books(message):

    continue_prompt = message.lower()

    if continue_prompt not in config.POSITIVE_REPLY + config.NEGATIVE_REPLY:
        return continue_creating_books()
    
    return continue_prompt