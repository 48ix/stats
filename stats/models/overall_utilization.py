"""IX-Wide Utilization Response Models."""

# Standard Library
import math
from typing import List

# Third Party
from pydantic import Field, BaseModel, StrictInt, validator


class OverallUtilization(BaseModel):
    """IX-Wide utilization response model."""

    ingress: List[List] = Field(
        ..., title="Ingress Utilization", description="Actual port utilization data."
    )
    egress: List[List] = Field(
        ..., title="Egress Utilization", description="Actual port utilization data."
    )
    ingress_average: StrictInt = Field(..., title="Ingress Average")
    egress_average: StrictInt = Field(..., title="Egress Average")
    ingress_peak: StrictInt = Field(..., title="Peak Ingress Utilization")

    @validator("ingress_average", "egress_average", "ingress_peak", pre=True)
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
