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
SEARCH_RESULTS = 10
NOT_FOUND = 'Not found'
DEFAULT_LANGUAGE = "en"
MAX_LOAD = 1000
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
        typer.echo(f"Congratulations! {username} has been created!")
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


def google_books_request(user_input, search_index):

    params = {
        "q": user_input,
        "startIndex": search_index,
        "maxResults": SEARCH_RESULTS,
        "langRestrict": DEFAULT_LANGUAGE
    }

    query_string = urllib.parse.urlencode(params)
    query = SEARCH_URL.format(query_string)
    response = requests.get(query).json()

    return response


def google_book_query(book_id):
    query = BOOK_URL.format(book_id)
    return requests.get(query).json()


def google_books_output(books):
    books_dict = {}
    for i, book in enumerate(books, start=1):
        print(f"{i}. {book.get('title')}, Written By {book.get('authors')}")
        books_dict[str(i)] = book
        #books_dict[i] = book
    return books_dict


def google_books_to_create():
    books_to_create = typer.prompt(f"What books would you like to create?", type=set)
    books_to_create = sorted([book for book in books_to_create if book != " "])
    try:
        validate_books(books_to_create)
    except ValueError:
        print("Invalid value. Please try again.")
        return google_books_to_create()
    return books_to_create


def validate_books(books):
    for book in books:
        try:
            book = int(book)
        except ValueError:
            raise
        
        if book > SEARCH_RESULTS:
            raise ValueError()
        

def google_books(response, user):

    books = []
    for google_book in response["items"]:

        book_id = google_book.get("id")
        google_book_response = google_book_query(book_id)

        book_info = google_book_response.get("volumeInfo")
        book_title = book_info.get("title")
        book_authors = ", ".join(book_info.get("authors", NOT_FOUND))
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


def google_books_to_create_request(books_final, books, access_token, books_loaded):

    for book in books:

        if book in books_final:
            # print(books_final["1"])
            # print(books_final[book])
            book_response = requests.post(f"{SERVER_URL}/books", json=books_final[book], headers=access_token)

            if book_response.status_code == status.HTTP_201_CREATED:
                books_loaded += 1
                print(f"{books_loaded}. {books_final[book]['title']}, By {books_final[book]['authors']}")
            else:
                print(book_response.json())
    
    return books_loaded
    

def main(
        new_user: Optional[bool] = typer.Option(default=False, prompt=True),
        username: Optional[str] = typer.Option(default=None, prompt=True), 
        password: Optional[str] = typer.Option(default=None, prompt=True, confirmation_prompt=True, hide_input=True), 
        search: Optional[str] = typer.Option(default=None)):
    
    user = False
    user_created = False
    user_input = search

    if new_user:
        user_created = create_user(username, password)

    if user_created or (not new_user and (username and password)):
        user, access_token = user_auth(username, password)

    if user:

        if search is None:
            user_input = typer.prompt("What books would you like to search for?")

        search_index = 0
        books_loaded = 0
        stop_load = False

        google_books_response = google_books_request(user_input, search_index)

        while True:

            google_books_retrieved = google_books(google_books_response, user)

            books_dict = google_books_output(google_books_retrieved)
            #print(books_dict)

            google_books_to_create_final = google_books_to_create()
            print(google_books_to_create_final)
            
            google_books_to_create_request(books_dict, google_books_to_create_final, access_token, books_loaded)

            if books_loaded >= MAX_LOAD:
                stop_load = True
                break

            search_index += SEARCH_RESULTS
            sleep(SLEEP_BETWEEN_REQUESTS)

            google_books_response = google_books_request(user_input, search_index)

        if stop_load:
            typer.echo(f"All done! {books_loaded} books were created.")

    
if __name__ == "__main__":
    typer.run(main)
    # a = typer.prompt("Test", type=set)
    # print(sorted([b for b in a if b != " "]))
