"""Route Policy Models."""

# Standard Library
from typing import Optional
from datetime import datetime

# Third Party
from pydantic import BaseModel, StrictInt, StrictStr, StrictBool


class UpdatePolicyResponse(BaseModel):
    """Response Model for Route Policy Update Request."""

    id: StrictInt
    in_progress: StrictBool
    detail: Optional[StrictStr]
    request_time: datetime
    complete_time: Optional[datetime]
    requestor: StrictStr
