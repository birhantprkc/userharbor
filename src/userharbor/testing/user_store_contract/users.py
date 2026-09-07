import pytest

from userharbor.interfaces import UserStore, UserToken

from ._support import EXPIRES_AT, assert_token, create_user, create_user_request


def test_create_user_persists_user_and_verification_token(
    user_store: UserStore,
) -> None:
    request = create_user_request()

    user_store.create_user(request)

    user = user_store.get_user_by_username("alice")
    assert user is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.verified is False
    assert user_store.get_password_hash("alice") == "password-hash"
    assert_token(
        user_store.get_email_verification("alice-verification-token-hash"),
        username="alice",
        token_hash="alice-verification-token-hash",
    )


def test_create_user_rolls_back_when_database_rejects_row(
    user_store: UserStore,
) -> None:
    create_user(user_store)
    duplicate_email = create_user_request(
        username="bob",
        email="alice@example.com",
        password_hash="other-password-hash",
        verification_token_hash="other-verification-token-hash",
    )

    with pytest.raises(Exception):
        user_store.create_user(duplicate_email)

    assert user_store.get_user_by_username("bob") is None
    assert (
        user_store.get_email_verification("other-verification-token-hash") is None
    )


def test_create_user_rejects_case_insensitive_duplicate_username(
    user_store: UserStore,
) -> None:
    create_user(user_store, username="Straße")
    duplicate_username = create_user_request(
        username="STRASSE",
        email="other@example.com",
        password_hash="other-password-hash",
        verification_token_hash="other-verification-token-hash",
    )

    with pytest.raises(Exception):
        user_store.create_user(duplicate_username)

    user = user_store.get_user_by_username("strasse")
    assert user is not None
    assert user.username == "Straße"
    assert user_store.get_user_by_email("other@example.com") is None
    assert (
        user_store.get_email_verification("other-verification-token-hash") is None
    )


def test_delete_user_removes_user_and_related_tokens(user_store: UserStore) -> None:
    create_user(user_store)
    user_store.add_session(UserToken("alice", "session-token-hash", EXPIRES_AT))
    user_store.set_password_reset(
        UserToken("alice", "reset-token-hash", EXPIRES_AT)
    )

    user_store.delete_user("alice")

    assert user_store.get_user_by_username("alice") is None
    assert user_store.get_email_verification(
        "alice-verification-token-hash"
    ) is None
    assert user_store.get_session("session-token-hash") is None
    assert user_store.get_password_reset("reset-token-hash") is None


def test_delete_user_ignores_missing_user(user_store: UserStore) -> None:
    user_store.delete_user("missing")

    assert user_store.get_user_by_username("missing") is None


def test_recreated_user_does_not_inherit_roles_or_permissions(
    user_store: UserStore,
) -> None:
    create_user(user_store)
    create_user(user_store, username="bob", email="bob@example.com")
    user_store.create_role("admin")
    user_store.create_permission("users.delete")
    user_store.grant_permission_to_role("admin", "users.delete")
    user_store.grant_role_to_user("alice", "admin")
    user_store.grant_role_to_user("bob", "admin")

    user_store.delete_user("alice")
    create_user(user_store, email="new-owner@example.com")

    assert user_store.get_user_roles("alice") == set()
    assert user_store.get_user_permissions("alice") == set()
    assert user_store.get_user_roles("bob") == {"admin"}
    assert user_store.get_user_permissions("bob") == {"users.delete"}
    assert user_store.role_exists("admin")
    assert user_store.permission_exists("users.delete")
    assert user_store.get_role_permissions("admin") == {"users.delete"}


def test_get_password_hash_returns_stored_hash(user_store: UserStore) -> None:
    create_user(user_store)

    assert user_store.get_password_hash("alice") == "password-hash"


def test_get_password_hash_raises_for_missing_user(user_store: UserStore) -> None:
    with pytest.raises(KeyError):
        user_store.get_password_hash("missing")


def test_get_user_by_email_returns_matching_user(user_store: UserStore) -> None:
    create_user(user_store)

    user = user_store.get_user_by_email("alice@example.com")

    assert user is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.verified is False


def test_get_user_by_email_returns_none_for_missing_email(
    user_store: UserStore,
) -> None:
    create_user(user_store)

    assert user_store.get_user_by_email("missing@example.com") is None


def test_get_user_by_username_returns_matching_user(
    user_store: UserStore,
) -> None:
    create_user(user_store)

    user = user_store.get_user_by_username("alice")

    assert user is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.verified is False


@pytest.mark.parametrize(
    ("stored_username", "lookup_username"),
    [
        ("Alice", "aLiCe"),
        ("Straße", "STRASSE"),
    ],
)
def test_get_user_by_username_is_case_insensitive(
    user_store: UserStore,
    stored_username: str,
    lookup_username: str,
) -> None:
    create_user(user_store, username=stored_username)

    user = user_store.get_user_by_username(lookup_username)

    assert user is not None
    assert user.username == stored_username


def test_get_user_by_username_returns_none_for_missing_user(
    user_store: UserStore,
) -> None:
    assert user_store.get_user_by_username("missing") is None


def test_set_password_hash_updates_stored_hash(user_store: UserStore) -> None:
    create_user(user_store)

    user_store.set_password_hash("alice", "new-password-hash")

    assert user_store.get_password_hash("alice") == "new-password-hash"


def test_set_password_hash_raises_for_missing_user(user_store: UserStore) -> None:
    with pytest.raises(KeyError):
        user_store.set_password_hash("missing", "new-password-hash")


def test_set_user_verified_marks_user_as_verified(user_store: UserStore) -> None:
    create_user(user_store)

    user_store.set_user_verified("alice")

    user = user_store.get_user_by_username("alice")
    assert user is not None
    assert user.verified is True


def test_set_user_verified_ignores_missing_user(user_store: UserStore) -> None:
    user_store.set_user_verified("missing")

    assert user_store.get_user_by_username("missing") is None


__all__ = [name for name in globals() if name.startswith("test_")]
