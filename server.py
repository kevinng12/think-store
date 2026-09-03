import json
import os
import re
from typing import Optional

import gspread
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file, session
from google.oauth2 import service_account

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET", "change-me-in-production")

APP_USERNAME = os.getenv("APP_USERNAME", "admin")
APP_PASSWORD = os.getenv("APP_PASSWORD", "admin123")
DEFAULT_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
DEFAULT_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Sheet1")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def parse_sheet_url(url: str) -> tuple[str, str]:
    cleaned = (url or "").strip()
    if not cleaned:
        raise ValueError("Sheet link is required.")

    match = re.search(r"/spreadsheets/d/([A-Za-z0-9-_]+)", cleaned)
    if not match:
        raise ValueError("Please provide a valid Google Sheets link.")

    sheet_id = match.group(1)
    return sheet_id, DEFAULT_SHEET_NAME


def get_active_sheet_id() -> str:
    if session.get("sheet_id"):
        return session["sheet_id"]
    if DEFAULT_SHEET_ID:
        return DEFAULT_SHEET_ID
    raise RuntimeError("No Google Sheet configured. Set GOOGLE_SHEET_ID or provide a valid sheet link after logging in.")


def get_active_sheet_name() -> str:
    return session.get("sheet_name") or DEFAULT_SHEET_NAME


def get_credentials():
    if SERVICE_ACCOUNT_JSON:
        info = json.loads(SERVICE_ACCOUNT_JSON)
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

    if SERVICE_ACCOUNT_FILE:
        return service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    raise RuntimeError(
        "Missing Google auth configuration. Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON."
    )


def get_worksheet(sheet_id: Optional[str] = None, sheet_name: Optional[str] = None):
    active_sheet_id = sheet_id or get_active_sheet_id()
    active_sheet_name = sheet_name or get_active_sheet_name()

    credentials = get_credentials()
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(active_sheet_id)
    return spreadsheet.worksheet(active_sheet_name)


@app.get("/")
def index_page():
    return send_file(os.path.join(BASE_DIR, "index.html"))


@app.get("/sheet.html")
def sheet_page():
    return send_file(os.path.join(BASE_DIR, "sheet.html"))


@app.get("/styles.css")
def styles_page():
    return send_file(os.path.join(BASE_DIR, "styles.css"))


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()

    if username == APP_USERNAME and password == APP_PASSWORD:
        session["logged_in"] = True
        return jsonify({"success": True, "message": "Logged in successfully."})

    return jsonify({"error": "Invalid username or password."}), 401


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"success": True})


@app.get("/api/session")
def session_status():
    return jsonify({"loggedIn": bool(session.get("logged_in"))})


@app.post("/api/sheet-config")
def set_sheet_config():
    if not session.get("logged_in"):
        return jsonify({"error": "Login required."}), 401

    payload = request.get_json(silent=True) or {}
    sheet_url = (payload.get("sheetUrl") or "").strip()
    if not sheet_url:
        return jsonify({"error": "A Google Sheet link is required."}), 400

    try:
        sheet_id, sheet_name = parse_sheet_url(sheet_url)
        session["sheet_id"] = sheet_id
        session["sheet_name"] = sheet_name
        return jsonify({"success": True, "sheetId": sheet_id, "sheetName": sheet_name})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.get("/api/sheet")
def read_sheet():
    if not session.get("logged_in"):
        return jsonify({"error": "Login required."}), 401

    try:
        worksheet = get_worksheet()
        rows = worksheet.get_all_records()
        return jsonify(rows)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/sheet")
def write_sheet():
    if not session.get("logged_in"):
        return jsonify({"error": "Login required."}), 401

    try:
        payload = request.get_json(silent=True) or {}
        if not payload:
            return jsonify({"error": "Request body is required."}), 400

        name = (payload.get("Name") or payload.get("name") or "").strip()
        grade = (payload.get("Grade") or payload.get("grade") or "").strip()
        balance = (payload.get("Balance") or payload.get("balance") or "").strip()

        if not name or not grade or not balance:
            return jsonify({"error": "Name, Grade, and Balance are required."}), 400

        worksheet = get_worksheet()
        worksheet.append_row([name, grade, balance])
        return jsonify({"success": True, "row": [name, grade, balance]}), 201
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
