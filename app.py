
from flask import Flask, request, jsonify
from flask_cors import CORS
import random, smtplib, time
from email.message import EmailMessage
import firebase_admin
from firebase_admin import credentials, firestore

# ================= Flask App =================
app = Flask(__name__)
CORS(app)  # ⚡ Enable CORS for all routes

# ================= Firebase Admin =================
cred = credentials.Certificate("serviceAccountKey.json")  # 🔹 Your Firebase service account
firebase_admin.initialize_app(cred)
db = firestore.client()

# ================= In-Memory OTP Storage =================
otp_store = {}  # {email: {"otp": "123456", "expires": timestamp}}

# ================= Email Config =================
EMAIL = "anupriyac316@gmail.com"          # 🔹 Your Gmail
APP_PASSWORD = "xqxx ohgu yhre ucco"     # 🔹 Gmail App Password

def send_email(to_email, otp):
    """Send OTP email via Gmail"""
    msg = EmailMessage()
    msg["Subject"] = "CASC Admin Login OTP"
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg.set_content(f"""
Your OTP to login as admin is:

{otp}

This OTP is valid for 5 minutes.
If you didn't request this, ignore this email.
""")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print(f"OTP sent to {to_email}: {otp}")
    except Exception as e:
        print(f"Failed to send email: {e}")

# ================= Routes =================

@app.route("/send-login-otp", methods=["POST"])
def send_login_otp():
    """Send OTP to admin email"""
    email = request.json.get("email")
    if not email:
        return jsonify({"success": False, "message": "Email is required"}), 400

    # Check if email exists and role is admin
    users = db.collection("users").where("email", "==", email).where("role", "==", "admin").stream()
    if not any(users):
        return jsonify({"success": False, "message": "Email not registered as admin"}), 403

    # Generate 6-digit OTP
    otp = random.randint(100000, 999999)
    otp_store[email] = {"otp": str(otp), "expires": time.time() + 300}  # 5 min expiry

    send_email(email, otp)
    return jsonify({"success": True, "message": "OTP sent to email"})

@app.route("/verify-login-otp", methods=["POST"])
def verify_login_otp():
    """Verify OTP"""
    email = request.json.get("email")
    otp = request.json.get("otp")

    if not email or not otp:
        return jsonify({"success": False, "message": "Email and OTP required"}), 400

    data = otp_store.get(email)
    if not data:
        return jsonify({"success": False, "message": "No OTP found for this email"}), 400

    if time.time() > data["expires"]:
        del otp_store[email]
        return jsonify({"success": False, "message": "OTP expired"}), 400

    if data["otp"] != otp:
        return jsonify({"success": False, "message": "Invalid OTP"}), 400

    # OTP verified → remove it
    del otp_store[email]
    return jsonify({"success": True, "message": "OTP verified"})

# ================= Run Flask =================
if __name__ == "__main__":
    print("Starting Flask OTP login server on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
