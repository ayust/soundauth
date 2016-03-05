import sqlalchemy
from .db import groups
from .db import group_members


class Failure(Exception): pass


def create_group(name):
    """Create a new group."""
    query = groups.insert().values(
        name=name,
    )
    try:
        query.execute()
    except sqlalchemy.exc.IntegrityError:
        raise Failure("The group '{}' already exists.".format(name))


def drop_group(name):
    """Remove an existing group."""
    query = groups.delete().where(
        groups.c.name == name,
    )
    query.execute()


def add_member(group, member):
    """Add a member to an existing group."""
    query = groups.select().where(
        groups.c.name == group,
    )
    if not query.execute().first():
        raise Failure("No group named '{}' exists.".format(group))
    query = group_members.insert().values(parent=group, child=member)
    try:
        query.execute()
    except sqlalchemy.exc.IntegrityError:
        # If the membership already exists, nothing more to do.
        pass


def drop_member(group, member):
    """Remove a group membership."""
    query = group_members.delete().where(
        (group_members.c.parent == group) &
        (group_members.c.child == member),
    )
    query.execute()


def is_member(group, member):
    """Check for a group membership."""
    query = group_members.select().where(
        (group_members.c.parent == group) &
        (group_members.c.child == member),
    )
    if query.execute().first():
        return True
    return False
