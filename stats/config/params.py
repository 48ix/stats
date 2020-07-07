"""Validation model for Stats configuration."""

# Third Party
from pydantic import BaseModel, StrictInt, StrictStr, StrictBool, IPvAnyAddress


class DatabaseServer(BaseModel):
    """InfluxDB validation model."""

    host: StrictStr
    port: StrictInt = 8086
    ssl: StrictBool = False

    def __str__(self):
        """Build an HTTP client friendly string based on DB parameters."""
        template = "http{protocol}://{host}{port}"
        protocol = ""
        port = ""
        no_port = (80, 443)

        if self.ssl:
            protocol = "s"
        if self.port not in no_port:
            port = f":{self.port}"
        return template.format(protocol=protocol, host=str(self.host), port=port)


class Api(BaseModel):
    """REST API configuration parameters validation model."""

    title: StrictStr = "Stats API"
    description: StrictStr = "IX Statistics"
    default_period: StrictInt = 8


class Params(BaseModel):
    """General app-wide configuration parameters validation model."""

    debug: StrictBool = False
    db: DatabaseServer
    api: Api = Api()
    listen_address: IPvAnyAddress = "::1"
    listen_port: StrictInt = 8001
