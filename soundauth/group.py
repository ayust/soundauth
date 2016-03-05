import re

import sqlalchemy

from .db import groups
from .db import group_members
from .db import transaction


class Failure(Exception): pass


ACCOUNT_EXPANSIONS_CACHE = {}
DESCENDANT_EXPANSIONS_CACHE = {}
ANCESTOR_EXPANSIONS_CACHE = {}


def clear_account_cache(items=None):
    global ACCOUNT_EXPANSIONS_CACHE
    if items is None:
        ACCOUNT_EXPANSIONS_CACHE.clear()
    else:
        for item in items:
            ACCOUNT_EXPANSIONS_CACHE.pop(item, None)


def clear_descendant_cache(items=None):
    global DESCENDANT_EXPANSIONS_CACHE
    if items is None:
        DESCENDANT_EXPANSIONS_CACHE.clear()
    else:
        for item in items:
            DESCENDANT_EXPANSIONS_CACHE.pop(item, None)


def clear_ancestor_cache(items=None):
    global ANCESTOR_EXPANSIONS_CACHE
    if items is None:
        ANCESTOR_EXPANSIONS_CACHE.clear()
    else:
        for item in items:
            ANCESTOR_EXPANSIONS_CACHE.pop(item, None)


def clear_caches(parent=None, child=None):
    if parent is None or child is None:
        clear_account_cache()
        clear_ancestor_cache()
        clear_descendant_cache()
    else:
        upwards = list_ancestors(parent) | set([parent])
        downwards = list_descendants(child) | set([child])
        clear_account_cache(upwards)
        clear_ancestor_cache(downwards)
        clear_descendant_cache(upwards)


def create_group(name):
    """Create a new group."""
    if not re.match("^[a-z-]+$", name):
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
    clear_caches(parent=name, child=name)
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


def add_subgroup(group, member, edgetype="or"):
    """Add a group as a member to another group."""
    if not group_exists(group):
        raise Failure("No group named '{}' exists.".format(group))
    query = group_members.insert().values(
        parent=group,
        child=member,
        edgetype=edgetype,
    )
    clear_caches(parent=group, child=member)
    try:
        query.execute()
    except sqlalchemy.exc.IntegrityError:
        # If the membership already exists, nothing more to do.
        pass


def drop_subgroup(group, member, edgetype="or"):
    """Remove a group from membership in another group."""
    query = group_members.delete().where(
        (group_members.c.parent == group) &
        (group_members.c.child == member) &
        (group_members.c.edgetype == edgetype),
    )
    clear_caches(parent=group, child=member)
    query.execute()


def list_members(group):
    """List all of the top-level members of a group.

    Note: will return an empty list for groups that do not exist.
    """
    query = group_members.select().where(
        group_members.c.parent == group,
    )
    result = query.execute()
    return set((row.edgetype, row.child) for row in result)


def list_descendants(group):
    """Recursively list anything that could affect membership in this group."""
    descendants = DESCENDANT_EXPANSIONS_CACHE.get(group)
    if descendants is not None:
        return descendants
    descendants = set()
    query = group_members.select().where(
        group_members.c.parent == group,
    )
    for result in query.execute():
        child = result.child
        descendants.add(child)
        descendants |= list_descendants(child)
    descendants = frozenset(descendants)
    DESCENDANT_EXPANSIONS_CACHE[group] = descendants
    return descendants


def is_member(group, member):
    """Check for a top-level group membership.

    Note: this membership might be a negative edgetype.
    """
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
    member = unicode(account)
    query = group_members.insert().values(
        parent=group,
        child=member,
        edgetype="account",
    )
    clear_caches(parent=group, child=member)
    try:
        query.execute()
    except sqlalchemy.exc.IntegrityError:
        # If the membership already exists, nothing more to do.
        pass


def drop_member_account(group, account):
    """Remove an account from membership in a group."""
    member = unicode(account)
    query = group_members.delete().where(
        (group_members.c.parent == group) &
        (group_members.c.child == member) &
        (group_members.c.edgetype == "account"),
    )
    clear_caches(parent=group, child=member)
    query.execute()


def list_accounts(group):
    """List all of the accounts that are a member of a group.

    This function lists both direct and indirect memberships.
    """
    accounts = ACCOUNT_EXPANSIONS_CACHE.get(group)
    if accounts is not None:
        return accounts

    union = set()
    prune = set()
    intersect = None
    for edgetype, member in list_members(group):
        if edgetype == "account":
            union.add(int(member))
        elif edgetype == "or":
            union |= list_accounts(member)
        elif edgetype == "and":
            if intersect is None:
                intersect = set(list_accounts(member))
            else:
                intersect &= list_accounts(member)
        elif edgetype == "not":
            prune |= list_accounts(member)
        else:
            raise Failure("Unknown edge type '{}' for member.".format(edgetype))
    intersect = intersect or set()
    accounts = frozenset((union | intersect) - prune)
    ACCOUNT_EXPANSIONS_CACHE[group] = accounts
    return accounts


def is_member_account(group, account):
    """Returns whether or not an account is a member of a group.

    This function checks both direct and indirect memberships.
    """
    return account in list_accounts(group)


def list_ancestors(member):
    """List all of the groups that something is a member of, directly or indirectly."""
    ancestors = ANCESTOR_EXPANSIONS_CACHE.get(member)
    if ancestors is not None:
        return ancestors
    ancestors = set()
    query = group_members.select().where(
        group_members.c.child == member,
    )
    for result in query.execute():
        ancestor = result.parent
        ancestors.add(ancestor)
        ancestors |= list_ancestors(ancestor)
    ancestors = frozenset(ancestors)
    ANCESTOR_EXPANSIONS_CACHE[member] = ancestors
    return ancestors


def list_account_memberships(account):
    """List all groups that an account is a member of, directly or indirectly."""
    ancestors = list_ancestors(unicode(account))
    return set(
        a for a in ancestors
        if account in list_accounts(a))
