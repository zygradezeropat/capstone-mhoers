import os
import re
import requests

IPROG_API_URL = "https://sms.iprogtech.com/api/v1/sms_messages"

def _get_api_token():
    # Prefer Django settings, fallback to environment variable
    try:
        from django.conf import settings
        token = getattr(settings, "IPROG_SMS_API_TOKEN", None)
        if token:
            return token
    except Exception:
        pass
    token = os.getenv("IPROG_SMS_API_TOKEN")
    if not token:
        raise RuntimeError("IPROG SMS API token not set. Define settings.IPROG_SMS_API_TOKEN or env IPROG_SMS_API_TOKEN.")
    return token

def normalize_msisdn(phone_number: str) -> str:
    """Normalize to 63XXXXXXXXXX. Accepts 09..., +639..., 639..., or 9XXXXXXXXX."""
    if not phone_number:
        return phone_number
    digits = re.sub(r"\D+", "", phone_number)
    if digits.startswith("0"):
        return "63" + digits[1:]
    if digits.startswith("63"):
        return digits
    if digits.startswith("9") and len(digits) in (10, 11):
        return "63" + digits
    if phone_number.strip().startswith("+"):
        digits = digits.lstrip("+")
        if digits.startswith("63"):
            return digits
    return digits

def send_sms_iprog(phone_number: str, first_name: str = "", last_name: str = "", message: str = None, timeout: int = 10, sender_id: str = None):
    """
    Send an SMS using IPROG SMS API.
    If message is None, a default referral confirmation is used.

    Returns a dict with keys: ok, status_code, response, error
    """
    api_token = _get_api_token()
    msisdn = normalize_msisdn(phone_number)

    if not message:
        message = f"Hi {first_name} {last_name}, your referral has been successfully received by New Corella RHU."

    data = {
        "api_token": api_token,
        "phone_number": msisdn,
        "message": message,
    }
    if sender_id:
        data["sender_id"] = sender_id
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        resp = requests.post(IPROG_API_URL, data=data, headers=headers, timeout=timeout)
        ok = 200 <= resp.status_code < 300
        return {
            "ok": ok,
            "status_code": resp.status_code,
            "response": resp.text,
            "error": None if ok else f"HTTP {resp.status_code}"
        }
    except requests.RequestException as e:
        return {
            "ok": False,
            "status_code": None,
            "response": None,
            "error": str(e),
        }