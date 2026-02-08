from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import random, time
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

EMAIL = "anupriyac316@gmail.com"          # 🔹 Your Gmail
APP_PASSWORD = "xqxx ohgu yhre ucco"

def send_otp_email(email, otp):
    msg = EmailMessage()
    msg["Subject"] = "CASC Kalvisalai 2.O – Admin Login Verification"
    msg["From"] = EMAIL
    msg["To"] = email
    msg.set_content(f"""
Dear Administrator,

Your One-Time Password (OTP) for secure admin login to
CASC Kalvisalai 2.O is:

━━━━━━━━━━━━━━━━━━
   🔐 {otp}
━━━━━━━━━━━━━━━━━━

⏳ This OTP is valid for 5 minutes.
⚠️ Do not share this code with anyone.

Warm regards,
CASC Kalvisalai 2.O

""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, APP_PASSWORD)
        server.send_message(msg)

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    uid = data["uid"]
    email = data["email"]

    otp = str(random.randint(100000, 999999))
    expires = time.time() + 300

    db.collection("admin_otps").document(uid).set({
        "otp": otp,
        "expiresAt": expires
    })

    send_otp_email(email, otp)
    return jsonify({"success": True})

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    uid = data["uid"]
    entered_otp = data["otp"]

    doc = db.collection("admin_otps").document(uid).get()
    if not doc.exists:
        return jsonify({"success": False})

    d = doc.to_dict()
    if time.time() > d["expiresAt"]:
        return jsonify({"success": False, "message": "Expired"})

    if d["otp"] == entered_otp:
        db.collection("admin_otps").document(uid).delete()
        return jsonify({"success": True})

    return jsonify({"success": False})

if __name__ == "__main__":
    app.run(port=5000, debug=True)
