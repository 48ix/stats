"""API Endpoints for Routing Policy Control."""

# Standard Library
from typing import Optional

# Third Party
from fastapi import Header, BackgroundTasks
from fastapi.exceptions import HTTPException

# Project
from stats.log import log
from stats.auth.main import get_job, create_job, authenticate_user
from stats.actions.policy import _update_policy
from stats.models.update_policy import UpdatePolicyResponse


async def verify_auth(username: str, password: str) -> bool:
    """Verify a username & password combination is valid."""
    if not all((username, password)):
        raise HTTPException(401)
    authenticated = await authenticate_user(username=username, password=password)
    if not authenticated:
        raise HTTPException(401)
    return authenticated


async def update_policy(
    background_tasks: BackgroundTasks,
    x_48ix_api_user: Optional[str] = Header(None),
    x_48ix_api_key: Optional[str] = Header(None),
):
    """Initiate a manual policy update."""
    await verify_auth(x_48ix_api_user, x_48ix_api_key)

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


async def policy_status(
    job_id: int,
    x_48ix_api_user: Optional[str] = Header(None),
    x_48ix_api_key: Optional[str] = Header(None),
):
    """Get the status of a policy update by job ID."""
    await verify_auth(x_48ix_api_user, x_48ix_api_key)
    job = await get_job(job_id)
    await job.fetch_related("requestor")

    job_response = UpdatePolicyResponse(
        id=job.id,
        request_time=job.request_time,
        complete_time=job.complete_time,
        requestor=job.requestor.username,
        detail=job.detail,
        in_progress=job.in_progress,
    )
    log.debug("Job {} status: {}", job.id, job_response)
    return job_response.dict()
