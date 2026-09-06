"""Free-text Q&A over the amendments and the client base.

A sweep answers one question ("who is affected by this amendment?"). Anything
else the user types - explain this amendment, what should change in Meridian's
DPA, which clients are in scope - is a question, and should get an answer, not
a sweep. Grounded in the same corpus so it cannot invent clients or provisions.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from llm import chat, LLMNotConfigured

SYSTEM = """You are Amenda, assisting a Singapore law firm partner.

Answer from the CONTEXT provided - the firm's amendments and its client files.
Ground every claim: name the client, the document and the clause you rely on,
and cite the provision. If the context does not answer the question, say so
plainly and say what would. Never invent a client, document, provision or date.

Be brief and practical: a partner reading between meetings. Short paragraphs,
no headings, no bullet lists unless genuinely enumerating. Where a document is
outdated, say what it says now and what it should say.

Write plain text only: no markdown, no ** bold **, no # headings. Use ASCII
punctuation - a hyphen rather than a dash, straight quotes rather than curly.

If the question would be better served by a full sweep across all clients,
answer what you can and add a final line: "Select the amendment and run a sweep
for a complete client-by-client answer."""


def build_context(amendments: list, clients: list, max_docs: int = 40) -> str:
    ams = []
    for a in amendments:
        provs = "; ".join(
            f"{p['clause']}: {p['heading']} - {p['effect']}"
            for p in a.get("main_provisions", []))
        ams.append(
            f"[{a['id']}] {a['statute']} - {a['title']}\n"
            f"  Citation: {a['citation']} | In force: {a['force_date']}\n"
            f"  Summary: {a['summary']}\n"
            f"  Before: {a['before']}\n  After: {a['after']}\n"
            f"  Main provisions: {provs}")
    cls = []
    n = 0
    for c in clients:
        docs = []
        for d in c["documents"]:
            if n >= max_docs:
                break
            docs.append(f"    - [{d['id']}] {d['name']}: {d['text']}")
            n += 1
        cls.append(
            f"[{c['id']}] {c['name']} ({c['practice']}, {c['profile']['headcount']} staff)\n"
            f"  Business: {c['profile']['business']}\n"
            f"  Notes: {c['profile']['notes']}\n"
            f"  Documents:\n" + "\n".join(docs))
    return "AMENDMENTS\n" + "\n\n".join(ams) + "\n\nCLIENT FILES\n" + "\n\n".join(cls)


def ask(question: str, history: list[dict], amendments: list, clients: list) -> str:
    """Answer a free-text question. `history` is [{role, content}, ...]."""
    context = build_context(amendments, clients)
    convo = ""
    for m in history[-6:]:
        who = "PARTNER" if m.get("role") == "user" else "AMENDA"
        convo += f"\n{who}: {m.get('content', '')[:1200]}"
    user = f"CONTEXT\n{context}\n"
    if convo:
        user += f"\nEARLIER IN THIS CONVERSATION{convo}\n"
    user += f"\nPARTNER: {question}"
    return chat(SYSTEM, user, max_tokens=1200)


def classify(question: str) -> str:
    """Route: 'sweep' when the user wants a client-by-client exposure run,
    'qa' otherwise. Deliberately conservative - a question is a question."""
    q = question.lower().strip()
    sweep_phrases = (
        "run a sweep", "sweep the", "sweep our", "sweep client", "sweep all",
        "which clients are affected", "who is affected", "which clients are exposed",
        "find affected clients", "affected clients", "scan all clients",
    )
    return "sweep" if any(p in q for p in sweep_phrases) else "qa"
