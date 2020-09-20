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
    log.info("Opening database connection")
    await Tortoise.init(
        db_url=f"sqlite:///{str(params.api.dbmain_path)}",
        modules={"models": ["stats.auth.models"]},
    )
    await Tortoise.generate_schemas()


async def authdb_stop() -> None:
    """Close database connection."""
    log.info("Closing database connection")
    await Tortoise.close_connections()


async def get_user(username: str) -> ApiUser:
    """Get a user object by username."""
    try:
        user = await ApiUser.get(username=username)
    except DoesNotExist:
        raise AuthError("User '{u}' does not exist.", u=username) from None
    return user


async def get_job(job_id: int) -> ApiJob:
    """Get a job object by id."""
    try:
        job = await ApiJob.get(id=job_id)
    except DoesNotExist:
        raise StatsError(f"Job {job_id} does not exist.") from None
    return job


async def get_route(route: str) -> ApiRoute:
    """Get a user object by username."""
    return await ApiRoute.get(name=route)


async def create_user(username: str, password: str) -> None:
    """Create an API user."""
    hashed_password = argon2.hash(password)

    try:
        await ApiUser.create(username=username, password=hashed_password)
    except IntegrityError:
        raise AuthError("User '{u}' already exists.", u=username) from None

    log.success("Added user {}", username)


async def create_route(name: str) -> None:
    """Create an API route entry for authorization."""
    try:
        await ApiRoute.create(name=name)
    except IntegrityError:
        raise StatsError(f"Route '{name}' already exists") from None
    log.success("Added route {}", name)


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


async def associate_route(username: str, routes: Union[str, List[str]]) -> None:
    """Add routes to a user."""
    user = await get_user(username)

    if isinstance(routes, str):
        routes = [routes]

    for route in routes:
        matched = await get_route(route)
        await user.routes.add(matched)
        log.success("Added route {} to user {}", route, user.username)


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
        raise AuthError("User '{u}' does not exist.", u=username) from None

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
