import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

# ======================================================
# Firebase Initialization
# ======================================================
if not firebase_admin._apps:
    cred_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")

    if cred_json:
        cred = credentials.Certificate(json.loads(cred_json))
    else:
        # LOCAL fallback (only for your PC)
        cred = credentials.Certificate("serviceAccountKey.json")

    firebase_admin.initialize_app(cred)

db = firestore.client()

# ======================================================
# Day Order Setup
# ======================================================
DAY_ORDERS = ["I", "II", "III", "IV", "V", "VI"]

# ======================================================
# Helper: Count working days (skip Sundays)
# ======================================================
def count_working_days(start_date, end_date):
    days = 0
    cur = start_date

    while cur < end_date:
        cur += timedelta(days=1)
        if cur.weekday() != 6:  # Sunday
            days += 1

    return days

# ======================================================
# Main Logic
# ======================================================
def update_day_order():
    today = datetime.now().date()

    # 🚫 Sunday → do nothing
    if today.weekday() == 6:
        print("⛔ Sunday detected. Day order not updated.")
        return

    today_str = today.strftime("%Y-%m-%d")
    doc_ref = db.collection("settings").document("dayOrder")
    doc = doc_ref.get()

    # ---------- First time setup ----------
    if not doc.exists:
        doc_ref.set({
            "current": "I",
            "lastUpdatedDate": today_str,
            "autoUpdated": True,
            "history": [],
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        print("✅ First run: Day order set to I")
        return

    data = doc.to_dict()

    current_day = data.get("current")
    last_updated_str = data.get("lastUpdatedDate")

    # Safety: if current is missing or None
    if current_day not in DAY_ORDERS:
        current_day = "I"

    if last_updated_str:
        last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d").date()
    else:
        last_updated = today

    days_passed = count_working_days(last_updated, today)

    if days_passed <= 0:
        print(f"ℹ️ No update needed. Current day order: {current_day}")
        return

    new_index = (DAY_ORDERS.index(current_day) + days_passed) % len(DAY_ORDERS)
    new_day = DAY_ORDERS[new_index]

    doc_ref.update({
        "current": new_day,
        "lastUpdatedDate": today_str,
        "updatedAt": firestore.SERVER_TIMESTAMP,
        "history": firestore.ArrayUnion([
            {"date": today_str, "day": new_day}
        ])
    })

    print(f"🚀 Day order updated: {current_day} → {new_day}")

# ======================================================
# Run
# ======================================================
if __name__ == "__main__":
    update_day_order()
