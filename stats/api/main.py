"""API Routes & Configuration."""

# Third Party
from fastapi import FastAPI
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Project
from stats.log import log
from stats.util import parse_port_id
from stats.config import params
from stats.api.events import startup_authdb, shutdown_authdb
from stats.api.policy import job_status, update_acls, update_policy
from stats.exceptions import AuthError, StatsError
from stats.actions.utilization import (
    port_average_range,
    port_average_period,
    port_utilization_range,
    port_utilization_period,
    overall_utilization_period,
    overall_utilization_max_period,
    overall_utilization_average_period,
)
from stats.models.update_policy import UpdatePolicyResponse
from stats.models.port_utilization import PortUtilization
from stats.models.overall_utilization import OverallUtilization

api = FastAPI(
    debug=params.debug,
    title=params.api.title,
    description=params.api.description,
    docs_url=None,
    redoc_url="/docs",
    default_response_class=JSONResponse,
)


@api.exception_handler(StatsError)
async def handle_app_error(request, exc):
    """Handle custom StatsError Exception."""
    return JSONResponse({"error": str(exc)}, 500)


@api.exception_handler(AuthError)
async def handle_auth_error(request, exc):
    """Handle custom AuthError Exception."""
    return JSONResponse({"error": str(exc)}, exc.status_code)


api.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

api.add_event_handler("startup", startup_authdb)
api.add_event_handler("shutdown", shutdown_authdb)

ASGI_PARAMS = {
    "host": str(params.listen_address),
    "port": params.listen_port,
    "debug": params.debug,
}


async def port_utilization(
    port_id: str, period: int = None, start: str = None, end: str = None,
):
    """Get utilization statistics for a port."""
    if start is not None:
        data_in = await port_utilization_range(
            port_id=port_id,
            direction="in",
            start=start,
            end=end,
            limit=params.api.default_limit,
        )
        data_out = await port_utilization_range(
            port_id=port_id,
            direction="out",
            start=start,
            end=end,
            limit=params.api.default_limit,
        )
        avg_in = await port_average_range(
            port_id=port_id,
            direction="in",
            start=start,
            end=end,
            limit=params.api.default_limit,
        )
        avg_out = await port_average_range(
            port_id=port_id,
            direction="out",
            start=start,
            end=end,
            limit=params.api.default_limit,
        )
    else:
        period = period or params.api.default_period
        data_in = await port_utilization_period(
            port_id=port_id,
            direction="in",
            period=period,
            limit=params.api.default_limit,
        )
        data_out = await port_utilization_period(
            port_id=port_id,
            direction="out",
            period=period,
            limit=params.api.default_limit,
        )
        avg_in = await port_average_period(
            port_id=port_id,
            direction="in",
            period=period,
            limit=params.api.default_limit,
        )
        avg_out = await port_average_period(
            port_id=port_id,
            direction="out",
            period=period,
            limit=params.api.default_limit,
        )

    location, participant_id, _ = parse_port_id(port_id)

    response = {
        "ingress": data_in.get("values", [[]]),
        "egress": data_out.get("values", [[]]),
        "participant_id": participant_id,
        "location": location,
        "port_id": port_id,
        "ingress_average": avg_in.get("values", [["", 0]])[0][1],
        "egress_average": avg_out.get("values", [["", 0]])[0][1],
    }

    log.debug("Response for query: {}", response)

    return response


async def overall_utilization(period: int = None):
    """Get IX-Wide utilization statistics."""
    period = period or params.api.default_period
    data_in = await overall_utilization_period(
        direction="in", period=period, limit=params.api.default_limit
    )
    data_out = await overall_utilization_period(
        direction="out", period=period, limit=params.api.default_limit
    )
    avg_in = await overall_utilization_average_period(
        direction="in", period=period, limit=params.api.default_limit
    )
    avg_out = await overall_utilization_average_period(
        direction="out", period=period, limit=params.api.default_limit
    )
    peak_in = await overall_utilization_max_period(
        direction="in", period=period, limit=params.api.default_limit
    )

    return {
        "ingress": data_in.get("values", [[]]),
        "egress": data_out.get("values", [[]]),
        "ingress_average": avg_in.get("values", [["", 0]])[0][1],
        "egress_average": avg_out.get("values", [["", 0]])[0][1],
        "ingress_peak": peak_in.get("values", [["", 0]])[0][1],
    }


api.add_api_route(
    path="/utilization/all",
    endpoint=overall_utilization,
    response_model=OverallUtilization,
    methods=["GET", "OPTIONS"],
)

api.add_api_route(
    path="/utilization/{port_id}",
    endpoint=port_utilization,
    response_model=PortUtilization,
    methods=["GET", "OPTIONS"],
)

api.add_api_route(
    path="/policy/update/",
    endpoint=update_policy,
    response_model=UpdatePolicyResponse,
    methods=["POST"],
    status_code=201,
)

api.add_api_route(
    path="/acls/update/",
    endpoint=update_acls,
    response_model=UpdatePolicyResponse,
    methods=["POST"],
    status_code=201,
)

api.add_api_route(
    path="/job/{job_id}",
    endpoint=job_status,
    response_model=UpdatePolicyResponse,
    methods=["GET"],
    status_code=200,
)


def start(**kwargs):
    """Start the web server with Uvicorn ASGI."""
    # Third Party
    import uvicorn

    uvicorn_kwargs = ASGI_PARAMS
    uvicorn_kwargs.update(kwargs)
    uvicorn.run("stats.api.main:api", **uvicorn_kwargs)
