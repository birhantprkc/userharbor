from userharbor.interfaces import UserStore, UserToken

from ._support import (
    EXPIRES_AT,
    NEW_EXPIRES_AT,
    assert_token,
    create_user,
)


def test_add_session_persists_session_token(user_store: UserStore) -> None:
    create_user(user_store)

    user_store.add_session(UserToken("alice", "session-token-hash", EXPIRES_AT))

    assert_token(
        user_store.get_session("session-token-hash"),
        username="alice",
        token_hash="session-token-hash",
    )


def test_get_session_returns_token(user_store: UserStore) -> None:
    create_user(user_store)
    user_store.add_session(UserToken("alice", "session-token-hash", EXPIRES_AT))

    assert_token(
        user_store.get_session("session-token-hash"),
        username="alice",
        token_hash="session-token-hash",
    )


def test_get_session_returns_none_for_missing_token(user_store: UserStore) -> None:
    assert user_store.get_session("missing") is None


def test_refresh_session_updates_expiration(user_store: UserStore) -> None:
    create_user(user_store)
    user_store.add_session(UserToken("alice", "session-token-hash", EXPIRES_AT))

    user_store.refresh_session("session-token-hash", NEW_EXPIRES_AT)

    assert_token(
        user_store.get_session("session-token-hash"),
        username="alice",
        token_hash="session-token-hash",
        expires_at=NEW_EXPIRES_AT,
    )


def test_refresh_session_ignores_missing_token(user_store: UserStore) -> None:
    user_store.refresh_session("missing", NEW_EXPIRES_AT)

    assert user_store.get_session("missing") is None


def test_remove_all_sessions_deletes_only_users_sessions(
    user_store: UserStore,
) -> None:
    create_user(user_store)
    create_user(user_store, username="bob", email="bob@example.com")
    user_store.add_session(UserToken("alice", "alice-session-1", EXPIRES_AT))
    user_store.add_session(UserToken("alice", "alice-session-2", EXPIRES_AT))
    user_store.add_session(UserToken("bob", "bob-session", EXPIRES_AT))

    user_store.remove_all_sessions("alice")

    assert user_store.get_session("alice-session-1") is None
    assert user_store.get_session("alice-session-2") is None
    assert_token(
        user_store.get_session("bob-session"),
        username="bob",
        token_hash="bob-session",
    )


def test_remove_session_deletes_token(user_store: UserStore) -> None:
    create_user(user_store)
    user_store.add_session(UserToken("alice", "session-token-hash", EXPIRES_AT))

    user_store.remove_session("session-token-hash")

    assert user_store.get_session("session-token-hash") is None


def test_remove_session_ignores_missing_token(user_store: UserStore) -> None:
    user_store.remove_session("missing")

    assert user_store.get_session("missing") is None


__all__ = [name for name in globals() if name.startswith("test_")]
