import pytest

from userharbor.interfaces import UserStore, UserToken

from ._support import AbortTransaction, EXPIRES_AT, create_user_request


def test_transaction_commits_all_operations_on_success(
    user_store: UserStore,
) -> None:
    with user_store.transaction():
        user_store.create_user(create_user_request())
        user_store.set_user_verified("alice")
        user_store.add_session(
            UserToken("alice", "session-token-hash", EXPIRES_AT)
        )

    user = user_store.get_user_by_username("alice")
    assert user is not None
    assert user.verified is True
    assert user_store.get_session("session-token-hash") is not None


def test_transaction_rolls_back_all_operations_on_error(
    user_store: UserStore,
) -> None:
    with pytest.raises(AbortTransaction):
        with user_store.transaction():
            user_store.create_user(create_user_request())
            user_store.add_session(
                UserToken("alice", "session-token-hash", EXPIRES_AT)
            )
            raise AbortTransaction

    assert user_store.get_user_by_username("alice") is None
    assert user_store.get_email_verification(
        "alice-verification-token-hash"
    ) is None
    assert user_store.get_session("session-token-hash") is None


def test_nested_transaction_uses_outer_transaction(user_store: UserStore) -> None:
    with user_store.transaction():
        user_store.create_user(create_user_request())
        with user_store.transaction():
            user_store.add_session(
                UserToken("alice", "session-token-hash", EXPIRES_AT)
            )

    assert user_store.get_user_by_username("alice") is not None
    assert user_store.get_session("session-token-hash") is not None


def test_delete_user_rolls_back_user_tokens_and_roles(user_store: UserStore) -> None:
    user_store.create_user(create_user_request())
    user_store.add_session(UserToken("alice", "session-token-hash", EXPIRES_AT))
    user_store.set_password_reset(UserToken("alice", "reset-token-hash", EXPIRES_AT))
    user_store.create_role("admin")
    user_store.grant_role_to_user("alice", "admin")

    with pytest.raises(AbortTransaction):
        with user_store.transaction():
            user_store.delete_user("alice")
            raise AbortTransaction

    assert user_store.get_user_by_username("alice") is not None
    assert user_store.get_email_verification("alice-verification-token-hash") is not None
    assert user_store.get_session("session-token-hash") is not None
    assert user_store.get_password_reset("reset-token-hash") is not None
    assert user_store.get_user_roles("alice") == {"admin"}


def test_transaction_context_is_reset_after_rollback(
    user_store: UserStore,
) -> None:
    with pytest.raises(AbortTransaction):
        with user_store.transaction():
            user_store.create_user(create_user_request())
            raise AbortTransaction

    user_store.create_user(create_user_request())

    assert user_store.get_user_by_username("alice") is not None


__all__ = [name for name in globals() if name.startswith("test_")]
