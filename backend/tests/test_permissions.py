import asyncio

import pytest

from app.services.cache import TtlCache
from app.services.permissions import (
    AccessLevel,
    LockedReason,
    ShareScope,
    ShareType,
    can_manage_shares,
    find_duplicates,
    highest,
    is_assignable,
    lock_reason,
    share_sort_key,
)


@pytest.mark.parametrize("level", list(AccessLevel))
def test_manage_shares_requires_admin(level: AccessLevel) -> None:
    assert can_manage_shares(level) is (level in {AccessLevel.ADMIN, AccessLevel.OWNER})


@pytest.mark.parametrize("level", list(AccessLevel))
@pytest.mark.parametrize("scope", list(ShareScope))
def test_lock_reason_for_every_level_and_scope(level: AccessLevel, scope: ShareScope) -> None:
    reason = lock_reason(level, scope, AccessLevel.OWNER)
    if level is AccessLevel.OWNER:
        assert reason is LockedReason.OWNER
    elif scope is ShareScope.WORKSPACE:
        assert reason is LockedReason.INHERITED
    else:
        assert reason is None
    if level is not AccessLevel.OWNER and scope is ShareScope.ITEM:
        assert lock_reason(level, scope, AccessLevel.EDITOR) is LockedReason.NO_PERMISSION


def test_owner_is_never_assignable() -> None:
    assert [level for level in AccessLevel if not is_assignable(level)] == [AccessLevel.OWNER]


def test_share_sort_order() -> None:
    items = [
        (AccessLevel.VIEWER, ShareType.USER, "zoe"),
        (AccessLevel.ADMIN, ShareType.USER, "bea"),
        (AccessLevel.ADMIN, ShareType.GROUP, "Ventas"),
        (AccessLevel.OWNER, ShareType.USER, "ana"),
    ]
    ordered = sorted(items, key=lambda item: share_sort_key(*item))
    assert [label for _, _, label in ordered] == ["ana", "Ventas", "bea", "zoe"]


def test_highest_and_duplicates() -> None:
    assert highest([AccessLevel.VIEWER, AccessLevel.ADMIN]) is AccessLevel.ADMIN
    assert highest([]) is None
    assert find_duplicates(["a", "b", "a", "a"]) == ["a"]


async def test_cache_single_flight_and_invalidation() -> None:
    now = [0.0]
    cache = TtlCache(10, clock=lambda: now[0])
    calls = 0

    async def loader() -> int:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        return calls

    assert await asyncio.gather(*(cache.get_or_load("k", loader) for _ in range(5))) == [1] * 5
    assert calls == 1
    now[0] = 11
    assert await cache.get_or_load("k", loader) == 2
    cache.invalidate_prefix("k")
    assert await cache.get_or_load("k", loader) == 3
