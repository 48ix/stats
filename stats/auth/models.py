"""API Database Models."""

# Third Party
from tortoise.fields import (
    CharField,
    TextField,
    BooleanField,
    DatetimeField,
    ForeignKeyField,
    ManyToManyField,
    ReverseRelation,
    ForeignKeyRelation,
)
from tortoise.models import Model


class ApiUser(Model):
    """API user."""

    username = CharField(max_length=128, unique=True)
    password = CharField(max_length=255)
    routes = ManyToManyField("models.ApiRoute", related_name="users")
    jobs: ReverseRelation["ApiJob"]

    class Meta:
        """Tortoise ORM Config."""

        table = "api_users"


class ApiRoute(Model):
    """API route definition for access control."""

    name = CharField(max_length=255, unique=True)
    users: ReverseRelation["models.ApiUser"]  # noqa: F821

    class Meta:
        """Tortoise ORM Config."""

        table = "api_routes"


class ApiJob(Model):
    """API job model."""

    requestor: ForeignKeyRelation[ApiUser] = ForeignKeyField(
        "models.ApiUser", related_name="jobs"
    )
    request_time = DatetimeField(auto_now=True)
    complete_time = DatetimeField(null=True)
    in_progress = BooleanField(default=False)
    detail = TextField(null=True)

    class Meta:
        """Tortoise ORM Config."""

        table = "api_jobs"
