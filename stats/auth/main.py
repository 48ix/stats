"""Interact with local SQLite database for API user authentication."""

# Standard Library
from typing import List, Union
from datetime import datetime

# Third Party
from tortoise import Tortoise
from passlib.hash import argon2
from tortoise.exceptions import DoesNotExist, IntegrityError

# Project
from stats.log import log
from stats.config import params
from stats.exceptions import AuthError, StatsError
from stats.auth.models import ApiJob, ApiUser, ApiRoute


async def authdb_start() -> None:
    """Initialize database connection."""
    log.debug("Opening database connection")
    await Tortoise.init(
        db_url=f"sqlite:///{str(params.api.dbmain_path)}",
        modules={"models": ["stats.auth.models"]},
    )
    await Tortoise.generate_schemas()


async def authdb_stop() -> None:
    """Close database connection."""
    log.debug("Closing database connection")
    await Tortoise.close_connections()


async def get_user(username: str) -> ApiUser:
    """Get a user object by username."""
    try:
        user = await ApiUser.get(username=username)
    except DoesNotExist as err:
        raise AuthError(
            "User '{u}' does not exist.", u=username, status_code=404
        ) from err
    return user


async def get_job(job_id: int) -> ApiJob:
    """Get a job object by id."""
    try:
        job = await ApiJob.get(id=job_id)
    except DoesNotExist as err:
        raise StatsError(f"Job {job_id} does not exist.") from err
    return job


async def get_route(route: str) -> ApiRoute:
    """Get a user object by username."""
    try:
        _route = await ApiRoute.get(name=route)
    except DoesNotExist as err:
        raise AuthError("Route '{r}' does not exist.", r=route) from err
    return _route


async def create_user(username: str, password: str) -> None:
    """Create an API user."""
    hashed_password = argon2.hash(password)

    try:
        await ApiUser.create(username=username, password=hashed_password)
    except IntegrityError:
        raise AuthError(
            "User '{u}' already exists.", u=username, status_code=409
        ) from None

    log.success("Added user {}", username)


async def delete_user(username) -> None:
    """Delete an API user."""
    user = await get_user(username)
    await user.delete()
    log.success("Deleted user {}", username)


async def create_route(name: str) -> None:
    """Create an API route entry for authorization."""
    try:
        await ApiRoute.create(name=name)
    except IntegrityError:
        raise StatsError(f"Route '{name}' already exists") from None
    log.success("Added route {}", name)


async def delete_route(route) -> None:
    """Delete an API route."""
    _route = await get_route(route)
    await _route.delete()
    log.success("Deleted route {}", route)


async def create_job(requestor: str) -> ApiJob:
    """Create a new API job record."""
    user = await get_user(requestor)
    job = ApiJob(requestor=user, in_progress=True)
    await job.save()
    return job


async def update_job(job_id: int, **kwargs) -> None:
    """Update a job's attributes."""
    await ApiJob.filter(id=job_id).update(**kwargs)


async def complete_job(job_id: int) -> None:
    """Mark a job as complete."""
    await ApiJob.filter(id=job_id).update(
        in_progress=False, complete_time=datetime.utcnow()
    )


async def _change_route(
    username: str, routes: Union[str, List[str]], action: str
) -> None:
    """Associate or disassociate a route from a user."""
    user = await get_user(username)

    if isinstance(routes, str):
        routes = [routes]

    if action == "add":
        coro = user.routes.add
        msg = "Added route {} to user {}"
    elif action == "remove":
        coro = user.routes.remove
        msg = "Removed route {} from user {}"
    else:
        raise StatsError(f"Action {action} is not supported")

    for route in routes:
        matched = await get_route(route)
        await coro(matched)
        log.success(msg, route, user.username)


async def associate_route(username: str, routes: Union[str, List[str]]) -> None:
    """Add routes to a user."""
    await _change_route(username, routes, "add")


async def disassociate_route(username: str, routes: Union[str, List[str]]) -> None:
    """Remove routes from a user."""
    await _change_route(username, routes, "remove")


async def authorize_route(username: str, route: str) -> bool:
    """Verify if a user has access to an API route."""
    is_authorized = False
    try:
        user = await get_user(username)
        await user.fetch_related("routes")
        async for user_route in user.routes:
            if route == user_route.name:
                is_authorized = True
                break
    except DoesNotExist:
        raise AuthError(
            "User '{u}' does not exist.", u=username, status_code=401
        ) from None

    if is_authorized:
        log.debug("{} is authorized to access {}", username, route)
    if not is_authorized:
        log.error("{} is not authorized to access {}", username, route)

    return is_authorized


async def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user."""
    user = await get_user(username)
    valid = argon2.verify(password, user.password)
    if valid:
        log.debug("Authentication succeeded for user {}", username)
    if not valid:
        log.error("Authentication failed for user {}", username)
    return valid
