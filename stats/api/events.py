"""FastAPI Events."""

# Project
from stats.auth.main import authdb_stop, authdb_start


async def startup_authdb() -> None:
    """Connect to auth database on startup."""
    await authdb_start()


async def shutdown_authdb() -> None:
    """Disconnect from auth database on shutdown."""
    await authdb_stop()
