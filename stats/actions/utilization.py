"""Utilization Actions."""

# Third Party
import pendulum

# Project
from stats.database.driver import Influx


async def port_utilization_period(port_id: str, direction: str, period: int):
    """Get port utilization by relative time period in hours."""
    async with Influx("telegraf") as db:
        q = (
            db.SELECT(f"derivative(max(bytes{direction.title()}), 1s) * 8")
            .FROM("interfaces")
            .LAST(period)
            .WHERE(port_id=port_id)
            .GROUP("port_id", "participant_id")
            .FILL("none")
        )
        return await q.query()


async def port_utilization_range(port_id: str, direction: str, start: str, end=None):
    """Get port utilization by date range."""
    async with Influx("telegraf") as db:
        q = (
            db.SELECT(f"derivative(max(bytes{direction.title()}), 1s) * 8")
            .FROM("interfaces")
            .BETWEEN(start, end)
            .WHERE(port_id=port_id)
            .GROUP("port_id", "participant_id")
            .FILL("none")
        )
        return await q.query()


async def port_average_period(port_id: str, direction: str, period: int):
    """Get port utilization average by relative time period in hours."""
    parts = (
        "SELECT mean(*) from ",
        f"(SELECT derivative(max(bytes{direction.title()}), 1s) * 8",
        f"FROM interfaces WHERE port_id='{port_id}' AND",
        f"time > now() - {period}h GROUP BY time(1m) fill(previous))",
    )
    async with Influx("telegraf") as db:
        return await db.query(raw=" ".join(parts))


async def port_average_range(port_id: str, direction: str, start: str, end=None):
    """Get port utilization average by date range."""
    start_time = pendulum.parse(start, tz="UTC", strict=False)
    parts = (
        "SELECT mean(*) from ",
        f"(SELECT derivative(max(bytes{direction.title()}), 1s) * 8",
        f"FROM interfaces WHERE port_id='{port_id}' AND",
        f"time >= '{start_time.to_rfc3339_string()}'",
    )
    if end:
        end_time = pendulum.parse(end, tz="UTC", strict=False)
        parts += (f"AND time <= '{end_time.to_rfc3339_string()}'",)
    parts += ("GROUP BY time(1m) fill(previous))",)

    async with Influx("telegraf") as db:
        return await db.query(raw=" ".join(parts))


async def overall_utilization_period(direction: str, period: int):
    """Get IX-wide utilization by relative time period in hours."""
    async with Influx("telegraf") as db:
        q = (
            db.SELECT(f"derivative(max(bytes{direction.title()}), 1s) * 8")
            .FROM("interfaces")
            .LAST(period)
            .GROUP("port_id")
            .FILL("none")
        )
        return await q.query()


async def overall_utilization_average_period(direction: str, period: int):
    """Get IX-wide utilization average by relative time period in hours."""
    parts = (
        "SELECT mean(*) from ",
        f"(SELECT derivative(max(bytes{direction.title()}), 1s) * 8",
        "FROM interfaces WHERE",
        f"time > now() - {period}h GROUP BY time(1m) fill(previous))",
    )
    async with Influx("telegraf") as db:
        return await db.query(raw=" ".join(parts))


async def overall_utilization_max_period(direction: str, period: int):
    """Get IX-wide utilization peak by relative time period in hours."""
    parts = (
        "SELECT max(*) from ",
        f"(SELECT derivative(max(bytes{direction.title()}), 1s) * 8",
        "FROM interfaces WHERE",
        f"time > now() - {period}h GROUP BY time(1m) fill(previous))",
    )
    async with Influx("telegraf") as db:
        return await db.query(raw=" ".join(parts))
