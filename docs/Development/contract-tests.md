---
title: Contract tests
description: Developing and running the shared UserStore contract tests locally.
icon: lucide/list-checks

---
# Contract tests

The reusable `UserStore` contract tests live in
`userharbor.testing.user_store_contract`. Storage adapters import the complete
suite and provide a function-scoped `user_store` fixture:

```python
# tests/test_user_store_contract.py

from userharbor.testing.user_store_contract import *
```

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

The fixture must return a clean store for every test and clean up any databases,
connections, containers, or other resources it creates. Contract tests only use
the public `UserStore` interface. Backend-specific behavior should remain in the
adapter's own tests.

## Developing a contract across local repositories

Changes to the contract often need to be tested in both the main UserHarbor
repository and an adapter repository before a new UserHarbor version is
published. Keep the repositories next to each other:

```text
Dev/
    userharbor/
    userharbor-sqlalchemy/
```

From the adapter repository, run pytest with the local UserHarbor checkout
installed as an editable dependency:

```bash
cd ~/Dev/userharbor-sqlalchemy
uv run --with-editable ../userharbor pytest
```

This overlays the local checkout for that command without changing the
adapter's `pyproject.toml` or `uv.lock`. Uncommitted changes under
`userharbor/src/` are immediately available to the adapter, so contributors can
develop a new contract test and the corresponding adapter behavior together.

To confirm which UserHarbor checkout is imported:

```bash
uv run --with-editable ../userharbor python -c \
  "import userharbor; print(userharbor.__file__)"
```

The printed path should point to the local `userharbor/src/userharbor`
directory.

Run the main repository tests separately:

```bash
cd ~/Dev/userharbor
uv run pytest
```

Before submitting changes, both the main suite and every affected adapter suite
should pass.
