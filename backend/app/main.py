import logging

from fastapi import FastAPI, HTTPException

from app.sample_tickets import SAMPLE_TICKETS
from app.schemas import TicketRequest, CompareRequest
from app.workflows.runner import run_ticket, WORKFLOWS

logger = logging.getLogger("freshkart")

app = FastAPI(
    title="FreshKart Multi-Agent Support API",
    version="1.0.0",
    description="Runs customer support tickets through sequential or hierarchical agent teams.",
)


def _safe_run(message: str, approach: str, use_tools: bool, include_logs: bool) -> dict:
    """Run a ticket and convert errors into clean HTTP errors."""
    try:
        return run_ticket(message, approach=approach, use_tools=use_tools, include_logs=include_logs)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception:
        # Log full details on the server; never send internal errors to the client
        logger.exception("Ticket processing failed")
        raise HTTPException(status_code=500, detail="We could not process this ticket. Please try again.")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/options")
def options() -> dict:
    return {"approaches": list(WORKFLOWS), "use_tools": [True, False]}


@app.get("/sample-tickets")
def sample_tickets() -> list:
    return SAMPLE_TICKETS


@app.post("/tickets/run")
def run_single(request: TicketRequest) -> dict:
    return _safe_run(request.message, request.approach, request.use_tools, request.include_logs)


@app.post("/tickets/compare")
def run_compare(request: CompareRequest) -> dict:
    # Developer-only endpoint: always includes logs for the Agent Lab
    left = _safe_run(request.message, request.left.approach, request.left.use_tools, include_logs=True)
    right = _safe_run(request.message, request.right.approach, request.right.use_tools, include_logs=True)
    return {"left": left, "right": right}