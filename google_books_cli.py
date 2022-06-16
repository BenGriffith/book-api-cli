from time import sleep
from typing import Optional

import typer

from config import NUM_SEARCH_RESULTS, SLEEP_BETWEEN_REQUESTS, NEGATIVE_REPLY
from user import create_user, user_auth
from books import (
    search_phrase_request, 
    process_search_phrase_response, 
    print_books_to_create, 
    choose_books_to_create, 
    books_to_create_request, 
    continue_creating_books
    )
    

def main(
        new_user: Optional[bool] = typer.Option(default=False, prompt=True),
        username: Optional[str] = typer.Option(default=None, prompt=True), 
        password: Optional[str] = typer.Option(default=None, prompt=True, confirmation_prompt=True, hide_input=True), 
        search_phrase: Optional[str] = typer.Option(default=None)):
    
    is_user_logged_in = False

    if new_user:
        email = typer.prompt("What is your email address?")
        first_name = typer.prompt("What is your first name?")
        last_name = typer.prompt("What is your last name?")

        create_user(username, email, first_name, last_name, password)

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

            message_books_to_create = typer.style("What books would you like to create?", fg=typer.colors.GREEN)
            books_to_create_prompt = typer.prompt(message_books_to_create, type=set)
    
            user_selected_books = choose_books_to_create(books_to_create_prompt)
            
            books_to_create_request(books_to_create_dict, user_selected_books, access_token)

            search_index += NUM_SEARCH_RESULTS
            sleep(SLEEP_BETWEEN_REQUESTS)

            message_continue_creating_books = typer.style("Would you like to continue creating books?", fg=typer.colors.GREEN)
            continue_creating_books_prompt = typer.prompt(message_continue_creating_books, default="yes", type=str)

            continue_prompt = continue_creating_books(continue_creating_books_prompt)
            if continue_prompt in NEGATIVE_REPLY:
                break

            search_phrase_response = search_phrase_request(search_phrase, search_index)

    
if __name__ == "__main__":
    typer.run(main)