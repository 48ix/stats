"""CLI Commands & Configuration."""

# Standard Library
import asyncio

# Third Party
from click import CommandCollection, group, option, prompt, argument

# Project
from stats.cli.echo import Echo

echo = Echo()


@group()
def main():
    """Initialize CLI commands."""
    pass


def aiorun(coro, *args, **kwargs):
    """Safely await a coroutine with arguments, print a pretty response."""
    try:
        res = asyncio.run(coro(*args, **kwargs))
        return res
    except Exception:
        echo.console.print_exception()


@main.command()
@argument("port-id")
@option("-t", "--time", help="Number of previous hours to query")
@option("-d", "--direction", required=True, help="In or Out")
def port_utilization(port_id, time, direction):
    """Get utilization statistics for a port."""
    # Project
    from stats.actions.utilization import port_utilization_period

    echo(
        aiorun(
            port_utilization_period, port_id=port_id, period=time, direction=direction
        )
    )


@main.command()
@argument("port-id")
@option("-t", "--time", default=1, help="Number of previous hours to query")
@option("-d", "--direction", required=True, help="In or Out")
def port_average(port_id, time, direction):
    """Get utilization statistics for a port."""
    # Project
    from stats.actions.utilization import port_average_period

    echo(aiorun(port_average_period, port_id=port_id, period=time, direction=direction))


@main.command()
@option("-a", "--listen-address", default="::1", help="HTTP Listen Address")
@option("-p", "--listen-port", default=8001, help="HTTP Listen Port")
@option("-d", "--debug", default=False, is_flag=True, help="Enable debugging")
def start(listen_address, listen_port, debug):
    """Start the Stats REST API."""
    # Project
    from stats.api.main import start as api_start

    echo("Starting stats API on {}:{}...", listen_address, listen_port)
    try:
        api_start(host=listen_address, port=listen_port, debug=debug)
    except Exception:
        echo.console.print_exception()


@main.command()
def create_api_user():
    """Create an API User."""

    # Standard Library
    import secrets

    # Project
    from stats.auth.main import authdb_stop, create_user, authdb_start

    async def _create(_user, _key):
        await authdb_start()
        await create_user(_user, _key)
        await authdb_stop()

    username = prompt("Username", type=str)
    key = secrets.token_urlsafe(16)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_create(username, key))

    echo(
        """Generated API User:
  Username: {}
  API Key: {}
    """,
        username,
        key,
    )


@main.command()
@argument("route")
def create_api_route(route):
    """Create an API Route."""

    # Project
    from stats.auth.main import authdb_stop, authdb_start, create_route

    async def _create(_route):
        await authdb_start()
        await create_route(_route)
        await authdb_stop()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_create(route))

    echo("Generated API Route {}", route)


@main.command()
@argument("route")
@argument("username")
def route_to_user(route, username):
    """Associate a route with a username."""

    # Project
    from stats.auth.main import authdb_stop, authdb_start, associate_route

    async def _create(_route, _user):
        await authdb_start()
        await associate_route(_user, [_route])
        await authdb_stop()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_create(route, username))

    echo("Associated Route {} with user {}", route, username)


cli = CommandCollection(sources=[main])
