import re

import sqlalchemy

from .db import groups
from .db import group_members
from .db import transaction


class Failure(Exception): pass


GROUP_EXPANSIONS_CACHE = {}
MEMBER_EXPANSIONS_CACHE = {}


def clear_group_cache():
    # TODO: clear only the relevant cache keys
    global GROUP_EXPANSIONS_CACHE
    GROUP_EXPANSIONS_CACHE = {}


def clear_member_cache():
    # TODO: clear only the relevant cache keys
    global MEMBER_EXPANSIONS_CACHE
    MEMBER_EXPANSIONS_CACHE = {}


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
    clear_group_cache()
    clear_member_cache()
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
    clear_group_cache()
    clear_member_cache()
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
    clear_group_cache()
    clear_member_cache()
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
    clear_group_cache()
    clear_member_cache()
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
    clear_group_cache()
    clear_member_cache()
    query.execute()


def list_accounts(group):
    """List all of the accounts that are a member of a group.

    This function lists both direct and indirect memberships.
    """
    accounts = GROUP_EXPANSIONS_CACHE.get(group)
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
    GROUP_EXPANSIONS_CACHE[group] = accounts
    return accounts


def is_member_account(group, account):
    """Returns whether or not an account is a member of a group.

    This function checks both direct and indirect memberships.
    """
    return account in list_accounts(group)


def list_parents(member):
    """List all of the groups that something is a member of, directly or indirectly."""
    parents = MEMBER_EXPANSIONS_CACHE.get(member)
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
    MEMBER_EXPANSIONS_CACHE[member] = parents
    return parents


def list_account_memberships(account):
    """List all groups that an account is a member of, directly or indirectly."""
    member = "account:{}".format(account)
    return list_parents(member)
