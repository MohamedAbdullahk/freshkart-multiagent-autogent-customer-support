import json
from app.tools.order_tools import (
    get_order_details,
    get_payment_history,
    get_system_status,
    get_store_info,
    get_policy,
)

def show(title, result):
    print(f"\n=== {title} ===")
    print(json.dumps(json.loads(result), indent=2))

show("T1: Order details (#fk1023)", get_order_details("#fk1023"))
show("T1: Payment history", get_payment_history("FK1023"))
show("T1: Duplicate charge policy", get_policy("duplicate_charge"))
show("T2: OTP service status", get_system_status("otp_service"))
show("T3: Store info", get_store_info())
show("Wrong order ID", get_order_details("FK9999"))