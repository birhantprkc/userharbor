from datetime import timedelta

import pytest
from conftest import SECRET_KEY, VALID_EMAIL, VALID_PASSWORD, VALID_USERNAME

from userharbor.exceptions import InvalidUsernameError, WeakPasswordError
from userharbor.main import UserHarbor
from userharbor.security import verify_password


def test_custom_username_validator_accepts_username_and_is_only_used_for_registration(
    store, email_sender
) -> None:
    validated_usernames = []

    def username_validator(username: str) -> bool:
        validated_usernames.append(username)
        return username == "custom_user"

    userharbor = UserHarbor(
        SECRET_KEY,
        store,
        email_sender,
        timedelta(hours=24),
        timedelta(hours=1),
        timedelta(days=30),
        timedelta(days=7),
        username_validator,
    )

    userharbor.register("custom_user", VALID_EMAIL, VALID_PASSWORD)
    userharbor.roles.create("admin")
    userharbor.grant_role("custom_user", "admin")

    assert userharbor.get_roles("custom_user") == {"admin"}
    assert validated_usernames == ["custom_user"]


def test_custom_username_validator_rejects_default_valid_username(
    store, email_sender
) -> None:
    userharbor = UserHarbor(
        SECRET_KEY,
        store,
        email_sender,
        username_validator=lambda username: False,
    )

    with pytest.raises(InvalidUsernameError, match="Invalid username"):
        userharbor.register(VALID_USERNAME, VALID_EMAIL, VALID_PASSWORD)

    assert store.users == {}
    assert email_sender.sent_verifications == []


def test_custom_password_validator_is_used_for_register_change_and_reset(
    store, email_sender
) -> None:
    accepted_passwords = {"initial", "changed", "reset"}
    userharbor = UserHarbor(
        SECRET_KEY,
        store,
        email_sender,
        password_validator=lambda password: password in accepted_passwords,
    )

    userharbor.register(VALID_USERNAME, VALID_EMAIL, "initial")
    verification_token = email_sender.sent_verifications[-1].verification_token
    userharbor.verify_email(verification_token)
    session_token = userharbor.login(VALID_USERNAME, "initial")

    userharbor.change_password("initial", "changed", session_token)

    assert verify_password("changed", store.users[VALID_USERNAME].password_hash)

    userharbor.send_password_reset(VALID_EMAIL)
    reset_token = email_sender.sent_password_resets[-1].reset_token
    userharbor.reset_password("reset", reset_token)

    assert verify_password("reset", store.users[VALID_USERNAME].password_hash)


def test_custom_password_validator_rejects_default_strong_password(
    store, email_sender
) -> None:
    userharbor = UserHarbor(
        SECRET_KEY,
        store,
        email_sender,
        password_validator=lambda password: False,
    )

    with pytest.raises(WeakPasswordError, match="Weak password"):
        userharbor.register(VALID_USERNAME, VALID_EMAIL, VALID_PASSWORD)

    assert store.users == {}
    assert email_sender.sent_verifications == []
