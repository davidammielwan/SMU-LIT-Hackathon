"""Feature 2 — impact analysis.

Given a selected amendment and the client database, decide per document whether
it is truly affected (HIGH / MODERATE) or UNAFFECTED, and additionally check the
client *profile* for exposure no document captures.

Design rules (these are the pitch, keep them true):
- Topical adjacency is NOT impact. A PDPA consent form is unaffected by a PDPA
  breach-window change unless it states or assumes the changed position.
- Every flagged document must carry a verbatim clause quote as evidence.
- Every verdict carries a confidence marker: "found" (quote states the old
  position) vs "inferred" (exposure follows from profile or incorporation by
  reference), so the lawyer can see which claims to trust.
"""
import json
import os
import concurrent.futures

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm import chat_json

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def load_json(*parts):
    with open(os.path.join(DATA, *parts), encoding="utf-8") as f:
        return json.load(f)


SYSTEM = """You are a legal change-impact analyst for a Singapore law firm.
You receive ONE regulatory amendment and ONE client's file (profile + documents).
Decide which documents are TRULY affected by the amendment.

Categories:
- "high": the document states or assumes the OLD legal position that this
  amendment changes (e.g. restates a superseded time limit, threshold, or duty),
  or omits something the amendment now makes mandatory for this document's use.
- "moderate": the document is exposed INDIRECTLY and is not itself wrong -
  it incorporates an affected document by reference, sits near (but on the safe
  side of) a changed threshold, or warrants review without stating anything
  that the amendment contradicts.

  The high/moderate line is about whether THIS document's own words are now
  wrong. Ask: "if I read only this document, would I be misled?" Yes -> high.
  No, but it is downstream of something that is wrong -> moderate. Reserve
  "high" for documents whose own text states the superseded position or omits
  a duty that is mandatory for this document's purpose. Do not escalate to
  "high" merely because the client is important or the amendment is serious.
- "unaffected": everything else — INCLUDING documents on the same general topic
  that do not state or assume the changed position. Topical overlap alone is
  NEVER impact. A consent form is not affected by a breach-notification change.

Also assess the CLIENT PROFILE separately, under a STRICT test. The profile
verdict exists only to catch exposure that the DOCUMENTS MISS — a duty that
attaches to this client because of a specific, stated profile fact, where no
document on file addresses it.

Return "unaffected" for the profile UNLESS ALL of these hold:
1. A specific fact in the profile (a headcount crossing a statutory threshold,
   a licence held, a named business activity) triggers this amendment; AND
2. No document on file already carries that exposure (if a document is flagged
   for the same duty, the profile adds nothing - return unaffected); AND
3. The duty is concrete and actionable, not generic.

Generic applicability is NOT a profile hit. "Handles personal data", "has
employees", "is a company" are true of nearly every client and must return
"unaffected". If your reason could be copy-pasted to another client in a
different industry, it is not a profile hit.
Good example: a 40-employee client crossing a 25-employee threshold for a new
grievance duty, where no handbook on file mentions grievances.

Rules:
- For every high/moderate document verdict, quote the exact sentence fragment
  from the document text that carries the exposure ("clause_quote", verbatim).
- confidence is "found" when the quote itself states the old/missing position;
  "inferred" when the exposure follows indirectly (references, profile facts).
- "action": one imperative sentence a lawyer could act on, with the deadline if
  the amendment has a force date.
- Be conservative: when in doubt between moderate and unaffected, and the text
  carries no assumption the amendment changes, choose unaffected.

Return ONLY JSON:
{
  "document_verdicts": [
    {"doc_id": "...", "category": "high|moderate|unaffected",
     "clause_quote": "...", "reason": "...", "action": "...",
     "confidence": "found|inferred"}
  ],
  "profile_verdict": {"category": "high|moderate|unaffected",
     "reason": "...", "action": "...", "confidence": "inferred"}
}
Include EVERY document id in document_verdicts. For unaffected docs, clause_quote
and action may be empty strings and reason one short clause."""


