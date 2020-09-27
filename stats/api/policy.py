"""API Endpoints for Routing Policy Control."""

# Standard Library
from typing import Optional

# Third Party
from fastapi import Header, BackgroundTasks

# Project
from stats.log import log
from stats.auth.main import get_job, create_job, authorize_route, authenticate_user
from stats.exceptions import AuthError
from stats.actions.policy import _update_policy, _update_switch_acl
from stats.models.update_policy import UpdatePolicyResponse


async def _verify_auth(username: str, password: str, route: str) -> bool:
    """Authenticate & authorize a user.

    Verifies the proper headers are provided, authenticates the username
    & password, and authorizes the route.
    """
    has_headers = all((username, password))
    authenticated = await authenticate_user(username=username, password=password)
    authorized = await authorize_route(username, route)
    full_auth = all((has_headers, authenticated, authorized))

    if not full_auth:
        raise AuthError(
            "Authentication or authorization failed for user '{user}'",
            user=username,
            status_code=401,
        )

    return full_auth


async def update_policy(
    background_tasks: BackgroundTasks,
    x_48ix_api_user: Optional[str] = Header(None),
    x_48ix_api_key: Optional[str] = Header(None),
):
    """Initiate a manual policy update."""
    await _verify_auth(x_48ix_api_user, x_48ix_api_key, "/policy/update/")

    job = await create_job(requestor=x_48ix_api_user)
    await job.fetch_related("requestor")
    background_tasks.add_task(_update_policy, wait=1, job=job.id)
    job_response = UpdatePolicyResponse(
        id=job.id,
        request_time=job.request_time,
        complete_time=job.complete_time,
        requestor=job.requestor.username,
        detail=job.detail,
        in_progress=job.in_progress,
    )
    return job_response.dict()


async def update_acls(
    background_tasks: BackgroundTasks,
    x_48ix_api_user: Optional[str] = Header(None),
    x_48ix_api_key: Optional[str] = Header(None),
):
    """Initiate a manual policy update."""

    await _verify_auth(x_48ix_api_user, x_48ix_api_key, "/acls/update/")

    job = await create_job(requestor=x_48ix_api_user)
    await job.fetch_related("requestor")

    background_tasks.add_task(_update_switch_acl, job=job.id)

    job_response = UpdatePolicyResponse(
        id=job.id,
        request_time=job.request_time,
        complete_time=job.complete_time,
        requestor=job.requestor.username,
        detail=job.detail,
        in_progress=job.in_progress,
    )
    return job_response.dict()


async def job_status(
    job_id: int,
    x_48ix_api_user: Optional[str] = Header(None),
    x_48ix_api_key: Optional[str] = Header(None),
):
    """Get the status of a job by ID."""
    await _verify_auth(x_48ix_api_user, x_48ix_api_key, "/job/*")
    job = await get_job(job_id)
    await job.fetch_related("requestor")

    response = UpdatePolicyResponse(
        id=job.id,
        request_time=job.request_time,
        complete_time=job.complete_time,
        requestor=job.requestor.username,
        detail=job.detail,
        in_progress=job.in_progress,
    )
    log.debug("Job {} status: {}", job.id, response)
    return response.dict()
