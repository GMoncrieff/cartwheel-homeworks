"""Homework 2 authentication tests.

These run fully offline: no Langfuse, no Docker, no model provider key. The
endpoint functions are called directly rather than over HTTP, so no server
needs to be running. Tracing itself is verified through the recorded spans in
Part E, not here.

Both tests exercise the same property from opposite directions: the server
decides who the caller is, and nothing supplied by the caller can change it.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from server import app as server_app


@pytest.fixture(autouse=True)
def _clean_sessions():
    """_SESSIONS is module-level state; keep tests independent of each other."""
    server_app._SESSIONS.clear()
    yield
    server_app._SESSIONS.clear()


def test_create_session_rejects_role_mismatch(world: dict) -> None:
    """User 9002 is a merchant in the database; claiming shopper must fail.

    The role in the request body is a claim. create_session checks it against
    the stored role and refuses the mismatch, so a caller cannot pick the row
    of the access matrix it would like to be judged by.
    """
    with pytest.raises(HTTPException) as exc:
        server_app.create_session(
            server_app.SessionCreate(user_id=9002, role="shopper")
        )

    assert exc.value.status_code == 403
    # A refused request must also leave nothing usable behind: a session
    # created despite the 403 would be a bypass, since the caller could use
    # the session id without ever reading the rejected response.
    assert server_app._SESSIONS == {}


def test_token_cannot_authorize_a_different_session(world: dict) -> None:
    """A correctly signed token is still refused on another session.

    Both sessions belong to the same authenticated user, so this isolates the
    session binding itself: the token is not a general-purpose credential.
    """
    first = server_app.create_session(
        server_app.SessionCreate(user_id=1, role="shopper")
    )
    second = server_app.create_session(
        server_app.SessionCreate(user_id=1, role="shopper")
    )
    assert first["session_id"] != second["session_id"]

    # Pin the failure to the session binding: the token is genuinely valid,
    # so a 403 here cannot be blamed on a bad signature.
    payload = server_app.verify_token(first["token"])
    assert payload is not None
    assert payload["session_id"] == first["session_id"]

    with pytest.raises(HTTPException) as exc:
        server_app._authorize(second["session_id"], f"Bearer {first['token']}")

    assert exc.value.status_code == 403
