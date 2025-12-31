from pydantic import BaseModel
from typing import Literal

class ApiResponse(BaseModel):
    status:      Literal["success", "error"] = "success"
    message:     str
    data:        dict = None