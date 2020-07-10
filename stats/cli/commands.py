"""CLI Commands & Configuration."""

# Standard Library
import asyncio

# Third Party
from click import CommandCollection, group, option, argument

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
    from stats.actions.utilization import port_average_period

    echo(aiorun(port_average_period, port_id=port_id, period=time, direction=direction))


@main.command()
@option("-a", "--listen-address", default="::1", help="HTTP Listen Address")
@option("-p", "--listen-port", default=8001, help="HTTP Listen Port")
@option("-d", "--debug", default=False, is_flag=True, help="Enable debugging")
def start(listen_address, listen_port, debug):
    """Start the Stats REST API."""
    from stats.api.main import start as api_start

    echo("Starting stats API on {}:{}...", listen_address, listen_port)
    try:
        api_start(host=listen_address, port=listen_port, debug=debug)
    except Exception:
        echo.console.print_exception()


cli = CommandCollection(sources=[main])
