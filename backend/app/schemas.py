from typing import Literal
from pydantic import BaseModel, Field

Approach = Literal["sequential", "hierarchical"]


class RunConfig(BaseModel):
    """One combination of approach and tools."""
    approach: Approach = "hierarchical"
    use_tools: bool = True


class TicketRequest(BaseModel):
    """Request body for POST /tickets/run."""
    message: str = Field(..., min_length=3, max_length=2000)
    approach: Approach = "hierarchical"
    use_tools: bool = True
    include_logs: bool = False


class CompareRequest(BaseModel):
    """Request body for POST /tickets/compare."""
    message: str = Field(..., min_length=3, max_length=2000)
    left: RunConfig = RunConfig(approach="sequential")
    right: RunConfig = RunConfig(approach="hierarchical")