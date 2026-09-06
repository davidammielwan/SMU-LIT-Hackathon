"""Propagation — turn a flagged document into a concrete proposed edit.

The sweep says a clause is wrong. This says what it should say instead, as a
word-level diff a lawyer can read, approve or reject. Nothing is ever applied
automatically: every proposal carries a status and an audit entry.
"""
import difflib
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm import chat_json, LLMNotConfigured

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
STORE = os.path.join(DATA, "proposals.json")

SYSTEM = """You are a Singapore legal drafter revising a client document to
bring it in line with an amendment.

You get the amendment, the document, and the specific clause flagged as
outdated. Produce a minimal, surgical redline of that clause.

Rules:
- Change ONLY what the amendment requires. Preserve the document's existing
  drafting style, defined terms, numbering and voice. A lawyer must recognise
  it as their own clause, edited - not rewritten.
- "original" must be the flagged text copied VERBATIM from the document, long
  enough to locate unambiguously (a full sentence or sub-clause).
- "revised" is that same text with the necessary edits applied.
- "rationale" is one sentence: what changed and which provision compels it.
- "risk_if_unchanged" is one sentence: the concrete exposure of leaving it.
- If the fix requires a judgement call a lawyer must make (a commercial choice,
  a number not fixed by the amendment), say so in "needs_lawyer_input" and
  still propose your best draft.

Return ONLY JSON:
{"original": "...", "revised": "...", "rationale": "...",
 "risk_if_unchanged": "...", "needs_lawyer_input": "" }"""


def _load_store() -> dict:
    if os.path.exists(STORE):
        with open(STORE, encoding="utf-8") as f:
            return json.load(f)
    return {"proposals": {}, "audit": []}


def _save_store(store: dict) -> None:
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)


def word_diff(original: str, revised: str) -> list[dict]:
    """Word-level diff rendered as ordered spans: equal / removed / added.
    The frontend paints these red/green like a GitHub diff."""
    a, b = original.split(), revised.split()
    spans = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if op == "equal":
            spans.append({"type": "equal", "text": " ".join(a[i1:i2])})
        elif op == "delete":
            spans.append({"type": "removed", "text": " ".join(a[i1:i2])})
        elif op == "insert":
            spans.append({"type": "added", "text": " ".join(b[j1:j2])})
        elif op == "replace":
            spans.append({"type": "removed", "text": " ".join(a[i1:i2])})
            spans.append({"type": "added", "text": " ".join(b[j1:j2])})
    return spans


def propose(amendment: dict, client: dict, doc: dict, verdict: dict) -> dict:
    """Draft a redline for one flagged document. Cached by proposal id."""
    pid = f"{amendment['id']}:{doc['id']}"
    store = _load_store()
    if pid in store["proposals"]:
        return store["proposals"][pid]

    changes = "\n".join(
        f"- {c['aspect']}: was [{c['old']}] now [{c['new']}]"
        for c in amendment.get("key_changes", []))
    user = f"""AMENDMENT
{amendment['statute']} - {amendment['title']}
Citation: {amendment['citation']} | In force: {amendment['force_date']}
Key changes:
{changes}
New text: {amendment['after']}

CLIENT: {client['name']}
DOCUMENT: {doc['name']}
{doc['text']}

FLAGGED CLAUSE ({verdict.get('category')}): {verdict.get('clause_quote')}
WHY: {verdict.get('reason')}"""

    try:
        draft = chat_json(SYSTEM, user, max_tokens=2000)
    except LLMNotConfigured as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Redline failed: {e}"}

    proposal = {
        "id": pid,
        "amendment_id": amendment["id"],
        "amendment_title": amendment["title"],
        "citation": amendment["citation"],
        "force_date": amendment["force_date"],
        "client_id": client["id"],
        "client_name": client["name"],
        "doc_id": doc["id"],
        "doc_name": doc["name"],
        "category": verdict.get("category"),
        "original": draft.get("original", ""),
        "revised": draft.get("revised", ""),
        "rationale": draft.get("rationale", ""),
        "risk_if_unchanged": draft.get("risk_if_unchanged", ""),
        "needs_lawyer_input": draft.get("needs_lawyer_input", ""),
        "diff": word_diff(draft.get("original", ""), draft.get("revised", "")),
        "status": "pending",
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    store["proposals"][pid] = proposal
    _save_store(store)
    return proposal


def decide(pid: str, action: str, actor: str, note: str = "") -> dict:
    """Approve, reject or flag a proposal. Records an audit entry either way.

    Nothing is applied to a document without a human decision - this log is
    what a firm shows its insurer or the regulator.
    """
    if action not in ("approve", "reject", "flag"):
        return {"error": f"Unknown action: {action}"}
    store = _load_store()
    p = store["proposals"].get(pid)
    if not p:
        return {"error": "Proposal not found"}
    p["status"] = {"approve": "approved", "reject": "rejected",
                   "flag": "flagged for review"}[action]
    p["decided_by"] = actor
    p["decided_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    p["decision_note"] = note
    store["audit"].append({
        "at": p["decided_at"], "actor": actor, "action": p["status"],
        "proposal_id": pid, "client": p["client_name"], "document": p["doc_name"],
        "amendment": p["amendment_title"], "authority": p["citation"], "note": note,
    })
    _save_store(store)
    return p


def audit_log() -> list[dict]:
    return list(reversed(_load_store()["audit"]))


def all_proposals() -> list[dict]:
    return list(_load_store()["proposals"].values())
