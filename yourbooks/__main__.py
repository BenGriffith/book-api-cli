from time import sleep
from typing import Optional

import typer

from yourbooks.config import NUM_SEARCH_RESULTS, SLEEP_BETWEEN_REQUESTS
from yourbooks.user import create_user, user_auth
from yourbooks.books import (
    search_phrase_request, 
    process_search_phrase_response, 
    print_books_to_create, 
    choose_books_to_create, 
    books_to_create_request
    )
from yourbooks.exceptions import WrongBookSelectedException


def main(new_user: Optional[bool] = typer.Option(default=False, prompt=True), search_phrase: Optional[str] = typer.Option(default=None)):
    
    is_user_logged_in = False
    username = typer.prompt("Username")

    if new_user:
        password = typer.prompt("Password", confirmation_prompt=True, hide_input=True)
        email = typer.prompt("What is your email address?")
        first_name = typer.prompt("What is your first name?")
        last_name = typer.prompt("What is your last name?")

        username, password = create_user(username, email, first_name, last_name, password)

    else:
        password = typer.prompt("Password", hide_input=True)

    if username and password:
        user, access_token = user_auth(username, password)
        is_user_logged_in = True if user else False

    if is_user_logged_in:

        if search_phrase is None:
            message_search_phrase = typer.style("What books would you like to search for?", fg=typer.colors.GREEN)
            search_phrase = typer.prompt(message_search_phrase)

        search_index = 0
        search_phrase_response = search_phrase_request(search_phrase, search_index)

        while True:

            books_to_create = process_search_phrase_response(search_phrase_response, user)
            books_to_create_dict = print_books_to_create(books_to_create)

            while True:
                message_books_to_create = typer.style("What books would you like to create?", fg=typer.colors.GREEN)
                books_to_create_prompt = typer.prompt(message_books_to_create, type=str)
                books_to_create_set = set(books_to_create_prompt.split(","))

                try:
                    user_selected_books = choose_books_to_create(books_to_create_set)
                    break
                except WrongBookSelectedException as exc:
                    exc_message = typer.style(exc, fg=typer.colors.RED)
                    typer.echo(exc_message)
                    continue
            
            books_to_create_request(books_to_create_dict, user_selected_books, access_token)

            search_index += NUM_SEARCH_RESULTS
            sleep(SLEEP_BETWEEN_REQUESTS)

            message_continue_creating_books = typer.style("Would you like to continue creating books?", fg=typer.colors.GREEN)
            continue_prompt = typer.confirm(message_continue_creating_books)

            if not continue_prompt:
                break

            search_phrase_response = search_phrase_request(search_phrase, search_index)

    
if __name__ == "__main__":
    typer.run(main)