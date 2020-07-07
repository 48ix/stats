"""Port Utilization Response Models."""

# Standard Library
from typing import List

# Third Party
from pydantic import Field, BaseModel, StrictInt, StrictStr


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
