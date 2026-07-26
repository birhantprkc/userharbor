from userharbor.interfaces import UserStore, UserToken

from ._support import NEW_EXPIRES_AT, assert_token, create_user


def test_get_email_verification_returns_token(user_store: UserStore) -> None:
    create_user(user_store)

    assert_token(
        user_store.get_email_verification("alice-verification-token-hash"),
        username="alice",
        token_hash="alice-verification-token-hash",
    )


def test_get_email_verification_returns_none_for_missing_token(
    user_store: UserStore,
) -> None:
    assert user_store.get_email_verification("missing") is None


def test_set_email_verification_persists_token(user_store: UserStore) -> None:
    create_user(user_store)

    user_store.set_email_verification(
        UserToken("alice", "new-verification-token", NEW_EXPIRES_AT)
    )

    assert_token(
        user_store.get_email_verification("new-verification-token"),
        username="alice",
        token_hash="new-verification-token",
        expires_at=NEW_EXPIRES_AT,
    )


def test_set_email_verification_replaces_previous_token(
    user_store: UserStore,
) -> None:
    create_user(user_store)

    user_store.set_email_verification(
        UserToken("alice", "new-verification-token", NEW_EXPIRES_AT)
    )

    assert user_store.get_email_verification(
        "alice-verification-token-hash"
    ) is None


def test_remove_email_verification_deletes_token(user_store: UserStore) -> None:
    create_user(user_store)

    user_store.remove_email_verification("alice-verification-token-hash")

    assert user_store.get_email_verification(
        "alice-verification-token-hash"
    ) is None


def test_remove_email_verification_ignores_missing_token(
    user_store: UserStore,
) -> None:
    create_user(user_store)

    user_store.remove_email_verification("missing")

    assert (
        user_store.get_email_verification("alice-verification-token-hash")
        is not None
    )


__all__ = [name for name in globals() if name.startswith("test_")]
