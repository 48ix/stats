"""API Routes & Configuration."""
# Third Party
from fastapi import FastAPI

# Project
from stats.log import log
from stats.util import parse_port_id
from stats.config import params
from stats.actions.utilization import port_utilization_range, port_utilization_period
from stats.models.port_utilization import PortUtilization

api = FastAPI(
    debug=params.debug,
    title=params.api.title,
    description=params.api.description,
    docs_url=None,
    redoc_url="/docs",
)

ASGI_PARAMS = {
    "host": str(params.listen_address),
    "port": params.listen_port,
    "debug": params.debug,
}


@api.get("/{port_id}", response_model=PortUtilization)
async def port_utilization(
    port_id: str, period: int = None, start: str = None, end: str = None,
):
    """Get utilization statistics for a port."""
    if start is not None:
        data_in = await port_utilization_range(port_id, "in", start, end)
        data_out = await port_utilization_range(port_id, "out", start, end)
    else:
        period = period or params.api.default_period
        data_in = await port_utilization_period(port_id, "in", period)
        data_out = await port_utilization_period(port_id, "out", period)

    location, participant_id, _ = parse_port_id(port_id)

    response = {
        "ingress": data_in.get("values", [[]]),
        "egress": data_out.get("values", [[]]),
        "participant_id": participant_id,
        "location": location,
        "port_id": port_id,
    }

    log.debug("Response for query: {}", response)

    return response


def start(**kwargs):
    """Start the web server with Uvicorn ASGI."""
    import uvicorn

    uvicorn_kwargs = ASGI_PARAMS
    uvicorn_kwargs.update(kwargs)
    uvicorn.run("stats.api.main:api", **uvicorn_kwargs)
