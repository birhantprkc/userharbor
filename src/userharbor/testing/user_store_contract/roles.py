from userharbor.interfaces import UserStore

from ._support import create_user


def test_create_role_persists_role(user_store: UserStore) -> None:
    user_store.create_role("admin")

    assert user_store.role_exists("admin")
    assert user_store.list_roles() == {"admin"}


def test_delete_role_deletes_role_and_assignments(user_store: UserStore) -> None:
    create_user(user_store)
    user_store.create_role("admin")
    user_store.create_permission("users.delete")
    user_store.grant_role_to_user("alice", "admin")
    user_store.grant_permission_to_role("admin", "users.delete")

    user_store.delete_role("admin")

    assert not user_store.role_exists("admin")
    assert user_store.get_user_roles("alice") == set()
    assert user_store.get_role_permissions("admin") == set()


def test_delete_role_ignores_missing_role(user_store: UserStore) -> None:
    user_store.delete_role("missing")

    assert user_store.list_roles() == set()


def test_list_roles_returns_roles(user_store: UserStore) -> None:
    user_store.create_role("admin")
    user_store.create_role("support")

    assert user_store.list_roles() == {"admin", "support"}


def test_role_exists_returns_true_for_existing_role(user_store: UserStore) -> None:
    user_store.create_role("admin")

    assert user_store.role_exists("admin")


def test_role_exists_returns_false_for_missing_role(
    user_store: UserStore,
) -> None:
    assert not user_store.role_exists("missing")


def test_grant_role_to_user_persists_assignment(user_store: UserStore) -> None:
    create_user(user_store)
    user_store.create_role("admin")

    user_store.grant_role_to_user("alice", "admin")
    user_store.grant_role_to_user("alice", "admin")

    assert user_store.get_user_roles("alice") == {"admin"}


def test_revoke_role_from_user_deletes_assignment(user_store: UserStore) -> None:
    create_user(user_store)
    user_store.create_role("admin")
    user_store.grant_role_to_user("alice", "admin")

    user_store.revoke_role_from_user("alice", "admin")
    user_store.revoke_role_from_user("alice", "admin")

    assert user_store.get_user_roles("alice") == set()


def test_get_user_roles_returns_empty_set_for_missing_user(
    user_store: UserStore,
) -> None:
    assert user_store.get_user_roles("missing") == set()


__all__ = [name for name in globals() if name.startswith("test_")]
