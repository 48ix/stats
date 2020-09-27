"""Route Policy Server Interaction."""

# Standard Library
from socket import gaierror
from typing import Union, Sequence, Generator

# Third Party
import rpyc
from rpyc.core import Connection

# Project
from stats.log import log
from stats.config import params
from stats.auth.main import update_job, complete_job
from stats.exceptions import StatsError


async def _remote_call(method: str, job_id: int, job_name: str, *args, **kwargs):
    log.info("Job {}: Starting {}", job_id, job_name)
    result = None

    try:
        connection: Connection = rpyc.connect(
            params.policy_server.host, params.policy_server.port, ipv6=True,
        )
        call = getattr(connection.root, method)
        result = call(*args, **kwargs)

        if isinstance(result, (Sequence, Generator)):
            message = ", ".join(result)
        elif isinstance(result, str):
            message = result
        else:
            message = ""

        await update_job(job_id, detail=message)

    except (ConnectionRefusedError, gaierror) as err:
        log.error(str(err))
        await update_job(job_id, in_progress=False, detail=str(err))
        raise StatsError(str(err))

    except TimeoutError as err:
        await update_job(job_id, in_progress=False, detail=str(err))
        log.error(str(err))
        pass

    await complete_job(job_id)
    log.success("Job: {}: Completed {}", job_id, job_name)


async def _update_policy(wait: int, job: int) -> None:
    """Signal the routing policy server to manually update its policy."""

    await _remote_call("update_policy", job, "Policy Update", wait=wait)


async def _update_switch_acl(job: int) -> None:
    """Signal the routing policy server to manually update switch ACLs."""

    await _remote_call("update_acls", job, "Switch ACL Update")
