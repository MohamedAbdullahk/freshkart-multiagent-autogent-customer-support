import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

# Load the database file once when the module is imported
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "freshkart_db.json"

with open(DB_PATH, encoding="utf-8") as f:
    DB = json.load(f)

# Business rule values. Keep them in sync with the policy texts in freshkart_db.json.
REFUND_TIMELINE = "5-7 working days"
LATE_DELIVERY_THRESHOLD_MINUTES = 60
LATE_DELIVERY_CREDIT = 50


def _clean_order_id(order_id: str) -> str:
    """Normalize order IDs, e.g. '#fk1023 ' -> 'FK1023'."""
    return order_id.strip().upper().replace("#", "")


def _minutes_between(start: str, end: str) -> int:
    """Minutes from start to end, for timestamps like '2026-09-29 09:30'."""
    fmt = "%Y-%m-%d %H:%M"
    delta = datetime.strptime(end, fmt) - datetime.strptime(start, fmt)
    return int(delta.total_seconds() // 60)


def _resolution_rules(order_status: str, total_debited: int, extra: int) -> tuple[list, list]:
    """Business rules: which payment options and policies apply. Decided in code, not by the LLM."""
    options = []
    policies = []

    if extra > 0:
        policies.append("duplicate_charge")

    if order_status == "PAYMENT_FAILED" and total_debited > 0:
        policies.append("failed_order_refund")
        if extra > 0:
            options.append(f"Confirm the order and get the extra Rs. {extra} refunded within {REFUND_TIMELINE}")
        else:
            options.append("Confirm the order with the payment already made")
        options.append(f"Cancel the order and get the full Rs. {total_debited} refunded within {REFUND_TIMELINE}")
    elif extra > 0:
        options.append(f"The extra Rs. {extra} will be refunded automatically within {REFUND_TIMELINE} (no action needed)")

    return options, policies


def get_order_details(
    order_id: Annotated[str, "FreshKart order ID, for example FK1023"],
) -> str:
    """Order details: items, total amount, and current order status."""
    oid = _clean_order_id(order_id)
    order = DB["orders"].get(oid)
    if not order:
        return json.dumps({"found": False, "message": f"Order {oid} not found"})
    return json.dumps({"found": True, "order_id": oid, **order})


def get_payment_history(
    order_id: Annotated[str, "FreshKart order ID, for example FK1023"],
) -> str:
    """Payment transactions for an order, with duplicate charge detection, the allowed resolution options, and the policies that apply."""
    oid = _clean_order_id(order_id)
    txns = DB["payments"].get(oid)
    if txns is None:
        return json.dumps({"found": False, "message": f"No payments found for {oid}"})

    order = DB["orders"].get(oid, {})
    order_status = order.get("order_status", "unknown")
    order_total = order.get("total_amount", 0)
    successful = [t for t in txns if t["status"] == "SUCCESS"]
    total_debited = sum(t["amount"] for t in successful)
    extra = max(total_debited - order_total, 0)
    options, policies = _resolution_rules(order_status, total_debited, extra)

    return json.dumps({
        "found": True,
        "order_id": oid,
        "customer_name": order.get("customer_name", "unknown"),
        "order_status": order_status,
        "order_total": order_total,
        "transactions": txns,
        "successful_debit_count": len(successful),
        "total_debited": total_debited,
        "duplicate_charge_detected": len(successful) > 1,
        "extra_amount_debited": extra,
        "resolution_options": options,
        "applicable_policies": policies,
    })


def get_delivery_status(
    order_id: Annotated[str, "FreshKart order ID, for example FK1025"],
) -> str:
    """Live delivery status for an order: status, ETA, delay in minutes, late-delivery compensation, and the policies that apply."""
    oid = _clean_order_id(order_id)
    delivery = DB["deliveries"].get(oid)
    if not delivery:
        return json.dumps({"found": False, "message": f"No delivery record for {oid}"})

    order = DB["orders"].get(oid, {})
    result = {
        "found": True,
        "order_id": oid,
        "customer_name": order.get("customer_name", "unknown"),
        **delivery,
        "delay_minutes": 0,
        "compensation": "none",
        "applicable_policies": [],
    }

    # Business rule: more than 60 minutes late earns a credit
    if delivery.get("promised_by") and delivery.get("eta"):
        delay = max(_minutes_between(delivery["promised_by"], delivery["eta"]), 0)
        result["delay_minutes"] = delay
        if delay > LATE_DELIVERY_THRESHOLD_MINUTES:
            result["compensation"] = f"Rs. {LATE_DELIVERY_CREDIT} FreshKart credit, added automatically after delivery"
            result["applicable_policies"] = ["late_delivery"]

    return json.dumps(result)


def get_system_status(
    service: Annotated[str, "Service name: 'otp_service' or 'payment_gateway'"],
) -> str:
    """Current health status of a FreshKart system."""
    status = DB["system_status"].get(service.strip().lower())
    if not status:
        return json.dumps({"found": False, "message": f"Unknown service: {service}"})
    return json.dumps({"found": True, "service": service, **status})


def get_store_info() -> str:
    """Delivery hours, support hours, and service area."""
    return json.dumps(DB["store_info"])


def get_policy(
    topic: Annotated[str, "Policy topic: 'duplicate_charge', 'failed_order_refund', 'late_delivery', or 'privacy'"],
) -> str:
    """Official FreshKart policy text for a topic."""
    policy = DB["policies"].get(topic.strip().lower())
    if not policy:
        return json.dumps({"found": False, "message": f"No policy for topic: {topic}"})
    return json.dumps({"found": True, "topic": topic, "policy": policy})