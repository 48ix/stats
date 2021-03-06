"""Port Utilization Response Models."""

# Standard Library
import math
from typing import List

# Third Party
from pydantic import Field, BaseModel, StrictInt, StrictStr, validator


class PortUtilization(BaseModel):
    """Port utilization response model."""

    ingress: List[List] = Field(
        ..., title="Ingress Utilization", description="Actual port utilization data."
    )
    egress: List[List] = Field(
        ..., title="Egress Utilization", description="Actual port utilization data."
    )
    participant_id: StrictInt = Field(
        ...,
        title="Participant ID",
        description="Unique ID number assigned to the participant.",
    )
    port_id: StrictStr = Field(
        ...,
        title="Port ID",
        description="Unique identifier assigned to each participant port.",
    )
    location: StrictStr = Field(..., title="Location", description="IX Location ID")
    ingress_average: StrictInt = Field(..., title="Ingress Average")
    egress_average: StrictInt = Field(..., title="Egress Average")

    @validator("ingress_average", "egress_average", pre=True)
    def round_avg_bits(cls, value):
        """Round up bit floats to whole integers."""
        return math.ceil(value)

    @validator("ingress", "egress")
    def round_utilization_bits(cls, value):
        """Round up bit floats to whole integers."""
        if len(value) != 1:
            for pair in value:
                pair[1] = math.ceil(pair[1])
        return value
