import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
RUN_TIMEOUT_SECONDS = 180


class BackendError(Exception):
    """Raised when the backend cannot be reached or returns an error."""


def _handle(response: requests.Response):
    if response.ok:
        return response.json()
    try:
        detail = response.json().get("detail", response.text)
    except ValueError:
        detail = response.text
    raise BackendError(f"{response.status_code}: {detail}")


def _request(method: str, path: str, payload: dict | None = None, timeout: int = 10):
    try:
        response = requests.request(method, f"{BACKEND_URL}{path}", json=payload, timeout=timeout)
    except requests.ConnectionError:
        raise BackendError("Cannot reach the backend. Is the FastAPI server running on port 8000?")
    except requests.Timeout:
        raise BackendError("The backend took too long to respond. Please try again.")
    return _handle(response)


def check_health() -> bool:
    try:
        return _request("GET", "/health").get("status") == "ok"
    except BackendError:
        return False


def get_sample_tickets() -> list:
    return _request("GET", "/sample-tickets")


def get_options() -> dict:
    return _request("GET", "/options")


def run_ticket(message: str, approach: str = "hierarchical",
               use_tools: bool = True, include_logs: bool = False) -> dict:
    payload = {
        "message": message,
        "approach": approach,
        "use_tools": use_tools,
        "include_logs": include_logs,
    }
    return _request("POST", "/tickets/run", payload, timeout=RUN_TIMEOUT_SECONDS)


def compare_tickets(message: str, left: dict, right: dict) -> dict:
    payload = {"message": message, "left": left, "right": right}
    return _request("POST", "/tickets/compare", payload, timeout=RUN_TIMEOUT_SECONDS * 2)