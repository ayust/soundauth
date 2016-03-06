import sqlalchemy
# Grab some specific symbols for the table definition DSL
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import PrimaryKeyConstraint


METADATA_SINGLETON = sqlalchemy.MetaData()


def transaction():
    return ENGINE_SINGLETON.begin()


authenticators = Table("authenticators", METADATA_SINGLETON,
    # "public" portion of this authenticator, e.g. username
    Column("name", String(100), primary_key=True),
    # "private" portion of this authenticator, e.g. password
    Column("verifier", String(100), nullable=False),
    # The account with which this authenticator is associated
    Column("account", Integer, nullable=False),
)


accounts = Table("accounts", METADATA_SINGLETON,
    Column("id", Integer, primary_key=True),
)


groups = Table("groups", METADATA_SINGLETON,
    Column("name", String(100), primary_key=True),
)


group_members = Table("group_members", METADATA_SINGLETON,
    Column("parent", String(120), nullable=False),
    Column("child", String(120), nullable=False, index=True),
    Column("edgetype", String(100), nullable=False),
    PrimaryKeyConstraint("parent", "child", name="edge")
)


rules = Table("rules", METADATA_SINGLETON,
    Column("id", Integer, primary_key=True),
    Column("group", String(100), index=True),
    # One of 'deny', 'grant',
    Column("action", String(100), nullable=False),
    # E.g. "alliance", "!corp", etc...
    Column("condition", String(100)),
    Column("argument", String(100)),
    Column("order", Integer, nullable=False),
)


# TODO: Move the database connection string to configuration,
#       and optionally make this only trigger when requested.
ENGINE_SINGLETON = sqlalchemy.create_engine("sqlite:///:memory:", echo=True)
METADATA_SINGLETON.bind = ENGINE_SINGLETON
METADATA_SINGLETON.create_all()
