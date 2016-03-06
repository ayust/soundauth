from .db import rules
from .group import group_exists


class Failure(Exception): pass


def create_rule(group, action, condition, argument=None):
    """Add a new membership rule for a group and return the id.

    New rules are always added last in the ordering for the group
    they are modifying.
    """
    if not group_exists(group):
        raise Failure("The group '{}' does not exist.".format(group))
    existing = rules.select().where(
        rules.c.group == group,
    ).execute()
    max_order = max([0] + [row.order for row in existing])
    query = rules.insert().values(
        group=group,
        action=action,
        condition=condition,
        argument=argument,
        order=max_order+1,
    )
    rule_id = query.execute().inserted_primary_key[0]
    return rule_id


def drop_rule(rule_id):
    """Remove an existing rule."""
    query = rules.delete().where(rules.c.id == rule_id)
    query.execute()
