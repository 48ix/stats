"""Route Policy Server Interaction."""

# Standard Library
from socket import gaierror

# Third Party
import rpyc
from rpyc.core import Connection

# Project
from stats.log import log
from stats.config import params
from stats.auth.main import update_job, complete_job
from stats.exceptions import StatsError


async def _update_policy(wait: int, job: int) -> None:
    """Signal the routing policy server to manually update its policy."""

    log.info("Job {}: Starting policy update", job)
    result = None

    try:
        connection: Connection = rpyc.connect(
            params.policy_server.host, params.policy_server.port, ipv6=True,
        )
        result = connection.root.update_policy(wait)
        await update_job(job, detail=", ".join(result))

    except (ConnectionRefusedError, gaierror) as err:
        log.error(str(err))
        await update_job(job, in_progress=False, detail=str(err))
        raise StatsError(str(err))

    except TimeoutError as err:
        await update_job(job, in_progress=False, detail=str(err))
        log.error(str(err))
        pass

    await complete_job(job)
    log.success("Job: {}: Completed policy update", job)
