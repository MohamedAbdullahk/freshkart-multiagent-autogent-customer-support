from app.sample_tickets import SAMPLE_TICKETS

# Test runners use {"T1": "message", ...}
TICKETS = {ticket["id"]: ticket["message"] for ticket in SAMPLE_TICKETS}