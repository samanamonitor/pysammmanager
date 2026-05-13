# token_utils.py
import hmac
import hashlib
import time
import base64
import json
import os
import logging

SECRET_KEY = os.environ.get("SAMM_SECRET", "change-me-to-something-strong")

log = logging.getLogger(__name__)

def gettoken(**kwargs):
    user = kwargs.get("user", "")
    if isinstance(user, list):
        user = "".join(user)
    dashboard = kwargs.get("dashboard", "")
    if isinstance(dashboard, list):
        dashboard = "".join(dashboard)
    t = generate_token(user, dashboard)
    body = json.dumps({"token": t})
    return ("200 OK",
        [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body)))
        ], [body.encode('utf-8')])

def generate_token(user: str, dashboard: str, ttl_seconds: int = 300) -> str:
    """
    Create a short-lived signed token encoding the user identity.
    Format: base64(payload_json).base64(hmac_signature)
    """
    payload = {
        "user":      user,
        "dashboard": dashboard,
        "exp":       int(time.time()) + ttl_seconds,
    }
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode()

    sig = hmac.new(
        SECRET_KEY.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode()

    return f"{payload_b64}.{sig_b64}"


def verify_token(token) -> dict | None:
    """
    Verify signature and expiry. Returns the payload dict or None if invalid.
    """
    if isinstance(token, list) and len(token) > 0:
        token = token[0]

    try:
        payload_b64, sig_b64 = token.split(".", 1)
    except ValueError:
        log.error("Invalid token syntax. token='%s'", token)
        return None

    expected_sig = hmac.new(
        SECRET_KEY.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).digest()
    expected_b64 = base64.urlsafe_b64encode(expected_sig).decode()

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(sig_b64, expected_b64):
        log.error("Invalid token digest. token='%s'", token)
        return None

    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    log.debug("payload=%s" % payload)

    if time.time() > payload.get("exp", 0):
        log.error("Expired token. token='%s' payload='%s'", token, payload)
        return None

    allowed_dashboards=[
        "SAMM Windows Credentials Update",
        "SAMM Administration"
    ]
    dashboard = payload.get("dashboard", "")
    if dashboard not in allowed_dashboards:
        log.error("Invalid dashboard. payload='%s'", payload)
        return None

    return payload