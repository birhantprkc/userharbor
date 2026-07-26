---
title: Custom Integrations
description: How to build storage, email, framework, or provider integrations for UserHarbor.
icon: lucide/puzzle

---
# Custom Integrations

UserHarbor integrations should live outside the core package. The core library
owns account-management rules, token generation, token hashing, and password
hashing. Integrations provide infrastructure-specific behavior behind small
protocols.

Common integration types include:

* database or ORM-backed `UserStore` implementations
* email-provider `EmailSender` implementations
* framework packages that wire UserHarbor into routes, dependencies, or request
  handling
* provider adapters for services such as SendGrid, Resend, Mailgun, Redis, or
  MongoDB

Before creating a new adapter, review the official implementations:

```text
https://github.com/userharbor/userharbor-sqlalchemy
https://github.com/userharbor/userharbor-smtp
```

## Package structure

Keep custom integrations as separate packages. A typical package can be small:

```text
userharbor-myadapter/
    pyproject.toml
    README.md
    src/
        userharbor_myadapter/
            __init__.py
            py.typed
            store.py
            sender.py
    tests/
```

Only include the files your adapter needs. A storage adapter does not need an
email sender, and an email adapter does not need database code.

## UserStore integrations

Implement `UserStore` when your adapter is responsible for persistence.

`UserStore` is one required contract, but it is composed from smaller protocols
for readability:

* `UserAccountStore`
* `TokenStore`
* `RoleStore`
* `PermissionStore`

Adapter packages should still pass one store object to `UserHarbor`.

```python
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime

from userharbor.interfaces import CreateUserRequest, UserStore, UserToken


@dataclass
class MyUser:
    username: str
    email: str
    verified: bool


class MyUserStore(UserStore[MyUser]):
    def transaction(self) -> AbstractContextManager[None]:
        ...

    def create_user(self, user: CreateUserRequest) -> None:
        ...

    def set_user_verified(self, username: str) -> None:
        ...

    def delete_user(self, username: str) -> None:
        ...

    def get_user_by_username(self, username: str) -> MyUser | None:
        ...

    def get_user_by_email(self, email: str) -> MyUser | None:
        ...

    def get_password_hash(self, username: str) -> str:
        ...

    def set_password_hash(self, username: str, password_hash: str) -> None:
        ...

    # TokenStore

    def get_email_verification(self, token_hash: str) -> UserToken | None:
        ...

    def set_email_verification(self, verification: UserToken) -> None:
        ...

    def remove_email_verification(self, token_hash: str) -> None:
        ...

    def get_session(self, token_hash: str) -> UserToken | None:
        ...

    def add_session(self, session: UserToken) -> None:
        ...

    def remove_session(self, token_hash: str) -> None:
        ...

    def remove_all_sessions(self, username: str) -> None:
        ...

    def refresh_session(self, token_hash: str, new_expires_at: datetime) -> None:
        ...

    def get_password_reset(self, token_hash: str) -> UserToken | None:
        ...

    def set_password_reset(self, reset: UserToken) -> None:
        ...

    def remove_password_reset(self, token_hash: str) -> None:
        ...

    # RoleStore

    def create_role(self, role: str) -> None:
        ...

    def delete_role(self, role: str) -> None:
        ...

    def list_roles(self) -> set[str]:
        ...

    def role_exists(self, role: str) -> bool:
        ...

    def grant_role_to_user(self, username: str, role: str) -> None:
        ...

    def revoke_role_from_user(self, username: str, role: str) -> None:
        ...

    def get_user_roles(self, username: str) -> set[str]:
        ...

    # PermissionStore

    def create_permission(self, permission: str) -> None:
        ...

    def delete_permission(self, permission: str) -> None:
        ...

    def list_permissions(self) -> set[str]:
        ...

    def permission_exists(self, permission: str) -> bool:
        ...

    def grant_permission_to_role(self, role: str, permission: str) -> None:
        ...

    def revoke_permission_from_role(self, role: str, permission: str) -> None:
        ...

    def get_role_permissions(self, role: str) -> set[str]:
        ...

    def get_user_permissions(self, username: str) -> set[str]:
        ...
```

A `UserStore` is responsible for:

* creating and deleting users
* storing password hashes
* storing email verification token hashes
* storing session token hashes
* storing password reset token hashes
* storing role and permission definitions
* storing role-to-permission assignments
* storing user-to-role assignments
* removing sessions and tokens
* updating session expiration when sliding session refresh is enabled
* providing transaction boundaries for multi-step updates

The store should never store raw tokens. UserHarbor passes token hashes to the
store and keeps raw token handling in the core flow.

