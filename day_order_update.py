import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Day order list
day_orders = ["I", "II", "III", "IV", "V", "VI"]

def update_day_order():
    doc_ref = db.collection("settings").document("dayOrder")
    doc = doc_ref.get()

    today = datetime.now()
    today_key = today.strftime("%Y-%m-%d")

    if not doc.exists:
        # First time setup
        doc_ref.set({
            "current": "I",
            "lastUpdatedDate": today_key,
            "rotationEnabled": True
        })
        print("Created dayOrder document with I")
        return

    data = doc.to_dict()
    current_day = data.get("current", "I")
    last_updated_str = data.get("lastUpdatedDate")

    last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d") if last_updated_str else today

    # Count non-Sunday days passed
    temp = last_updated
    days_passed = 0
    while temp.date() < today.date():
        temp += timedelta(days=1)
        if temp.weekday() != 6:  # Sunday is 6
            days_passed += 1

    if days_passed > 0:
        index = day_orders.index(current_day)
        current_day = day_orders[(index + days_passed) % len(day_orders)]
        doc_ref.update({
            "current": current_day,
            "lastUpdatedDate": today_key,
            "updatedAt": firestore.SERVER_TIMESTAMP
        })
        print(f"Day order updated to {current_day}")
    else:
        print(f"No change, day order remains {current_day}")

if __name__ == "__main__":
    update_day_order()
