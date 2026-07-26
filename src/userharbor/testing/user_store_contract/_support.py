from datetime import datetime

from userharbor.interfaces import CreateUserRequest, UserStore, UserToken

EXPIRES_AT = datetime(2030, 1, 1, 12, 0, 0)
NEW_EXPIRES_AT = datetime(2030, 1, 2, 12, 0, 0)


class AbortTransaction(Exception):
    pass


def create_user_request(
    username: str = "alice",
    email: str = "alice@example.com",
    password_hash: str = "password-hash",
    verification_token_hash: str | None = None,
) -> CreateUserRequest:
    return CreateUserRequest(
        username=username,
        email=email,
        password_hash=password_hash,
        verification_token_hash=(
            verification_token_hash or f"{username}-verification-token-hash"
        ),
        expires_at=EXPIRES_AT,
    )


def create_user(
    user_store: UserStore,
    username: str = "alice",
    email: str = "alice@example.com",
) -> None:
    user_store.create_user(
        create_user_request(
            username=username,
            email=email,
        )
    )


def assert_token(
    token: UserToken | None,
    *,
    username: str,
    token_hash: str,
    expires_at: datetime = EXPIRES_AT,
) -> None:
    assert token is not None
    assert token.username == username
    assert token.token_hash == token_hash
    assert token.expires_at == expires_at
