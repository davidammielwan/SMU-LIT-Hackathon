"""Outlook / SMTP connector — email a partner when an amendment touches a
client file.

Two modes:
- Configured: SMTP_HOST/SMTP_USER/SMTP_PASS in .env sends a real message
  (smtp.office365.com:587 for Outlook / Microsoft 365).
- Unconfigured: the message is composed and stored in the outbox exactly as
  it would be sent, and marked "not sent - SMTP not configured". The brief is
  real either way, so the connector is demonstrable without live credentials.
"""
import json
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

DATA = os.path.join(os.path.dirname(__file__), "data")
OUTBOX = os.path.join(DATA, "outbox.json")
PREFS = os.path.join(DATA, "email_prefs.json")

PROVIDER_SMTP = {
    "Outlook": ("smtp.office365.com", 587),
    "Gmail": ("smtp.gmail.com", 587),
    "IMAP": (os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", "587") or 587)),
}


def _read(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def get_prefs() -> dict:
    return _read(PREFS, {"email": "", "provider": "Outlook",
                         "cadence": "The moment a client is affected",
                         "connected": False})


def save_prefs(email: str, provider: str, cadence: str) -> dict:
    prefs = {"email": email.strip(), "provider": provider, "cadence": cadence,
             "connected": bool(email.strip()),
             "smtp_ready": bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER")),
             "updated": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    _write(PREFS, prefs)
    return prefs


def compose_brief(amendment: dict, hits: list) -> tuple[str, str]:
    """Build the notification a partner actually wants: what changed, who is
    exposed, and the clause that proves it."""
    high = [h for h in hits if h.get("risk") == "high"]
    subject = (f"[Amenda] {amendment['statute']} - {len(hits)} client"
               f"{'' if len(hits) == 1 else 's'} affected"
               f"{f', {len(high)} high priority' if high else ''}")

    lines = [
        f"{amendment['statute']} - {amendment['title']}",
        f"Authority: {amendment['citation']}",
        f"In force: {amendment['force_date']}",
        "",
        amendment["summary"],
        "",
        f"{len(hits)} client file{'' if len(hits) == 1 else 's'} affected.",
        "",
    ]
    for h in hits:
        lines.append(f"--- {h['client_name']} [{h['risk'].upper()}]")
        for v in h.get("flagged_docs", []):
            lines.append(f"  {v['doc_name']} ({v['category']})")
            if v.get("clause_quote"):
                lines.append(f'    "{v["clause_quote"][:220]}"')
            if v.get("action"):
                lines.append(f"    Action: {v['action']}")
        if h.get("profile_verdict"):
            lines.append(f"  Client profile: {h['profile_verdict'].get('reason','')}")
        lines.append("")
    lines += [
        "Every flag above carries a verbatim clause quote from the document.",
        "Nothing has been changed. Open Amenda to review and approve edits.",
    ]
    return subject, "\n".join(lines)


def send(to: str, subject: str, body: str, provider: str = "Outlook") -> dict:
    """Send via SMTP if configured; otherwise record it as composed-not-sent."""
    host = os.getenv("SMTP_HOST") or PROVIDER_SMTP.get(provider, ("", 587))[0]
    port = int(os.getenv("SMTP_PORT", "0") or PROVIDER_SMTP.get(provider, ("", 587))[1])
    user, password = os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASS", "")

    record = {"to": to, "subject": subject, "body": body, "provider": provider,
              "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    if not (host and user and password):
        record["status"] = "composed - not sent (SMTP not configured)"
        record["sent"] = False
    else:
        try:
            msg = EmailMessage()
            msg["From"], msg["To"], msg["Subject"] = user, to, subject
            msg.set_content(body)
            with smtplib.SMTP(host, port, timeout=30) as s:
                s.starttls(context=ssl.create_default_context())
                s.login(user, password)
                s.send_message(msg)
            record["status"] = f"sent via {host}"
            record["sent"] = True
        except Exception as e:
            record["status"] = f"send failed: {e}"
            record["sent"] = False

    outbox = _read(OUTBOX, [])
    outbox.insert(0, record)
    _write(OUTBOX, outbox[:50])
    return record


def outbox() -> list:
    return _read(OUTBOX, [])
