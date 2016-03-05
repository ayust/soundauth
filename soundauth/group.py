import re

import sqlalchemy

from .db import groups
from .db import group_members
from .db import transaction


class Failure(Exception): pass


ACCOUNT_EXPANSIONS_CACHE = {}
MEMBER_EXPANSIONS_CACHE = {}
PARENT_EXPANSIONS_CACHE = {}


def clear_account_cache(groups=None):
    global ACCOUNT_EXPANSIONS_CACHE
    if groups is None:
        ACCOUNT_EXPANSIONS_CACHE.clear()
    else:
        for group in groups:
            ACCOUNT_EXPANSIONS_CACHE.pop(group, None)


def clear_member_cache(groups=None):
    global MEMBER_EXPANSIONS_CACHE
    if groups is None:
        MEMBER_EXPANSIONS_CACHE.clear()
    else:
        for group in groups:
            MEMBER_EXPANSIONS_CACHE.pop(group, None)


def clear_group_caches(groups=None):
    clear_account_cache(groups)
    clear_member_cache(groups)


def clear_parent_cache(children=None):
    global PARENT_EXPANSIONS_CACHE
    if children is None:
        PARENT_EXPANSIONS_CACHE.clear()
    else:
        for child in children:
            PARENT_EXPANSIONS_CACHE.pop(child, None)


def create_group(name):
    """Create a new group."""
    if not re.match("^\w+$", name):
        raise Failure("The group name '{}' is invalid.".format(name))
    query = groups.insert().values(
        name=name,
    )
    try:
        query.execute()
    except sqlalchemy.exc.IntegrityError:
        raise Failure("The group '{}' already exists.".format(name))


def drop_group(name):
    """Remove an existing group."""
    delete_group = groups.delete().where(
        groups.c.name == name,
    )
    delete_members = group_members.delete().where(
        (group_members.c.parent == name) |
        (group_members.c.child == name),
    )
    clear_group_caches(list_parents(name) | set([name]))
    clear_parent_cache(list_children(name) | set([name]))
    with transaction() as t:
        t.execute(delete_group)
        t.execute(delete_members)


def group_exists(name):
    """Returns whether or not a group exists."""
    query = groups.select().where(
        groups.c.name == name,
    )
    if query.execute().first():
        return True
    return False


def add_subgroup(group, member):
    """Add a group as a member to another group."""
    if not group_exists(group):
        raise Failure("No group named '{}' exists.".format(group))
    query = group_members.insert().values(parent=group, child=member)
    clear_group_caches(list_parents(group) | set([member]))
    clear_parent_cache(list_children(group) | set([member]))
    try:
        query.execute()
    except sqlalchemy.exc.IntegrityError:
        # If the membership already exists, nothing more to do.
        pass


def drop_subgroup(group, member):
    """Remove a group from membership in another group."""
    query = group_members.delete().where(
        (group_members.c.parent == group) &
        (group_members.c.child == member),
    )
    clear_group_caches(list_parents(group) | set([member]))
    clear_parent_cache(list_children(group) | set([member]))
    query.execute()


def list_members(group):
    """List all of the top-level members of a group.

    Note: will return an empty list for groups that do not exist.
    """
    query = group_members.select().where(
        group_members.c.parent == group,
    )
    result = query.execute()
    return set(row.child for row in result)


def list_children(group):
    """Recursively list all direct and indirect members of a group."""
    members = MEMBER_EXPANSIONS_CACHE.get(group)
    if members is not None:
        return members
    members = set()
    query = group_members.select().where(
        group_members.c.parent == group,
    )
    for result in query.execute():
        member = result.child
        members.add(member)
        members |= list_children(member)
    members = frozenset(members)
    MEMBER_EXPANSIONS_CACHE[group] = members
    return members


def is_member(group, member):
    """Check for a top-level group membership."""
    query = group_members.select().where(
        (group_members.c.parent == group) &
        (group_members.c.child == member),
    )
    if query.execute().first():
        return True
    return False


def add_member_account(group, account):
    """Add an account as a member to an existing group."""
    if not group_exists(group):
        raise Failure("No group named '{}' exists.".format(group))
    member = "account:{}".format(account)
    query = group_members.insert().values(parent=group, child=member)
    clear_group_caches(list_parents(group) | set([member]))
    clear_parent_cache(list_children(group) | set([member]))
    try:
        query.execute()
    except sqlalchemy.exc.IntegrityError:
        # If the membership already exists, nothing more to do.
        pass


def drop_member_account(group, account):
    """Remove an account from membership in a group."""
    member = "account:{}".format(account)
    query = group_members.delete().where(
        (group_members.c.parent == group) &
        (group_members.c.child == member),
    )
    clear_group_caches(list_parents(group) | set([member]))
    clear_parent_cache(list_children(group) | set([member]))
    query.execute()


def list_accounts(group):
    """List all of the accounts that are a member of a group.

    This function lists both direct and indirect memberships.
    """
    accounts = ACCOUNT_EXPANSIONS_CACHE.get(group)
    if accounts is not None:
        return accounts

    accounts = set()
    for member in list_members(group):
        prefix, _, value = member.rpartition(":")
        if not prefix:
            accounts |= list_accounts(value)
        elif prefix == "account":
            accounts.add(int(value))
        else:
            raise Failure("Unknown prefix '{}' for member.".format(prefix))
    accounts = frozenset(accounts)
    ACCOUNT_EXPANSIONS_CACHE[group] = accounts
    return accounts


def is_member_account(group, account):
    """Returns whether or not an account is a member of a group.

    This function checks both direct and indirect memberships.
    """
    return account in list_accounts(group)


def list_parents(member):
    """List all of the groups that something is a member of, directly or indirectly."""
    parents = PARENT_EXPANSIONS_CACHE.get(member)
    if parents is not None:
        return parents
    parents = set()
    query = group_members.select().where(
        group_members.c.child == member,
    )
    for result in query.execute():
        parent = result.parent
        parents.add(parent)
        parents |= list_parents(parent)
    parents = frozenset(parents)
    PARENT_EXPANSIONS_CACHE[member] = parents
    return parents


def list_account_memberships(account):
    """List all groups that an account is a member of, directly or indirectly."""
    member = "account:{}".format(account)
    return list_parents(member)
