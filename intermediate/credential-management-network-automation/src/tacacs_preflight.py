# src/tacacs_preflight.py
from tacacs_plus.client import TACACSClient
from tacacs_plus.flags import TAC_PLUS_AUTHEN_TYPE_PAP


class ServiceAccountError(Exception):
    pass


def verify_service_account(username, password, server, shared_secret):
    """
    Check the automation account against TACACS+ before a run.

    Args:
        username: Service account username
        password: Service account password (e.g. from Vault)
        server: TACACS+ server address
        shared_secret: TACACS+ key shared with the server

    Raises:
        ServiceAccountError: If the account can't log in or get a shell
    """
    client = TACACSClient(server, 49, shared_secret, timeout=5)

    # Authentication: is the password right, and is the account enabled?
    authen = client.authenticate(
        username, password, authen_type=TAC_PLUS_AUTHEN_TYPE_PAP
    )
    if not authen.valid:
        raise ServiceAccountError(f"TACACS+ rejected the login for {username}")

    # Authorisation: the same "service=shell" check a device makes before
    # giving the user an exec session. Arguments are bytes.
    author = client.authorize(
        username, arguments=[b"service=shell"], authen_type=TAC_PLUS_AUTHEN_TYPE_PAP
    )
    if not author.valid:
        raise ServiceAccountError(f"{username} is not authorised for a shell")
