import requests
import typer
from fastapi import status

from yourbooks.config import SERVER_URL

def create_user(username, email, first_name, last_name, password):

    user = {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": password,
    }

    response = requests.post(f"{SERVER_URL}/users/", json=user)

    if response.status_code == status.HTTP_201_CREATED:
        message_user_created = typer.style(f"Congratulations! {username} has been created!", fg=typer.colors.GREEN)
        typer.echo(message_user_created)
        return username, password

    message_detail = typer.style(f"{response.json()['detail']}.", fg=typer.colors.RED)
    typer.echo(message_detail)
    return False, False


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