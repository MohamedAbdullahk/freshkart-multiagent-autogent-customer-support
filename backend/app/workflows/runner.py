import contextlib
import io
import time

from app.workflows.sequential import run_sequential
from app.workflows.hierarchical import run_hierarchical
from app.workflows.results import build_result

# Approach name -> workflow function
WORKFLOWS = {
    "sequential": run_sequential,
    "hierarchical": run_hierarchical,
}


def run_ticket(ticket: str, approach: str = "hierarchical", use_tools: bool = True,
               include_logs: bool = True, verbose: bool = False) -> dict:
    """Single entry point used by the API: run one ticket with the chosen approach."""
    if approach not in WORKFLOWS:
        raise ValueError(f"Unknown approach '{approach}'. Choose one of: {', '.join(WORKFLOWS)}")
    if not ticket or not ticket.strip():
        raise ValueError("Ticket text cannot be empty.")

    start = time.perf_counter()
    workflow = WORKFLOWS[approach]
    if verbose:
        output = workflow(ticket.strip(), use_tools=use_tools, verbose=True)
    else:
        # Hide AutoGen's console output (API and UI do not need it)
        with contextlib.redirect_stdout(io.StringIO()):
            output = workflow(ticket.strip(), use_tools=use_tools, verbose=False)
    duration = time.perf_counter() - start

    return build_result(
        messages=output["messages"],
        approach=approach,
        use_tools=use_tools,
        guardrail_events=output["guardrail_events"],
        duration_seconds=duration,
        include_logs=include_logs,
    )