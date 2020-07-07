"""Utilization Actions."""

# Project
from stats.database.driver import Influx


async def port_utilization_period(port_id: str, direction: str, period: int):
    """Get port utilization by relative time period in hours."""
    async with Influx("telegraf") as db:
        q = (
            db.SELECT(f"derivative(max(bytes{direction.title()}), 1s)")
            .FROM("interfaces")
            .LAST(period)
            .WHERE(port_id=port_id)
            .GROUP("port_id", "participant_id")
        )
        return await q.query()


async def port_utilization_range(port_id: str, direction: str, start: str, end=None):
    """Get port utilization by date range."""
    async with Influx("telegraf") as db:
        q = (
            db.SELECT(f"derivative(max(bytes{direction.title()}), 1s)")
            .FROM("interfaces")
            .BETWEEN(start, end)
            .WHERE(port_id=port_id)
            .GROUP("port_id", "participant_id")
        )
        return await q.query()
