"""InfluxDB driver."""

# Third Party
import pendulum

# Project
from stats.log import log as _logger
from stats.util import intersperse, clean_keyname
from stats.config import params
from stats.constants import __version__
from stats.exceptions import StatsError
from stats.http.client import BaseHttpClient


class Influx(BaseHttpClient):
    """Communicate with InfluxDB via BaseHTTPClient."""

    def __init__(self, database, *args, **kwargs):
        """Initialize Influx()."""
        super().__init__(
            *args,
            base_url=str(params.db),
            verify_ssl=False,
            logger=_logger,
            user_agent=f"48-IX-Stats/{__version__}",
            exception_class=StatsError,
            **kwargs,
        )
        self.database = clean_keyname(database)
        self.start_time = None
        self.end_time = None
        self.period = None
        self.selections = None
        self.where = None
        self.measurement = None
        self.granularity = 10
        self.group_by = None
        self.fill = None

    async def _parse(self, response):
        try:
            results = response.get("results", [{}])[0]
            if "error" in results:
                self.log.critical(results["error"])
                series = [{}]
            else:
                series = results.get("series", [{}])
        except (KeyError, IndexError):
            series = [{}]
        return series[0]

    async def running(self):
        """Ensure InfluxDB is running."""
        res = await self._asession.get("/ping")

        if res.status_code not in (200, 204):
            raise StatsError("Database is not running")

        return True

    def _build_query(self):
        """Construct an InfluxDB-compatible line-protocol query string."""
        query = ["SELECT", ",".join(str(s) for s in self.selections)]
        query.extend(["FROM", str(self.measurement)])

        where = []

        if self.where:
            where.extend([f"{k}='{v}'" for k, v in self.where.items()])

        if self.period:
            where.append(f"time > now() - {self.period}")

        elif self.start_time:
            start = self.start_time.in_timezone("UTC").to_rfc3339_string()
            where.append(f"time >= '{start}'")

            if self.end_time:
                end = self.end_time.in_timezone("UTC").to_rfc3339_string()
                where.append(f"time <= '{end}'")

        if len(query) != 0:
            where = intersperse(where, "AND")
            where.insert(0, "WHERE")
            query.append(" ".join(where))

        if self.group_by:
            query.append(self.group_by)

        if self.fill:
            query.append(self.fill)

        query_string = " ".join(str(i) for i in query)

        return query_string

    async def query(self, raw=False):
        """Execute the query."""
        await self.running()
        if raw:
            query = raw
        else:
            query = self._build_query()

        self.log.info(query)
        response = await self._aget("query", params={"q": query, "db": self.database})

        return await self._parse(response)

    def SELECT(self, *selections):
        """Set selections, like 'SELECT <selection>' in line-protocol."""
        if selections.count == 0:
            selections = ("*",)
        self.selections = selections
        return self

    def FROM(self, measurement):
        """Set measurements, like 'SELECT <s> FROM <measurement>' in line-protocol."""
        self.measurement = measurement
        return self

    def LAST(self, hours: int):
        """Set relative time period."""
        hours = int(hours)
        self.period = f"{hours}h"
        return self

    def BETWEEN(self, start_time, end_time=None):
        """Set time range."""
        self.start_time = pendulum.parse(start_time, tz="Etc/UTC")
        self.end_time = end_time or pendulum.now("Etc/UTC")
        return self

    def WHERE(self, tags=None, **kwargs):
        """Set tag match conditions."""
        where = {}

        if isinstance(tags, dict):
            where.update(tags)

        where.update(kwargs)

        self.where = where
        return self

    def GROUP(self, *items, time=True):
        """Set 'GROUP BY'."""
        group = [*items]
        if time:
            group.append(f"time({self.granularity}s)")
        group = intersperse(group, ",")
        group.insert(0, "GROUP BY")
        self.group_by = " ".join(group)
        return self

    def FILL(self, item):
        """Set 'FILL' function."""
        self.fill = f"FILL({item})"
        return self
