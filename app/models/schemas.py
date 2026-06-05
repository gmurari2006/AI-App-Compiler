from pydantic import BaseModel
from typing import List


class IntentSchema(BaseModel):
    app_type: str
    features: List[str]
    roles: List[str]