def build_user_prompt(amendment: dict, client: dict) -> str:
    changes = "\n".join(
        f"- {c['aspect']}: was [{c['old']}] now [{c['new']}]"
        for c in amendment.get("key_changes", [])
    )
    docs = "\n\n".join(
        f"[doc_id={d['id']}] {d['name']}\n{d['text']}" for d in client["documents"]
    )
    return f"""AMENDMENT
Statute: {amendment['statute']}
Title: {amendment['title']}
Citation: {amendment['citation']}
Gazetted: {amendment['gazetted']} | In force: {amendment['force_date']}
Summary: {amendment['summary']}
Key changes:
{changes}
Old text: {amendment['before']}
New text: {amendment['after']}

CLIENT
Name: {client['name']} (practice: {client['practice']})
Profile: {json.dumps(client['profile'])}

DOCUMENTS
{docs}"""


def sweep_client(amendment: dict, client: dict) -> dict:
    """Analyse one client against one amendment."""
    result = chat_json(SYSTEM, build_user_prompt(amendment, client))
    # normalise + attach display fields
    verdicts = []
    doc_names = {d["id"]: d["name"] for d in client["documents"]}
    for v in result.get("document_verdicts", []):
        if v.get("doc_id") not in doc_names:
            continue
        v["doc_name"] = doc_names[v["doc_id"]]
        v["category"] = v.get("category", "unaffected").lower()
        verdicts.append(v)
    profile = result.get("profile_verdict") or {"category": "unaffected", "reason": ""}
    profile["category"] = profile.get("category", "unaffected").lower()
    return {
        "client_id": client["id"],
        "client_name": client["name"],
        "document_verdicts": verdicts,
        "profile_verdict": profile,
    }


def sweep(amendment_ids: list[str], client_ids: list[str] | None = None) -> dict:
    """Run the sweep for the selected amendments across the client base.

    One LLM call per (amendment, client) pair, in parallel.
    """
    amendments = {a["id"]: a for a in load_json("amendments", "amendments.json")}
    clients = load_json("clients", "clients.json")
    if client_ids:
        clients = [c for c in clients if c["id"] in client_ids]

    tasks = [
        (amendments[aid], c) for aid in amendment_ids if aid in amendments
        for c in clients
    ]
    results = []
    errors = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(sweep_client, a, c): (a, c) for a, c in tasks}
        for fut in concurrent.futures.as_completed(futures):
            a, c = futures[fut]
            try:
                r = fut.result()
                r["amendment_id"] = a["id"]
                r["amendment_title"] = a["title"]
                r["citation"] = a["citation"]
                r["force_date"] = a["force_date"]
                results.append(r)
            except Exception as e:  # keep the sweep alive if one pair fails
                errors.append({"amendment_id": a["id"], "client_id": c["id"],
                               "error": str(e)})

    # Aggregate into ranked client hits for the dashboard
    order = {"high": 0, "moderate": 1, "unaffected": 2}
    hits = []
    for r in results:
        flagged = [v for v in r["document_verdicts"] if v["category"] != "unaffected"]
        prof = r["profile_verdict"]
        if not flagged and prof["category"] == "unaffected":
            continue
        worst = min(
            [order[v["category"]] for v in flagged] + [order[prof["category"]]]
        )
        hits.append({
            "amendment_id": r["amendment_id"],
            "amendment_title": r["amendment_title"],
            "citation": r["citation"],
            "force_date": r["force_date"],
            "client_id": r["client_id"],
            "client_name": r["client_name"],
            "risk": "high" if worst == 0 else "moderate",
            "flagged_docs": flagged,
            "profile_verdict": prof if prof["category"] != "unaffected" else None,
        })
    hits.sort(key=lambda h: (0 if h["risk"] == "high" else 1, h["client_name"]))
    scanned = len({(r["amendment_id"], r["client_id"]) for r in results})
    docs_scanned = sum(len(r["document_verdicts"]) for r in results)
    return {"hits": hits, "raw": results, "errors": errors,
            "meta": {"pairs_scanned": scanned, "docs_scanned": docs_scanned}}
