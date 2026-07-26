from userharbor.interfaces import UserStore

from ._support import create_user


def test_create_permission_persists_permission(user_store: UserStore) -> None:
    user_store.create_permission("users.delete")

    assert user_store.permission_exists("users.delete")
    assert user_store.list_permissions() == {"users.delete"}


def test_delete_permission_deletes_permission_and_assignments(
    user_store: UserStore,
) -> None:
    user_store.create_role("admin")
    user_store.create_permission("users.delete")
    user_store.grant_permission_to_role("admin", "users.delete")

    user_store.delete_permission("users.delete")

    assert not user_store.permission_exists("users.delete")
    assert user_store.get_role_permissions("admin") == set()


def test_delete_permission_ignores_missing_permission(
    user_store: UserStore,
) -> None:
    user_store.delete_permission("missing.permission")

    assert user_store.list_permissions() == set()


def test_list_permissions_returns_permissions(user_store: UserStore) -> None:
    user_store.create_permission("users.read")
    user_store.create_permission("users.delete")

    assert user_store.list_permissions() == {"users.read", "users.delete"}


def test_permission_exists_returns_true_for_existing_permission(
    user_store: UserStore,
) -> None:
    user_store.create_permission("users.delete")

    assert user_store.permission_exists("users.delete")


def test_permission_exists_returns_false_for_missing_permission(
    user_store: UserStore,
) -> None:
    assert not user_store.permission_exists("missing.permission")


def test_grant_permission_to_role_persists_assignment(
    user_store: UserStore,
) -> None:
    user_store.create_role("admin")
    user_store.create_permission("users.delete")

    user_store.grant_permission_to_role("admin", "users.delete")
    user_store.grant_permission_to_role("admin", "users.delete")

    assert user_store.get_role_permissions("admin") == {"users.delete"}


def test_revoke_permission_from_role_deletes_assignment(
    user_store: UserStore,
) -> None:
    user_store.create_role("admin")
    user_store.create_permission("users.delete")
    user_store.grant_permission_to_role("admin", "users.delete")

    user_store.revoke_permission_from_role("admin", "users.delete")
    user_store.revoke_permission_from_role("admin", "users.delete")

    assert user_store.get_role_permissions("admin") == set()


def test_get_user_permissions_returns_permissions_from_roles(
    user_store: UserStore,
) -> None:
    create_user(user_store)
    user_store.create_role("admin")
    user_store.create_role("billing")
    user_store.create_permission("users.delete")
    user_store.create_permission("invoices.read")
    user_store.grant_permission_to_role("admin", "users.delete")
    user_store.grant_permission_to_role("billing", "invoices.read")
    user_store.grant_role_to_user("alice", "admin")
    user_store.grant_role_to_user("alice", "billing")

    assert user_store.get_user_permissions("alice") == {
        "users.delete",
        "invoices.read",
    }


def test_get_user_permissions_returns_empty_set_for_missing_user(
    user_store: UserStore,
) -> None:
    assert user_store.get_user_permissions("missing") == set()


__all__ = [name for name in globals() if name.startswith("test_")]