The user type returned by `get_user_by_username()` and `get_user_by_email()` can
be any object that provides `username`, `email`, and `verified`. Parameterize
`UserStore` with that concrete type so `UserHarbor.get_current_user()` preserves
it in type checkers.

### Contract semantics

A conforming `UserStore` must preserve the behavior expected by UserHarbor, not
only provide methods with matching signatures. In particular:

* usernames and email addresses are unique
* creating a user and their initial email verification token is atomic
* a newly created user is not verified
* setting a new email verification token removes the user's previous
  verification token
* setting a new password reset token removes the user's previous reset token
* deleting a user removes their verification tokens, password reset tokens, and
  sessions
* deleting a missing user, token, session, role, or permission is a no-op
* refreshing a missing session and marking a missing user as verified are no-ops
* reading a missing user or token returns `None`
* reading roles or effective permissions for a missing user returns an empty set
* reading or updating a password hash for a missing user raises `KeyError`
* granting or revoking the same relationship more than once is idempotent
* deleting roles and permissions removes their relationship assignments

The shared contract tests are the executable specification for these rules.
Backend-specific exception types and persistence details remain the adapter's
responsibility.

### Transactions

`transaction()` should return a context manager. UserHarbor uses it around
operations that update multiple related records, such as email verification,
password reset, password change, account deletion, and role or permission
assignment.

A conforming store must commit when the block finishes successfully and roll
back every change from the block when an exception is raised. Nested
`transaction()` calls must participate in the outer transaction.

A `nullcontext()` can be useful in an early prototype or a deliberately simple
test double, but it does not satisfy the complete `UserStore` contract and will
not pass the shared transaction tests.

### Testing

Every `UserStore` integration should run the shared contract tests provided by
UserHarbor. Import the complete suite in one test module:

```python
# tests/test_user_store_contract.py

from userharbor.testing.user_store_contract import *  # noqa: F403
```

Then provide a function-scoped `user_store` fixture in the integration:

```python
# tests/conftest.py

import pytest


@pytest.fixture
def user_store():
    store = create_user_store()
    try:
        yield store
    finally:
        dispose_user_store(store)
```

The fixture must provide a clean store for every test and release any database
connections or other resources afterwards. The shared suite verifies users,
password hashes, verification and reset tokens, sessions, roles, permissions,
assignments, and transaction behavior through the public `UserStore` interface.

Keep backend-specific tests in the integration repository. Examples include
database schema and migration tests, provider-specific errors, custom model
mapping, connection handling, and backend-specific transaction behavior.

See [UserStore contract tests](../Development/contract-tests.md) for instructions
on developing contracts and testing them against a local UserHarbor checkout
before a new version is published.

## EmailSender integrations

Implement `EmailSender` when your adapter is responsible for message delivery.

```python
from userharbor.interfaces import EmailSender


class MyEmailSender(EmailSender):
    def send_verification(
        self,
        username: str,
        email: str,
        verification_token: str,
    ) -> None:
        ...

    def send_password_reset(
        self,
        username: str,
        email: str,
        reset_token: str,
    ) -> None:
        ...

    def send_email_verified(self, username: str, email: str) -> None:
        ...

    def send_password_changed(self, username: str, email: str) -> None:
        ...

    def send_account_deleted(self, username: str, email: str) -> None:
        ...
```

An `EmailSender` should only send messages. It should not decide whether a token
is valid, hash tokens, verify users, or reset passwords. Those responsibilities
belong to UserHarbor core.

### Testing

For `EmailSender`, cover:

* verification messages
* password reset messages
* email-verified messages
* password-changed messages
* account-deleted messages
* subject and sender configuration
* template rendering, if templates are supported
* provider authentication or API calls using fakes

## Framework integrations

Framework integrations should compose UserHarbor with framework-specific tools
instead of moving domain behavior into the framework package.

A framework adapter may provide:

* dependency helpers
* route or router factories
* request-to-command mapping
* response models
* examples for configuring stores and email senders

It should avoid hard-coding one database or email provider unless that is the
explicit purpose of the package. Prefer accepting a configured `UserHarbor`
instance or accepting `UserStore` and `EmailSender` implementations from the
application.

## Public API

Export the main adapter class from the package root:

```python
from .store import MyUserStore

__all__ = ["MyUserStore"]
```

If the package is typed, include `py.typed` and configure packaging so it is
included in distributions.

## Naming

Use a clear package name that identifies the target integration:

```text
userharbor-sqlalchemy
userharbor-smtp
userharbor-fastapi
userharbor-sendgrid
userharbor-redis
```

Keep the adapter focused. If one package starts combining unrelated storage,
email, and framework behavior, split it into smaller packages.
