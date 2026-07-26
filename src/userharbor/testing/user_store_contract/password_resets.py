from userharbor.interfaces import UserStore, UserToken

from ._support import (
    EXPIRES_AT,
    NEW_EXPIRES_AT,
    assert_token,
    create_user,
)


def test_get_password_reset_returns_token(user_store: UserStore) -> None:
    create_user(user_store)
    reset = UserToken("alice", "reset-token-hash", EXPIRES_AT)
    user_store.set_password_reset(reset)

    assert_token(
        user_store.get_password_reset("reset-token-hash"),
        username="alice",
        token_hash="reset-token-hash",
    )


def test_get_password_reset_returns_none_for_missing_token(
    user_store: UserStore,
) -> None:
    assert user_store.get_password_reset("missing") is None


def test_set_password_reset_persists_token(user_store: UserStore) -> None:
    create_user(user_store)

    user_store.set_password_reset(
        UserToken("alice", "reset-token-hash", NEW_EXPIRES_AT)
    )

    assert_token(
        user_store.get_password_reset("reset-token-hash"),
        username="alice",
        token_hash="reset-token-hash",
        expires_at=NEW_EXPIRES_AT,
    )


def test_set_password_reset_replaces_previous_token(
    user_store: UserStore,
) -> None:
    create_user(user_store)
    user_store.set_password_reset(
        UserToken("alice", "old-reset-token-hash", EXPIRES_AT)
    )

    user_store.set_password_reset(
        UserToken("alice", "new-reset-token-hash", NEW_EXPIRES_AT)
    )

    assert user_store.get_password_reset("old-reset-token-hash") is None


def test_remove_password_reset_deletes_token(user_store: UserStore) -> None:
    create_user(user_store)
    user_store.set_password_reset(
        UserToken("alice", "reset-token-hash", EXPIRES_AT)
    )

    user_store.remove_password_reset("reset-token-hash")

    assert user_store.get_password_reset("reset-token-hash") is None


def test_remove_password_reset_ignores_missing_token(
    user_store: UserStore,
) -> None:
    user_store.remove_password_reset("missing")

    assert user_store.get_password_reset("missing") is None


__all__ = [name for name in globals() if name.startswith("test_")]
