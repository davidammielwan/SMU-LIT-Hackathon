# RegulaSense — Agentic AI for Regulatory Resilience in Law Firms

> **Tagline**: *Don't just track the law — stay structurally ahead of it.*

---

## 1. Executive Summary

RegulaSense is an agentic AI platform that continuously monitors Singapore's regulatory landscape, automatically detects changes in legislation, subsidiary instruments, guidance notes, circulars, court rulings, **and parliamentary debate proceedings**, and then **propagates** those changes across a firm's entire operational surface — client advisories, matter workflows, compliance documents, and templates — before the outdated version causes harm.

The system goes beyond horizon-scanning. It doesn't just *tell* you something changed; it **identifies which clients and their matters are now at risk**, **explains how they are affected**, **assigns a three-level severity classification**, and **recommends concrete remediation actions** — including which clients need to be proactively notified and what filings or documents require revision.

### 1.1 MVP Decision Summary

The following decisions have been finalised for the Minimum Viable Product:

| Decision | MVP Choice | Rationale |
|---|---|---|
| **LLM Provider** | OpenAI via OpenRouter | Cost-effective access to GPT-4o with fallback model flexibility |
| **Deployment** | On-premise (Docker Compose) | Simplified setup for demo/hackathon; cloud-ready architecture for future migration |
| **Primary Focus** | Client-centric impact warnings | Warn clients in specific categories when relevant law changes (e.g., tech law amendments → tech business clients) |
| **Jurisdiction** | Singapore only | Focused regulatory corpus; architecture supports multi-jurisdiction expansion later |
| **Authentication** | Simple custom auth (JWT) | No SSO/identity provider integration needed for MVP |
| **Integrations** | None — standalone web dashboard | No DMS, PMS, or communication platform integrations |
| **Data Sources** | SSO, MAS, PDPC, ACRA, Parliament, PairSearch + general PDF scraping | Broad coverage with parliamentary debate monitoring for early warning |
| **Token Optimisation** | Aggressive context management without information loss | Smart chunking, caching, and prompt compression |

---

## 2. Problem Analysis

### 2.1 The Regulatory Velocity Problem

Singapore's regulatory environment is one of the most dynamic in Asia-Pacific:

| Dimension | Scale |
|---|---|
| Subsidiary legislation instruments gazetted annually | 1,000+ |
| MAS notices, circulars, and guidelines per year | 200+ |
| ACRA, PDPC, and other agency guidance updates | 100+ |
| Parliamentary Bills introduced and debated per session | 50+ |
| Court decisions reinterpreting statutory provisions | Continuous |
| Cross-jurisdictional conflicting standards (ASEAN, international) | Growing |

### 2.2 The Real Risk: Silent Drift

The danger is not that firms are unaware of changes — most subscribe to alert services. The danger is **silent drift**: the growing, invisible gap between what the current rules require and what the firm's accumulated tools, templates, checklists, and working practices still assume.

**Silent drift manifests as:**

- A template clause that references a repealed provision
- A compliance checklist built on superseded guidance
- A workflow that skips a newly required step
- An advisory letter that cites outdated thresholds
- A training module that teaches a procedure the regulator has since amended
- A client engagement that proceeds under assumptions a recent court decision has invalidated
- **A lawyer unaware that a parliamentary debate signals an imminent amendment that will affect ongoing client matters**

### 2.3 Why Existing Solutions Fall Short

| Existing Approach | Limitation |
|---|---|
| Horizon-scanning / alert services | Tell you *what* changed, not *what of yours is now wrong* |
| Manual review cycles | Too slow, too expensive, too error-prone at scale |
| Static compliance tools | Encode rules at a point in time; become liabilities when rules shift |
| General-purpose LLMs | No firm-specific context; cannot map changes to your documents |
| Document management systems | Store documents but don't understand their regulatory dependencies |
| Parliamentary monitoring services | Report debate activity but don't map implications to specific client portfolios |

---

## 3. Solution Architecture Overview

### 3.1 High-Level Architecture

```mermaid
graph TB
    subgraph "Data Ingestion Layer"
        A["Web Scrapers<br/>(SSO, AGC, MAS, ACRA, PDPC)"]
        B["API Connectors<br/>(LawNet, SSO, Government APIs)"]
        C["RSS / Gazette Feeds"]
        D["Court Decision Monitors"]
        E2["Parliamentary Debate Scraper<br/>(Hansard / Parliament.gov.sg)"]
        F2["PairSearch Scraper"]
        G2["PDF Document Scraper<br/>(Multi-source)"]
    end

    subgraph "Processing & Intelligence Layer"
        E["Change Detection Engine"]
        F["NLP & Legal Semantics Pipeline"]
        G["Impact Analysis Agent"]
        H["Severity Classification Engine"]
        I["Timeline & Enforcement Tracker"]
        I2["Early Warning Engine<br/>(Parliamentary Signals)"]
    end

    subgraph "Knowledge Graph & Storage"
        J["Regulatory Knowledge Graph<br/>(Neo4j)"]
        K["Firm Document Store<br/>(Vector DB + PostgreSQL)"]
        L["Change History Ledger<br/>(Immutable Audit Log)"]
        M["Client-Regulation Mapping Index"]
    end

    subgraph "Application Layer"
        N["Dashboard & Alert Centre"]
        O["Impact Report Generator"]
        P["Regulatory Diff Viewer"]
        Q["Conversational AI Chatbot"]
        R["Client Advisory Engine"]
    end

    subgraph "Standalone Web Dashboard"
        S["In-App Notifications"]
        V["Export & Reporting<br/>(PDF, DOCX, Excel)"]
    end

    A --> E
    B --> E
    C --> E
    D --> E
    E2 --> I2
    F2 --> E
    G2 --> E
    E --> F
    I2 --> F
    F --> G
    F --> H
    F --> I
    G --> J
    G --> K
    H --> J
    I --> J
    J --> N
    J --> O
    J --> P
    J --> Q
    K --> Q
    M --> Q
    M --> R
    N --> S
    O --> V
```

### 3.2 Core Design Principles

| Principle | Implementation |
|---|---|
| **Client-centric impact mapping** | Every regulatory change is evaluated against the firm's client portfolio by industry/sector, not just by document |
| **Regulatory-first ontology** | Every entity in the system is modelled around its regulatory dependency chain |
| **Change propagation by default** | When a regulation changes, the system *automatically* traverses all downstream dependencies to affected clients |
| **Early warning via parliamentary monitoring** | Parliamentary debates and readings are scraped to warn about *potential* upcoming amendments before they are enacted |
| **Severity-driven prioritisation** | Not all changes are equal; the system triages by liability exposure and enforcement timeline |
| **Explainability** | Every recommendation includes a clear chain of reasoning from source change → affected client/asset → recommended action |
| **Auditability** | Every detection, classification, and recommendation is logged immutably for compliance and professional indemnity |
| **Human-in-the-loop** | The system recommends; humans approve and execute. No automated changes to client-facing materials without lawyer sign-off |
| **Token-efficient AI** | Aggressive prompt optimisation, response caching, and smart context windowing to minimise API costs without removing necessary information |

---

## 4. Module 1 — Regulatory Data Ingestion & Sync Engine

### 4.1 Purpose

Continuously scrape, ingest, normalise, and sync Singapore's regulatory corpus — including **parliamentary proceedings**, **PairSearch results**, and **PDF documents from any government website** — so the system always holds a current, structured, and semantically indexed mirror of the law.

### 4.2 Data Sources

| Source | Type | URL / Access Method | Update Frequency | Priority |
|---|---|---|---|---|
| Singapore Statutes Online (SSO) | Primary & subsidiary legislation | `https://sso.agc.gov.sg` | Real-time on gazette | 🔴 P0 |
| Attorney-General's Chambers (AGC) | Gazette notifications | `https://www.agc.gov.sg` | As published | 🔴 P0 |
| Singapore Parliament | Hansard, Order Papers, Bills | `https://www.parliament.gov.sg` | Per sitting | 🔴 P0 |
| Monetary Authority of Singapore (MAS) | Notices, circulars, guidelines | `https://www.mas.gov.sg` | Weekly+ | 🔴 P0 |
| PDPC | Data protection guidance | `https://www.pdpc.gov.sg` | As issued | 🟡 P1 |
| ACRA | Company law updates | `https://www.acra.gov.sg` | Monthly+ | 🟡 P1 |
| PairSearch | Legal research / case law | `https://pairsearch.com` (or relevant endpoint) | As indexed | 🟡 P1 |
| Ministry of Law (MinLaw) | Policy papers, consultations | `https://www.mlaw.gov.sg` | As published | 🟡 P1 |
| Government Gazette | Subsidiary legislation | `https://www.egazette.gov.sg` | As gazetted | 🔴 P0 |
| Supreme Court / State Courts | Practice directions, judgments | `https://www.judiciary.gov.sg` | Continuous | 🟢 P2 |

### 4.3 Scraping Architecture

```mermaid
flowchart LR
    subgraph "Scraper Orchestrator (Celery + Redis)"
        direction TB
        S1["Scheduler<br/>(Cron-based per source)"]
        S2["Rate Limiter<br/>(Respectful crawling)"]
        S3["Retry & Error Handler"]
    end

    subgraph "Source-Specific Scrapers"
        direction TB
        SC1["SSO Scraper<br/>(Playwright headless)"]
        SC2["MAS Scraper<br/>(API + HTML fallback)"]
        SC3["Gazette RSS Parser"]
        SC4["Court Judgment Scraper"]
        SC5["PDPC/ACRA Scraper"]
        SC6["Parliament Hansard Scraper"]
        SC7["PairSearch Scraper"]
        SC8["Generic PDF Scraper<br/>(Multi-site)"]
    end

    subgraph "Post-Processing Pipeline"
        direction TB
        P1["HTML → Structured Text"]
        P1B["PDF → Structured Text<br/>(PyMuPDF + pdfplumber)"]
        P2["Section / Clause Parser"]
        P3["Metadata Extractor<br/>(Date, Act No., Amendment No.)"]
        P4["Deduplication Engine"]
        P5["Change Diff Calculator"]
    end

    S1 --> SC1
    S1 --> SC2
    S1 --> SC3
    S1 --> SC4
    S1 --> SC5
    S1 --> SC6
    S1 --> SC7
    S1 --> SC8
    SC1 --> P1
    SC2 --> P1
    SC3 --> P1
    SC4 --> P1
    SC5 --> P1
    SC6 --> P1
    SC7 --> P1
    SC8 --> P1B
    P1 --> P2
    P1B --> P2
    P2 --> P3
    P3 --> P4
    P4 --> P5
```

### 4.4 Scraper Implementation Details

#### 4.4.1 Singapore Statutes Online (SSO) Scraper

```
Target:         https://sso.agc.gov.sg
Technology:     Playwright (headless Chromium) — SSO uses dynamic JS rendering
Schedule:       Every 6 hours
Strategy:
  1. Navigate to the "What's New" / "Recent Amendments" page
  2. Extract list of recently amended Acts and subsidiary legislation
  3. For each amended instrument:
     a. Fetch the current consolidated text
     b. Compare against the previously stored version (section-by-section)
     c. Generate a structured diff (additions, deletions, modifications)
     d. Extract metadata: Act number, section numbers affected, 
        commencement date, gazette reference
  4. Store the new version and the diff in the database
  5. Trigger the Change Detection Engine
Rate Limiting:  Max 1 request/second, respect robots.txt
Error Handling: Exponential backoff with max 5 retries; alert on persistent failure
```

#### 4.4.2 MAS Regulatory Scraper

```
Target:         https://www.mas.gov.sg/regulation
Technology:     httpx + BeautifulSoup (mostly static HTML) / API where available
Schedule:       Every 4 hours
Strategy:
  1. Monitor the "Regulations and Guidance" listing pages
  2. Detect new or updated:
     - MAS Notices (e.g., MAS Notice 637, SFA notices)
     - Circulars
     - Guidelines
     - Consultation papers and response papers
     - FAQs
  3. For each detected change:
     a. Download the full document (PDF or HTML)
     b. Extract text content (PyMuPDF for PDFs)
     c. Parse into structured sections
     d. Compare against previous version
     e. Tag with regulatory domain (banking, insurance, securities, payments)
  4. Store and trigger downstream processing
```

#### 4.4.3 Gazette Monitor

```
Target:         https://www.egazette.gov.sg
Technology:     RSS feed parser + httpx fallback
Schedule:       Every 2 hours (gazette publications are time-critical)
Strategy:
  1. Parse the gazette RSS feed for new entries
  2. For each new gazette notification:
     a. Classify type: Act commencement, subsidiary legislation, 
        amendment order, revocation, etc.
     b. Extract key metadata:
        - Instrument title and number
        - Parent Act (if subsidiary legislation)
        - Commencement / effective date
        - Transitional provisions (if any)
     c. Link to the full text on SSO
     d. Trigger priority processing if commencement date is < 30 days away
```

#### 4.4.4 Parliamentary Debate & Hansard Scraper (NEW)

```
Target:         https://www.parliament.gov.sg
Technology:     Playwright (headless) + httpx + PDF parser
Schedule:       Daily (Parliament sits on specific days; check for new 
                Hansard publications and Order Papers)
Strategy:
  1. Monitor the Parliament website for:
     a. New Bills introduced (First Reading, Second Reading, Third Reading)
     b. Hansard transcripts (Official Reports of Parliamentary Debates)
     c. Order Papers (upcoming parliamentary business)
     d. Select Committee reports
     e. Ministerial Statements related to regulatory policy
  2. For each new Bill detected:
     a. Download the Bill text (usually PDF)
     b. Extract structured content: long title, clauses, schedules
     c. Identify which existing Acts the Bill proposes to amend
     d. Parse the specific amendments proposed (additions, deletions, 
        substitutions to existing provisions)
     e. Flag as "POTENTIAL AMENDMENT — NOT YET ENACTED"
     f. Track the Bill's progress through readings
  3. For each Hansard transcript:
     a. Download and extract text
     b. Use NLP to identify:
        - References to specific Acts or regulations
        - Ministerial statements signalling upcoming regulatory changes
        - Discussions of policy shifts that may lead to amendments
        - Committee recommendations for legislative reform
     c. Generate "Early Warning Signals" for potential amendments
     d. Link signals to affected regulatory domains
  4. Classification of parliamentary signals:
     - 🔴 Bill at Third Reading → Amendment is imminent
     - 🟡 Bill at Second Reading → Amendment is likely, details known
     - 🟡 Bill at First Reading → Amendment is proposed, high-level known
     - 🟢 Ministerial Statement → Potential future amendment signalled
     - 🟢 Select Committee Report → Recommendations may lead to amendments
Output:
  - "Early Warning" entries in the dashboard with status tracking
  - Linked to affected Acts, regulatory domains, and ultimately to clients
  - Separate visual treatment from enacted amendments (dotted border, 
    "PENDING" badge, estimated timeline)
```

#### 4.4.5 PairSearch Scraper

```
Target:         https://pairsearch.com (or relevant API endpoint)
Technology:     httpx + Playwright (depending on site architecture)
Schedule:       Every 12 hours
Strategy:
  1. Monitor PairSearch for new legal research results, case analyses, 
     and regulatory commentary
  2. For each new entry:
     a. Extract title, summary, full text, and linked regulatory references
     b. Identify which Acts, sections, or guidance notes are discussed
     c. Classify whether the content represents:
        - A new court interpretation of existing law
        - Commentary on a recent amendment
        - Analysis of regulatory trends
     d. Generate embeddings and store for chatbot retrieval
  3. Cross-reference with existing knowledge graph entries
  4. Flag any court decisions that reinterpret provisions currently 
     referenced by firm documents or client matters
```

#### 4.4.6 Generic PDF Document Scraper

```
Target:         Any government agency website publishing PDFs
Technology:     httpx (download) + PyMuPDF + pdfplumber (extraction)
Schedule:       Triggered per-source or on-demand
Strategy:
  1. Accept a URL pointing to a PDF or a webpage containing PDF links
  2. Download the PDF document
  3. Extract text using a multi-strategy approach:
     a. PyMuPDF for text-based PDFs (fast, preserves structure)
     b. pdfplumber for table-heavy PDFs (extracts tabular data)
     c. OCR fallback (Tesseract) for scanned/image-based PDFs
  4. Post-processing:
     a. Clean and normalise extracted text
     b. Identify document structure (headings, sections, paragraphs)
     c. Extract metadata from document properties and content
     d. Parse regulatory references (Act names, section numbers, 
        gazette references)
  5. Generate embeddings for semantic search
  6. Store in the document corpus with source URL and download timestamp
Supported PDF Types:
  - Regulatory guidance documents
  - Consultation papers
  - Response to consultation papers
  - Circulars and notices (when published as PDF)
  - Practice directions
  - Annual reports with regulatory updates
```

### 4.5 Data Normalisation Schema

Every ingested regulatory instrument is normalised into the following structure:

```json
{
  "instrument_id": "SL-2026-0342",
  "type": "subsidiary_legislation",
  "parent_act": {
    "id": "ACT-2020-0012",
    "title": "Personal Data Protection Act 2012",
    "chapter": "26"
  },
  "title": "Personal Data Protection (Amendment) Regulations 2026",
  "gazette_reference": "S 342/2026",
  "gazette_date": "2026-08-28",
  "commencement_date": "2026-10-01",
  "commencement_type": "fixed_date",
  "status": "enacted_not_yet_in_force",
  "regulatory_domain": ["data_protection", "technology"],
  "industry_sectors_affected": ["technology", "healthcare", "financial_services"],
  "issuing_authority": "PDPC",
  "sections_affected": [
    {
      "section": "26A",
      "action": "inserted",
      "summary": "New mandatory breach notification timeline reduced from 3 to 2 business days"
    },
    {
      "section": "48(1)",
      "action": "amended",
      "summary": "Maximum financial penalty increased from $1M to $10M or 10% of annual turnover"
    }
  ],
  "full_text_url": "https://sso.agc.gov.sg/SL/PDPA2012-S342-2026",
  "full_text_hash": "sha256:a3f2b8c1...",
  "previous_version_hash": "sha256:d7e9f4a2...",
  "diff_id": "DIFF-2026-08-28-0342",
  "source": "sso",
  "source_format": "html",
  "ingestion_timestamp": "2026-08-28T14:23:01Z",
  "processing_status": "pending_analysis"
}
```

Parliamentary early warning entries use an extended schema:

```json
{
  "signal_id": "PARL-2026-B042",
  "type": "parliamentary_early_warning",
  "signal_type": "bill_second_reading",
  "bill_title": "Companies (Amendment) Bill 2026",
  "bill_number": "Bill No. 42/2026",
  "target_act": {
    "id": "ACT-1967-0050",
    "title": "Companies Act 1967"
  },
  "parliament_sitting_date": "2026-09-03",
  "reading_stage": "second_reading",
  "proposed_changes_summary": "Introduces enhanced director liability provisions and mandatory climate risk disclosure for large companies",
  "estimated_commencement": "Q1 2027 (estimated based on typical legislative timeline)",
  "confidence_level": "high",
  "hansard_url": "https://www.parliament.gov.sg/...",
  "industry_sectors_affected": ["corporate_governance", "environmental", "financial_services"],
  "status": "monitoring",
  "ingestion_timestamp": "2026-09-04T08:00:00Z"
}
```

### 4.6 Version Control for Legislation

The system maintains a **git-like version history** for every legislative instrument:

```
legislation/
├── acts/
│   ├── personal-data-protection-act-2012/
│   │   ├── v1.0.0/  (Original enacted text)
│   │   ├── v1.1.0/  (2014 amendment)
│   │   ├── v1.2.0/  (2020 amendment)
│   │   ├── v1.3.0/  (2026 amendment — current)
│   │   └── metadata.json
│   └── companies-act-1967/
│       ├── ...
│       └── metadata.json
├── subsidiary_legislation/
│   └── ...
├── guidance/
│   ├── mas-notices/
│   ├── pdpc-guidelines/
│   └── ...
├── court_decisions/
│   └── ...
└── parliamentary/
    ├── bills/
    │   └── companies-amendment-bill-2026/
    │       ├── first_reading/
    │       ├── second_reading/
    │       └── metadata.json
    ├── hansard/
    │   └── 2026-09-03/
    └── early_warnings/
        └── ...
```

Each version stores:
- The full text (structured by sections/clauses)
- A diff against the previous version
- Metadata (gazette reference, dates, affected sections)
- Semantic embeddings for each section (for similarity search)

---

## 5. Module 2 — Change Detection & Impact Analysis Engine

### 5.1 Purpose

When a regulatory change is detected, automatically identify **which of the firm's clients — categorised by industry and sector — are affected**, along with their specific matters, documents, and workflows, and **in what way**.

### 5.2 Client-Centric Impact Model

> **Key Design Decision**: The MVP prioritises **client-centric impact mapping** over document-centric. The system's primary output is: *"This amendment affects these clients in this sector because..."* rather than just *"These documents reference this section."*

#### 5.2.1 Industry-Sector Taxonomy

Clients are tagged with one or more industry sectors. Regulatory changes are mapped to affected sectors. The intersection drives impact alerts.

| Sector Code | Sector Name | Key Regulatory Bodies | Example Regulations |
|---|---|---|---|
| `TECH` | Technology & Digital | PDPC, IMDA, CSA | PDPA, Cybersecurity Act, Online Safety Act |
| `FINSERV` | Financial Services | MAS | SFA, Banking Act, PS Act, MAS Notices |
| `HEALTH` | Healthcare & Life Sciences | MOH, HSA | Healthcare Services Act, Medicines Act |
| `CORPGOV` | Corporate Governance | ACRA, SGX | Companies Act, Securities Act |
| `PROPCON` | Property & Construction | URA, BCA | Planning Act, Building Control Act |
| `EMPLOY` | Employment & Labour | MOM | Employment Act, WICA, EFMA |
| `ENVIRON` | Environment & Sustainability | NEA, MSE | Environmental Protection Act |
| `IP` | Intellectual Property | IPOS | Patents Act, Copyright Act, Trade Marks Act |
| `DISPUTE` | Dispute Resolution | Courts, SIAC, SIMC | SCJA, Arbitration Act |
| `GENERAL` | General / Cross-Sector | AGC, MinLaw | Interpretation Act, Evidence Act |

#### 5.2.2 Client-Sector-Regulation Mapping Flow

```mermaid
flowchart TD
    A["Regulatory Change Detected<br/>(e.g., PDPA Amendment)"] --> B["Identify Regulatory Domain<br/>(data_protection)"]
    B --> C["Map to Affected Sectors<br/>(TECH, FINSERV, HEALTH)"]
    C --> D["Query: All Clients in<br/>Affected Sectors"]
    D --> E{"For each affected client..."}
    E --> F["Check active matters"]
    E --> G["Check client-specific documents"]
    E --> H["Assess timeline overlap<br/>(matter completion vs.<br/>commencement date)"]
    F --> I["Generate Client Impact Report"]
    G --> I
    H --> I
    I --> J["Classify Severity"]
    J --> K["Generate Alert + Recommended Actions"]
```

### 5.3 The Regulatory Knowledge Graph

The core intelligence of RegulaSense is a **knowledge graph** that maps the relationships between regulatory instruments, industry sectors, and the firm's clients.

```mermaid
graph LR
    subgraph "Regulatory Layer"
        R1["Act: PDPA 2012"]
        R2["Section 26A<br/>(Breach Notification)"]
        R3["PDPC Guideline:<br/>Breach Notification"]
        R4["MAS Notice 655:<br/>Cyber Hygiene"]
    end

    subgraph "Sector Layer"
        S1["Sector: TECH"]
        S2["Sector: FINSERV"]
        S3["Sector: HEALTH"]
    end

    subgraph "Client Layer"
        C1["Client A:<br/>FinTech Startup<br/>(TECH, FINSERV)"]
        C2["Client B:<br/>Healthcare Provider<br/>(HEALTH, TECH)"]
        C3["Client C:<br/>MNC Data Centre<br/>(TECH)"]
    end

    subgraph "Matter Layer"
        M1["Matter: DPA Review<br/>(Client A)"]
        M2["Matter: PDPC Investigation<br/>(Client B)"]
        M3["Matter: Compliance Retainer<br/>(Client C)"]
    end

    R1 --> R2
    R1 --> R3
    R1 --> S1
    R1 --> S3
    R4 --> S2
    S1 --> C1
    S1 --> C2
    S1 --> C3
    S2 --> C1
    S3 --> C2
    C1 --> M1
    C2 --> M2
    C3 --> M3
```

#### 5.3.1 Knowledge Graph Schema (Neo4j)

**Node Types:**

| Node Label | Properties | Description |
|---|---|---|
| `Act` | id, title, chapter, jurisdiction, status, current_version | A primary statute |
| `Section` | id, act_id, number, title, text, text_embedding, version | A section/clause within an Act |
| `SubsidiaryLegislation` | id, title, parent_act_id, gazette_ref, status | Regulations, orders, rules under an Act |
| `Guidance` | id, title, issuing_authority, type, status | Notices, circulars, guidelines |
| `CourtDecision` | id, case_name, citation, court, date, headnotes_embedding | A judicial decision |
| `ParliamentarySignal` | id, bill_title, reading_stage, sitting_date, confidence, target_act_id | An early warning from parliamentary proceedings |
| `Amendment` | id, instrument_id, gazette_date, commencement_date, severity | A specific change event |
| `Sector` | id, code, name, key_regulatory_bodies | An industry sector classification |
| `FirmDocument` | id, title, type, path, content_embedding, last_reviewed, client_id | A document owned by the firm (may be client-specific) |
| `Checklist` | id, title, domain, items_json, last_reviewed | A compliance checklist |
| `Workflow` | id, title, steps_json, regulatory_basis, last_reviewed | A process or SOP |
| `Template` | id, title, clause_embeddings, regulatory_references | A template document |
| `Client` | id, name, industry_sectors, active_matters, risk_profile | A client of the firm |
| `Matter` | id, client_id, description, practice_area, status, expected_completion | A legal matter / engagement |
| `TrainingModule` | id, title, content_embedding, last_updated | Internal training material |

**Relationship Types:**

| Relationship | From → To | Properties |
|---|---|---|
| `AMENDS` | Amendment → Section | sections_affected, action_type |
| `SUPERSEDES` | Guidance → Guidance | effective_date |
| `INTERPRETS` | CourtDecision → Section | ratio, obiter, binding |
| `REGULATES` | Act → Sector | primary_or_secondary |
| `SIGNALS_AMENDMENT` | ParliamentarySignal → Act | confidence_level, estimated_timeline |
| `BELONGS_TO_SECTOR` | Client → Sector | — |
| `REFERENCES` | FirmDocument → Section | clause_id, reference_type |
| `BASED_ON` | Checklist → Guidance | items_mapped |
| `IMPLEMENTS` | Workflow → Section | step_mapping |
| `USES_TEMPLATE` | Matter → Template | — |
| `HAS_MATTER` | Client → Matter | — |
| `SUBJECT_TO` | Client → Act | via sector mapping |
| `AFFECTS_SECTOR` | Amendment → Sector | impact_type |
| `AFFECTS_CLIENT` | Amendment → Client | severity, action_type, deadline |
| `REQUIRES_ACTION` | Amendment → Client | action_type, deadline |

### 5.4 Impact Analysis Pipeline

When a new amendment is detected, the following pipeline executes:

```mermaid
flowchart TD
    A["New Amendment Detected"] --> B["Parse & Structure the Change"]
    B --> C["Identify Affected Sections<br/>& Regulatory Domains"]
    C --> D["Map to Affected Industry Sectors"]
    D --> E{"For each affected sector..."}
    E --> F["Query Knowledge Graph:<br/>Find all clients in this sector"]
    F --> G{"For each affected client..."}
    G --> H["Check active matters:<br/>Is the client's matter timeline<br/>overlapping with commencement?"]
    G --> I["Check client-specific documents:<br/>Do any reference the<br/>amended provisions?"]
    G --> J["Assess client risk profile:<br/>How exposed is this client?"]
    H --> K["Generate Client Impact Report"]
    I --> K
    J --> K
    K --> L["Assign Severity Level"]
    L --> M["Generate Alerts &<br/>Recommended Actions"]
    
    C --> N["Semantic Search:<br/>Find firm assets with<br/>similar content embeddings<br/>(catch unlinked references)"]
    N --> K
```

### 5.5 Impact Type Taxonomy

| Impact Type | Description | Example |
|---|---|---|
| **Client Sector Impact** | The amendment affects a regulatory domain that applies to the client's industry sector | PDPA amendment affects all clients tagged with `TECH` sector |
| **Active Matter Timeline Risk** | The client has a matter whose expected timeline extends past the amendment's commencement date | Client B's enforcement action concludes in March 2027; new penalty regime commences January 2027 |
| **Direct Statutory Reference** | A client-specific document explicitly cites a provision that has been amended | A DPA drafted for Client A quoting s.26A PDPA — the section has been rewritten |
| **Procedural Deviation** | A client process or workflow no longer matches the amended requirement | A breach notification workflow based on 72-hour timeline, but amendment changes it to 48 hours |
| **Threshold / Value Obsolescence** | A client document contains numerical thresholds that have been superseded | A compliance guide for Client C stating the max penalty is $1M, but it is now $10M |
| **Definitional Shift** | A term whose legal definition has been expanded, narrowed, or replaced, affecting the client's obligations | "Personal data" definition expanded to include pseudonymised data — Client A processes such data |
| **Regulatory Basis Revoked** | The guidance on which a client-specific document is based has been revoked or superseded | A checklist for Client B based on a MAS circular that has been replaced |
| **Early Warning (Parliamentary)** | A parliamentary debate or Bill reading signals a potential future amendment affecting the client's sector | Second Reading of Companies Amendment Bill signals enhanced director duties for Client A's board |

---

## 6. Module 3 — Severity Classification System

### 6.1 Three-Level Severity Model

Every detected impact is classified into one of three severity levels:

### 🔴 SEVERITY 1 — CRITICAL (Immediate Liability Risk)

> **Definition**: The regulatory change creates an immediate or near-term risk of non-compliance, professional liability, regulatory penalty, or client harm if the affected asset is not updated before the commencement date.

**Criteria (any one triggers CRITICAL):**

- The amendment is **already in force** or commences within **30 days**
- The affected client has an **active matter** whose timeline overlaps with commencement
- The change involves **mandatory obligations** (e.g., notification deadlines, filing requirements)
- Non-compliance carries **criminal sanctions** or **significant financial penalties**
- The affected asset could cause the firm to **give incorrect legal advice** to the client if not updated
- The change affects **client-facing documents** that have already been issued or are pending issuance

**Required Response:**

- Immediate notification to practice group heads and relevant fee earners
- Affected assets flagged as **"DO NOT USE — UNDER REVIEW"** in the system
- Remediation deadline: **Within 5 business days** or before commencement date (whichever is sooner)
- Mandatory acknowledgement from responsible lawyer
- Client notification drafted and queued for review

---

### 🟡 SEVERITY 2 — MODERATE (Scheduled Remediation Required)

> **Definition**: The regulatory change will affect the firm's clients or assets, but there is sufficient time and the risk is manageable if remediation is scheduled and tracked.

**Criteria:**

- The amendment commences in **31–90 days**
- The affected client's matters **do not** have overlapping timelines
- The change involves **procedural updates** rather than substantive legal risk
- The affected asset is **internal-facing** (training materials, internal SOPs)
- Non-compliance would result in **administrative issues** rather than liability

**Required Response:**

- Notification to relevant practice group within **1 week**
- Remediation scheduled and tracked in the task management system
- Remediation deadline: **Within 30 days** or 2 weeks before commencement (whichever is sooner)
- Periodic status check until remediation is confirmed

---

### 🟢 SEVERITY 3 — LOW (Awareness & Planning)

> **Definition**: The regulatory change is relevant but does not pose immediate risk. Includes parliamentary early warnings, consultation papers, and changes with distant commencement dates.

**Criteria:**

- The amendment commences **> 90 days** from now, or is a **consultation paper** (not yet enacted)
- **Parliamentary signal** (Bill at First Reading, Ministerial Statement) — potential amendment, not yet enacted
- The affected client's sector is tangentially related
- The change is **minor** (e.g., typographical corrections, renumbering)

**Required Response:**

- Included in the **weekly regulatory digest**
- Added to the **next scheduled review cycle** for affected assets
- No immediate action required, but tracked for future follow-up
- Parliamentary signals monitored for escalation (if Bill progresses to later readings)

### 6.2 Severity Scoring Algorithm

```
severity_score = weighted_sum(
    time_urgency_score       × 0.30,   # How soon does the change take effect?
    liability_exposure_score × 0.25,   # What are the penalties for non-compliance?
    client_impact_breadth    × 0.20,   # How many clients (by sector) are affected?
    matter_timeline_overlap  × 0.15,   # Do any active matters overlap with commencement?
    remediation_complexity   × 0.10    # How hard is it to fix?
)

if severity_score >= 0.70:  → CRITICAL (Severity 1)
if severity_score >= 0.40:  → MODERATE (Severity 2)
if severity_score <  0.40:  → LOW      (Severity 3)
```

**Sub-score Definitions:**

| Sub-score | 0.0 (Low) | 0.5 (Medium) | 1.0 (High) |
|---|---|---|---|
| Time Urgency | > 90 days, consultation, or parliamentary signal | 31–90 days | ≤ 30 days or already in force |
| Liability Exposure | Administrative / minor | Financial penalties | Criminal sanctions / professional liability |
| Client Impact Breadth | 0 clients / tangential sector | 1–5 clients in affected sector | 6+ clients or flagship clients |
| Matter Timeline Overlap | No active matters overlap | Some matters have distant overlap | Active matters with imminent overlap |
| Remediation Complexity | Simple text update | Procedural redesign | Requires legal analysis + client comms |

### 6.3 Timeline Tracking

Each amendment record includes a structured timeline:

```json
{
  "amendment_id": "AMD-2026-0342",
  "timeline": {
    "gazette_date": "2026-08-28",
    "commencement_date": "2026-10-01",
    "commencement_type": "fixed_date",
    "days_until_commencement": 33,
    "transitional_provisions": {
      "exists": true,
      "summary": "Existing breach investigations commenced before 1 Oct 2026 may follow the previous 72-hour timeline",
      "transitional_end_date": "2027-01-01"
    },
    "firm_remediation_deadline": "2026-09-17",
    "status": "pending_remediation",
    "clients_with_overlapping_matters": [
      {
        "client_id": "CLT-001",
        "client_name": "HealthFirst Holdings",
        "matter_id": "MAT-2025-089",
        "matter_description": "PDPC Investigation",
        "expected_completion": "2027-03-15",
        "overlap_severity": "high"
      }
    ]
  }
}
```

For parliamentary early warnings, the timeline includes estimated dates:

```json
{
  "signal_id": "PARL-2026-B042",
  "timeline": {
    "first_reading_date": "2026-07-15",
    "second_reading_date": "2026-09-03",
    "third_reading_date": null,
    "estimated_enactment": "2026-11-01",
    "estimated_commencement": "2027-Q1",
    "confidence": "moderate",
    "status": "monitoring_second_reading"
  }
}
```

The dashboard displays a **countdown timer** for each pending amendment, colour-coded by urgency. Parliamentary signals show an **estimated timeline bar** with a confidence indicator.

---

## 7. Module 4 — Conversational AI Chatbot

### 7.1 Purpose

A context-aware legal AI chatbot that allows lawyers to ask natural-language questions about:

1. **How a regulatory change affects specific clients** (by sector and by individual client)
2. **Which clients need to be proactively informed** (e.g., if a client's case is long and amendments will be in force by then)
3. **What documents should be revised for each client**
4. **What kind of actions the lawyer should take** in accordance with the change for the clients in effect
5. **Parliamentary early warnings** and their implications for current client matters

### 7.2 Architecture

```mermaid
flowchart TB
    subgraph "User Interface"
        U["Lawyer's Chat Interface"]
    end

    subgraph "Chatbot Engine"
        A["Query Understanding<br/>(Intent + Entity Extraction)"]
        B["Context Assembly Agent"]
        C["Knowledge Graph Query Agent"]
        D["Document Retrieval Agent<br/>(RAG)"]
        E["Reasoning & Synthesis Agent"]
        F["Response Generation<br/>(with Citations)"]
    end

    subgraph "Knowledge Sources"
        G["Regulatory Knowledge Graph"]
        H["Firm Document Vector Store"]
        I["Client-Matter Database"]
        J["Amendment Impact Reports"]
        K["Change History Ledger"]
        L["Parliamentary Signals DB"]
    end

    U --> A
    A --> B
    B --> C
    B --> D
    C --> G
    C --> I
    C --> L
    D --> H
    D --> J
    D --> K
    C --> E
    D --> E
    E --> F
    F --> U
```

### 7.3 Chatbot Capabilities — Detailed Scenarios

#### Scenario 1: Client Impact Assessment by Sector

```
Lawyer: "Which of my tech sector clients are affected by the new PDPA 
         breach notification amendments?"

System internally:
  1. Identifies the amendment: PDPA (Amendment) Regulations 2026
  2. Maps amendment to affected sectors: TECH, HEALTH, FINSERV
  3. Filters by TECH sector as requested
  4. Queries knowledge graph for all clients tagged TECH
  5. For each client, checks active matters and existing documents
  6. Ranks clients by exposure level

Response:
  "Based on the PDPA (Amendment) Regulations 2026 (S 342/2026), 
   which reduces the mandatory breach notification window from 
   3 business days to 2 business days effective 1 October 2026, 
   the following TECH sector clients are affected:

   🔴 HIGH IMPACT (3 clients):
   1. TechCorp Pte Ltd — Active DPA review engagement; their current 
      incident response plan references the 72-hour window.
      → Action: Update incident response plan; issue client advisory
      → Deadline: Before 1 Oct 2026
   2. DataVault Singapore — Retainer client for PDPA advisory; their 
      compliance manual references outdated thresholds.
      → Action: Revise compliance manual sections 3.2, 5.1
      → Deadline: 17 Sep 2026 (2 weeks before commencement)
   3. CloudFirst Pte Ltd — Data processor handling personal data; 
      new constructive knowledge provision affects their monitoring 
      obligations.
      → Action: Review data processing agreement; advise on 
         monitoring system upgrade
      → Deadline: Before 1 Oct 2026

   🟡 MODERATE IMPACT (2 clients):
   [...]

   📋 Summary of required actions:
   - Issue client advisory to all HIGH IMPACT clients within 5 days
   - 3 documents need revision [view list]
   - 1 client engagement needs scope update [details]"
```

#### Scenario 2: Client Matter Timeline Risk

```
Lawyer: "Client B's enforcement action is expected to conclude in 
         March 2027. Will the new penalty regime under the amended 
         Companies Act apply to their case?"

System internally:
  1. Identifies the client and matter
  2. Retrieves the relevant amendment details
  3. Analyses transitional provisions
  4. Considers commencement date vs. matter timeline
  5. Checks for any court guidance on retrospective application

Response:
  "The Companies (Amendment) Act 2026 introduces enhanced penalty 
   provisions under s.157A, effective 1 January 2027. Your client's 
   enforcement action (Matter #M-2025-0089) is expected to conclude 
   in March 2027.

   ⚠️ Key considerations:
   1. The amended penalty regime applies to offences committed on 
      or after 1 Jan 2027. Since the alleged conduct occurred in 
      2024, the previous penalty regime should apply.
   2. However, the transitional provisions in s.5 of the Amendment 
      Act state that proceedings commenced after 1 Jan 2027 are 
      subject to the new procedural requirements.
   3. Your client's matter was commenced in June 2025, so the old 
      procedural framework should apply.

   📋 Recommended actions:
   - Confirm with ACRA that the old regime applies (para 3(b) of 
     the transitional provisions)
   - Update your submissions to pre-emptively address this point
   - Inform the client that the penalty exposure remains at the 
     previous cap of $5,000 (not the new $50,000)

   ⚖️ Relevant authority: [See transitional provisions analysis]"
```

#### Scenario 3: Proactive Client Notification Assessment

```
Lawyer: "Which of my clients should be informed about the upcoming 
         Companies Amendment Bill that's currently at Second Reading?"

System internally:
  1. Retrieves parliamentary signal: Companies Amendment Bill 2026
  2. Identifies target sectors: CORPGOV, FINSERV, ENVIRON
  3. Queries all clients in these sectors
  4. Assesses each client's exposure to proposed changes
  5. Considers matter timelines vs. estimated commencement

Response:
  "The Companies (Amendment) Bill 2026 (Bill No. 42/2026) passed 
   its Second Reading on 3 September 2026. Based on typical 
   legislative timelines, the amendments are estimated to commence 
   in Q1 2027.

   ⚠️ Note: This is a parliamentary early warning — the Bill has 
   not yet been enacted. Changes may occur before final passage.

   📢 Clients to proactively inform (5):

   1. MegaCorp Holdings (CORPGOV) — The proposed enhanced director 
      liability provisions will affect their board governance 
      framework. Their board meets quarterly (next: November 2026).
      → Recommend: Brief the board at the November meeting
      → Urgency: Moderate (estimated commencement Q1 2027)

   2. GreenTech Capital (CORPGOV, ENVIRON) — The mandatory climate 
      risk disclosure requirements will apply to them as a large 
      company. They currently have no ESG reporting framework.
      → Recommend: Begin ESG reporting setup now; 3-6 months 
         typical implementation
      → Urgency: High (lead time needed)

   3. FinSecure Pte Ltd (FINSERV) — Enhanced audit committee 
      requirements may affect their current governance structure.
      → Recommend: Review current audit committee composition
      → Urgency: Low (may be grandfathered under transitional 
         provisions)

   [2 more clients...]

   📄 Draft advisory template available [Generate Draft →]"
```

#### Scenario 4: Document Revision Guidance Per Client

```
Lawyer: "What documents do I need to update for Client A in light 
         of the MAS Notice 655 revisions?"

System internally:
  1. Retrieves all documents linked to Client A
  2. Filters by those referencing MAS Notice 655
  3. Runs impact analysis on each document
  4. Generates specific revision recommendations

Response:
  "For Client A (FinSecure Pte Ltd), the following documents 
   reference MAS Notice 655 and require revision:

   📄 Documents requiring update (4):

   1. Cybersecurity Policy Framework (DOC-2024-0445)
      - Section 3.2 references the old penetration testing 
        frequency (annual) — now required quarterly
      - Section 5.1 password policy references superseded 
        MAS guidance — update to new minimum standards
      - 🔴 Priority: CRITICAL (client-facing, active use)

   2. Board Risk Report Template (TPL-2023-0112)
      - Appendix B cyber-risk metrics need new KPIs per 
        revised Notice
      - 🟡 Priority: MODERATE (next board meeting in Nov)

   3. Vendor Assessment Checklist (CKL-2024-0067)
      - Questions 14-18 based on old third-party risk 
        requirements — need full rewrite
      - 🟡 Priority: MODERATE (next vendor review in Dec)

   4. Training Slide Deck: MAS Compliance (TRN-2024-0023)
      - Multiple slides reference superseded provisions
      - 🟢 Priority: LOW (next training session in Q1 2027)

   [View detailed diff for each document →]"
```

### 7.4 Chatbot Technical Implementation

| Component | Technology | Details |
|---|---|---|
| **LLM Backend** | OpenAI GPT-4o via OpenRouter (`openrouter.ai/api/v1`) | Primary reasoning engine; OpenRouter provides unified API with fallback model flexibility |
| **OpenRouter Configuration** | API Key auth, model: `openai/gpt-4o` | Supports fallback to `openai/gpt-4o-mini` for lower-priority queries |
| **Retrieval** | Hybrid: Knowledge Graph (Cypher queries) + Vector Search (pgvector) | Graph traversal for structured relationships; vector search for semantic similarity |
| **Embedding Model** | `openai/text-embedding-3-large` (via OpenRouter or direct) | 3072-dimensional embeddings for high-fidelity semantic search |
| **Context Window Management** | Smart chunking with priority ranking + caching | Most relevant context packed first; citations always included; cached responses for repeated queries |
| **Conversation Memory** | PostgreSQL-backed session store | Maintains context across multi-turn conversations within a session |
| **Citation Engine** | Custom post-processor | Every factual claim linked to source regulation, document, or knowledge graph node |
| **Guardrails** | Legal-specific validation layer | Prevents hallucination of legal provisions; validates all cited sections exist in the database |

### 7.5 Token Optimisation Strategy

Since OpenRouter usage is metered by token, the system employs aggressive optimisation without sacrificing output quality:

| Strategy | Implementation | Estimated Savings |
|---|---|---|
| **Response Caching** | Cache LLM responses for identical or near-identical queries (semantic hash matching). TTL: 24 hours or until underlying data changes | 30–40% fewer API calls |
| **Tiered Model Routing** | Use `gpt-4o-mini` for simple lookups and classifications; `gpt-4o` only for complex legal reasoning | 50–60% cost reduction for simple queries |
| **Smart Context Windowing** | Retrieve only the most relevant knowledge graph paths and document chunks; rank by relevance score before packing into context | 20–30% fewer input tokens |
| **Prompt Compression** | Use structured prompts with minimal boilerplate; compress system instructions; avoid redundant context | 10–15% fewer input tokens |
| **Incremental Reasoning** | For multi-step queries, cache intermediate reasoning steps; don't re-derive context that hasn't changed | 20–30% fewer tokens for follow-up queries |
| **Embedding Caching** | Cache all generated embeddings; only regenerate when source content changes (tracked by content hash) | 90%+ fewer embedding API calls |
| **Batch Processing** | When analysing multiple documents or clients for the same amendment, batch the analysis in a single prompt rather than individual calls | 40–50% fewer calls for batch operations |

**Estimated Monthly Token Budget** (for a firm with ~50 active clients):

| Usage Type | Estimated Tokens/Month | Model | Estimated Cost |
|---|---|---|---|
| Impact analysis (amendments) | ~500K input + 200K output | GPT-4o | ~$5 |
| Chatbot conversations | ~2M input + 500K output | GPT-4o / GPT-4o-mini | ~$15 |
| Embedding generation | ~1M tokens | text-embedding-3-large | ~$0.13 |
| Parliamentary analysis | ~300K input + 100K output | GPT-4o | ~$3 |
| **Total estimated** | | | **~$25/month** |

### 7.6 Prompt Engineering Architecture

The chatbot uses a **multi-agent prompt chain**:

```
1. QUERY ANALYZER AGENT (gpt-4o-mini — cost-efficient)
   Input:  Raw user query + conversation history
   Output: Structured intent + entities + required data sources
   
2. DATA RETRIEVAL AGENT (no LLM — pure code)
   Input:  Structured query from step 1
   Output: Relevant context from knowledge graph + vector store
   Actions: Cypher queries, vector similarity search, document retrieval
   
3. LEGAL REASONING AGENT (gpt-4o — full reasoning)
   Input:  User query + retrieved context + amendment details
   Output: Structured legal analysis with conclusions
   System prompt includes:
   - Singapore legal system context
   - Interpretation rules (purposive approach per s.9A Interpretation Act)
   - Professional conduct obligations
   - Disclaimer requirements
   Token budget: Dynamically allocated based on query complexity
   
4. RESPONSE FORMATTER AGENT (gpt-4o-mini — cost-efficient)
   Input:  Legal analysis from step 3
   Output: User-friendly response with:
   - Clear answer to the question
   - Supporting reasoning
   - Cited sources (with links)
   - Recommended actions (prioritised)
   - Caveats and limitations
```

---

## 8. Module 5 — Regulatory Diff Viewer (Optional Feature)

### 8.1 Purpose

A GitHub-style diff interface that allows lawyers to visually compare versions of legislation, regulations, guidance notes, and firm documents — seeing exactly what changed, when, and why it matters.

### 8.2 Interface Design

The diff viewer provides three viewing modes:

#### 8.2.1 Side-by-Side View (Split Diff)

```
┌─────────────────────────────────┬─────────────────────────────────┐
│ PDPA s.26D — Before             │ PDPA s.26D — After              │
│ (v1.2.0, effective 1 Feb 2021)  │ (v1.3.0, effective 1 Oct 2026)  │
├─────────────────────────────────┼─────────────────────────────────┤
│                                 │                                 │
│ 26D.—(1) A data controller      │ 26D.—(1) A data controller      │
│ shall, on becoming aware of a   │ shall, on becoming aware of a   │
│ notifiable data breach, notify  │ notifiable data breach, notify  │
│ the Commission as soon as       │ the Commission as soon as       │
│ practicable but in any case     │ practicable but in any case     │
│ not later than ███ 3 calendar   │ not later than ███ 2 business   │
│ ███ days after the day the data │ ███ days after the day the data │
│ controller becomes aware of     │ controller becomes aware of     │
│ the data breach.                │ the data breach.                │
│                                 │                                 │
│                                 │ ███ (1A) For the purposes of    │
│                                 │ ███ subsection (1), a data      │
│                                 │ ███ controller is deemed to     │
│                                 │ ███ have become aware of a      │
│                                 │ ███ notifiable data breach      │
│                                 │ ███ when the controller ought   │
│                                 │ ███ reasonably to have become   │
│                                 │ ███ aware of the breach.        │
│                                 │                                 │
└─────────────────────────────────┴─────────────────────────────────┘
```

#### 8.2.2 Unified View (Inline Diff)

Shows changes inline with red/green highlighting (like `git diff --unified`).

#### 8.2.3 Annotated View (RegulaSense-Enhanced)

The unique value-add: alongside the diff, the system shows **annotations** explaining the practical impact of each change, **including which clients are affected**:

```
┌─────────────────────────────────────────────────────────────────────┐
│ PDPA s.26D — Annotated Diff                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  26D.—(1) ... not later than                                        │
│ - 3 calendar days                                                   │
│ + 2 business days                                                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 💡 IMPACT ANNOTATION                                        │   │
│  │                                                              │   │
│  │ This change REDUCES the notification window significantly:   │   │
│  │ • Old: 3 calendar days (≈ 72 hours including weekends)       │   │
│  │ • New: 2 business days (≈ 48 working hours, excl weekends)   │   │
│  │                                                              │   │
│  │ Practical effect: If a breach is discovered on a Friday,     │   │
│  │ the old rule gave until Monday. The new rule gives until     │   │
│  │ Tuesday (next business day + 1).                             │   │
│  │                                                              │   │
│  │ 🔴 SEVERITY: CRITICAL                                       │   │
│  │ 👥 Affected clients: 8 (TECH: 5, HEALTH: 2, FINSERV: 1)    │   │
│  │ 📄 Affected firm assets: 4 documents, 2 workflows           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ + (1A) For the purposes of subsection (1), a data controller       │
│ + is deemed to have become aware of a notifiable data breach       │
│ + when the controller ought reasonably to have become aware        │
│ + of the breach.                                                    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 💡 IMPACT ANNOTATION                                        │   │
│  │                                                              │   │
│  │ NEW constructive knowledge provision. This means the clock   │   │
│  │ starts ticking not just when the controller actually knows   │   │
│  │ about the breach, but when it SHOULD have known.             │   │
│  │                                                              │   │
│  │ Implication: Clients need robust detection and monitoring    │   │
│  │ systems. "We didn't know" is no longer a defence if a        │   │
│  │ reasonable organisation would have detected the breach.      │   │
│  │                                                              │   │
│  │ 🟡 SEVERITY: MODERATE                                       │   │
│  │ Action: Update breach response SOPs to include proactive     │   │
│  │ monitoring obligations for all TECH sector clients           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.3 Diff Engine Implementation

| Component | Technology | Purpose |
|---|---|---|
| Text Diffing | `difflib` (Python) / `diff-match-patch` (JS) | Compute character-level and line-level diffs |
| Section-Aware Diffing | Custom parser | Align diffs by section/clause structure, not just line numbers |
| Semantic Diffing | LLM-powered (GPT-4o-mini via OpenRouter) | Identify when text is reworded but meaning is preserved vs. substantively changed |
| Annotation Generation | LLM agent (GPT-4o via OpenRouter) | Generate plain-language impact annotations for each material change |
| Rendering | React + Monaco Editor (diff mode) | GitHub-style split/unified diff UI with syntax highlighting |
| Version Selection | Custom timeline picker | Select any two versions of a legislative instrument to compare |
| Export | PDF / DOCX generator | Export annotated diffs for client communications or internal memos |

---

## 9. Technology Stack

### 9.1 Full Stack Overview

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | Next.js 15 (App Router) + TypeScript | Server-side rendering, React Server Components for performance |
| **UI Framework** | shadcn/ui + Radix UI + Tailwind CSS | Accessible, customisable components; legal professionals expect a polished UI |
| **Diff Viewer** | Monaco Editor (diff mode) or react-diff-viewer-continued | Battle-tested diff rendering with split/unified views |
| **Charts & Dashboards** | Recharts + Tremor | Severity distribution, timeline views, trend analysis |
| **Backend API** | FastAPI (Python) | High-performance async API; excellent for AI/ML integration |
| **Task Queue** | Celery + Redis | Distributed task processing for scrapers and analysis pipelines |
| **Primary Database** | PostgreSQL 16 + pgvector | Relational data + vector embeddings in one database |
| **Knowledge Graph** | Neo4j 5 | Native graph database for regulatory-asset-client relationship mapping |
| **Vector Store** | pgvector (built into PostgreSQL) | Semantic search over document embeddings without extra infrastructure |
| **LLM Orchestration** | LangChain / LangGraph | Agent orchestration, tool calling, memory management |
| **LLM Provider** | OpenAI GPT-4o via OpenRouter (`openrouter.ai/api/v1`) | Unified API; model flexibility; pay-per-token; easy fallback to gpt-4o-mini |
| **Embedding Model** | OpenAI `text-embedding-3-large` (via OpenRouter or direct) | 3072-dimensional embeddings for high-fidelity semantic search |
| **Web Scraping** | Playwright + httpx + BeautifulSoup | Headless browser for JS-rendered sites; HTTP for static pages |
| **PDF Processing** | PyMuPDF + pdfplumber + Tesseract OCR (fallback) | Extract structured text from regulatory PDFs (text-based and scanned) |
| **Authentication** | Custom JWT auth (simple login system) | Lightweight auth for MVP; no external identity provider needed |
| **Caching** | Redis | API response caching, LLM response caching, rate limiting, session storage |
| **Logging & Monitoring** | Structured logging (structlog) + Sentry | Error tracking, performance monitoring |
| **Deployment** | Docker + Docker Compose (on-premise MVP) | Single-command deployment on any machine with Docker; cloud-ready architecture |
| **CI/CD** | GitHub Actions | Automated testing, linting |
| **File Storage** | Local filesystem (Docker volume) | MVP uses local storage; can migrate to S3/GCS for cloud deployment |

### 9.2 OpenRouter Integration Details

```python
# OpenRouter API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = "sk-or-..."  # From environment variable

# Model routing configuration
MODEL_CONFIG = {
    "complex_reasoning": {
        "model": "openai/gpt-4o",
        "max_tokens": 4096,
        "temperature": 0.1,
        "use_for": ["legal_analysis", "impact_assessment", "client_advisory"]
    },
    "simple_tasks": {
        "model": "openai/gpt-4o-mini",
        "max_tokens": 2048,
        "temperature": 0.0,
        "use_for": ["query_classification", "entity_extraction", 
                     "response_formatting", "semantic_diffing"]
    },
    "embeddings": {
        "model": "openai/text-embedding-3-large",
        "dimensions": 3072
    }
}

# All API calls go through OpenRouter's unified endpoint
# Headers include:
# - Authorization: Bearer {OPENROUTER_API_KEY}
# - HTTP-Referer: https://regulasense.app (for OpenRouter analytics)
# - X-Title: RegulaSense (for OpenRouter dashboard)
```

### 9.3 Architecture Diagram — On-Premise Deployment (MVP)

```mermaid
graph TB
    subgraph "Host Machine (Docker Compose)"
        subgraph "Frontend Container"
            FE["Next.js Frontend<br/>(Port 3000)"]
        end

        subgraph "Backend Containers"
            API["FastAPI Backend<br/>(Uvicorn, Port 8000)"]
            WS["WebSocket Server<br/>(Chat, Port 8001)"]
        end

        subgraph "Worker Containers"
            CW["Celery Workers<br/>(Scraping + Analysis)"]
            CB["Celery Beat<br/>(Scheduled Tasks)"]
        end

        subgraph "Data Containers"
            PG["PostgreSQL 16<br/>+ pgvector<br/>(Port 5432)"]
            N4J["Neo4j 5<br/>(Port 7474/7687)"]
            RD["Redis<br/>(Port 6379)"]
        end

        subgraph "Volumes"
            V1["pg_data"]
            V2["neo4j_data"]
            V3["scraped_docs"]
        end
    end

    subgraph "External Services"
        OR["OpenRouter API<br/>(openrouter.ai)"]
    end

    FE <--> API
    FE <--> WS
    API <--> PG
    API <--> N4J
    API <--> RD
    API <--> OR
    CW <--> RD
    CW <--> PG
    CW <--> N4J
    CW <--> OR
    CB --> RD
    PG --> V1
    N4J --> V2
    CW --> V3
```

---

## 10. Database Schema (PostgreSQL)

### 10.1 Core Tables

```sql
-- ============================================================
-- REGULATORY DATA
-- ============================================================

CREATE TABLE legislative_instruments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_type VARCHAR(50) NOT NULL,  -- 'act', 'subsidiary_legislation', 'guidance', 'notice', 'circular', 'court_decision'
    title           TEXT NOT NULL,
    short_title     VARCHAR(255),
    chapter_number  VARCHAR(20),
    instrument_number VARCHAR(50),
    issuing_authority VARCHAR(100),
    regulatory_domain TEXT[],              -- ARRAY of domains: 'banking', 'data_protection', etc.
    industry_sectors TEXT[],               -- ARRAY of sector codes: 'TECH', 'FINSERV', etc.
    jurisdiction    VARCHAR(50) DEFAULT 'singapore',
    current_version VARCHAR(20),
    status          VARCHAR(30) NOT NULL,  -- 'in_force', 'not_yet_in_force', 'repealed', 'superseded'
    url             TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE instrument_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id   UUID REFERENCES legislative_instruments(id),
    version         VARCHAR(20) NOT NULL,
    full_text       TEXT NOT NULL,
    structured_json JSONB,                 -- Section-by-section structured content
    text_hash       VARCHAR(64) NOT NULL,  -- SHA-256 of full_text
    gazette_reference VARCHAR(50),
    effective_date  DATE,
    gazette_date    DATE,
    source_url      TEXT,
    source_format   VARCHAR(20),           -- 'html', 'pdf', 'rss'
    embedding       VECTOR(3072),          -- pgvector embedding of full text
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(instrument_id, version)
);

CREATE TABLE instrument_sections (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id   UUID REFERENCES legislative_instruments(id),
    version_id      UUID REFERENCES instrument_versions(id),
    section_number  VARCHAR(20) NOT NULL,
    section_title   TEXT,
    section_text    TEXT NOT NULL,
    parent_section  VARCHAR(20),           -- For subsections
    embedding       VECTOR(3072),          -- Section-level embedding
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sections_embedding ON instrument_sections 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================
-- PARLIAMENTARY MONITORING (NEW)
-- ============================================================

CREATE TABLE parliamentary_signals (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_type         VARCHAR(50) NOT NULL,  -- 'bill_first_reading', 'bill_second_reading', 'bill_third_reading', 'ministerial_statement', 'select_committee_report'
    bill_title          TEXT,
    bill_number         VARCHAR(50),
    target_instrument_id UUID REFERENCES legislative_instruments(id),
    sitting_date        DATE NOT NULL,
    reading_stage       VARCHAR(30),           -- 'first', 'second', 'third', 'committee', 'enacted'
    proposed_changes    JSONB,                 -- Structured summary of proposed amendments
    summary             TEXT,
    hansard_url         TEXT,
    bill_pdf_url        TEXT,
    industry_sectors    TEXT[],                -- Sectors likely affected
    confidence_level    VARCHAR(20),           -- 'high', 'moderate', 'low'
    estimated_enactment DATE,
    estimated_commencement DATE,
    status              VARCHAR(30) DEFAULT 'monitoring',  -- 'monitoring', 'enacted', 'lapsed', 'withdrawn'
    llm_analysis        JSONB,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AMENDMENTS & CHANGES
-- ============================================================

CREATE TABLE amendments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id       UUID REFERENCES legislative_instruments(id),
    parliamentary_signal_id UUID REFERENCES parliamentary_signals(id),  -- Link to the signal that predicted this
    amendment_type      VARCHAR(50) NOT NULL,  -- 'textual_amendment', 'new_provision', 'repeal', 'commencement', 'substitution'
    gazette_reference   VARCHAR(50),
    gazette_date        DATE,
    commencement_date   DATE,
    commencement_type   VARCHAR(30),           -- 'fixed_date', 'ministerial_order', 'immediate', 'unknown'
    transitional_provisions JSONB,
    summary             TEXT,
    llm_analysis        JSONB,                 -- Detailed LLM-generated analysis
    industry_sectors    TEXT[],                 -- Sectors affected
    severity_score      DECIMAL(3,2),
    severity_level      INTEGER CHECK (severity_level IN (1, 2, 3)),
    processing_status   VARCHAR(30) DEFAULT 'pending',
    detected_at         TIMESTAMPTZ DEFAULT NOW(),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE amendment_diffs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amendment_id    UUID REFERENCES amendments(id),
    old_version_id  UUID REFERENCES instrument_versions(id),
    new_version_id  UUID REFERENCES instrument_versions(id),
    section_number  VARCHAR(20),
    diff_type       VARCHAR(20) NOT NULL,  -- 'addition', 'deletion', 'modification'
    old_text        TEXT,
    new_text        TEXT,
    unified_diff    TEXT,                   -- Standard unified diff format
    annotation      TEXT,                   -- LLM-generated impact annotation
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDUSTRY SECTORS
-- ============================================================

CREATE TABLE sectors (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(20) UNIQUE NOT NULL,  -- 'TECH', 'FINSERV', etc.
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    key_regulatory_bodies TEXT[],
    key_legislation TEXT[],
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CLIENTS & MATTERS
-- ============================================================

CREATE TABLE clients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    industry        VARCHAR(100),
    risk_profile    VARCHAR(30) DEFAULT 'standard',
    sector_codes    TEXT[],                -- Array of sector codes: ['TECH', 'FINSERV']
    regulatory_domains TEXT[],
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE client_sectors (
    client_id       UUID REFERENCES clients(id),
    sector_id       UUID REFERENCES sectors(id),
    PRIMARY KEY (client_id, sector_id)
);

CREATE TABLE matters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES clients(id),
    title           TEXT NOT NULL,
    practice_area   VARCHAR(100),
    description     TEXT,
    status          VARCHAR(30) DEFAULT 'active',
    expected_completion DATE,
    regulatory_references TEXT[],          -- Acts/sections relevant to this matter
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE client_impact_assessments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    amendment_id    UUID REFERENCES amendments(id),
    parliamentary_signal_id UUID REFERENCES parliamentary_signals(id),  -- For early warnings
    client_id       UUID REFERENCES clients(id),
    matter_id       UUID REFERENCES matters(id),
    impact_type     VARCHAR(50) NOT NULL,
    severity_level  INTEGER CHECK (severity_level IN (1, 2, 3)),
    impact_summary  TEXT NOT NULL,
    recommended_actions JSONB,
    notify_client   BOOLEAN DEFAULT FALSE,
    notification_urgency VARCHAR(20),
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMPTZ,
    status          VARCHAR(30) DEFAULT 'pending',
    assigned_to     UUID,
    resolved_at     TIMESTAMPTZ,
    resolution_notes TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- FIRM DOCUMENTS (Client-Specific Focus)
-- ============================================================

CREATE TABLE firm_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       UUID REFERENCES clients(id),  -- NULL for firm-wide documents
    matter_id       UUID REFERENCES matters(id),   -- NULL for non-matter-specific docs
    title           TEXT NOT NULL,
    document_type   VARCHAR(50) NOT NULL,  -- 'template', 'checklist', 'playbook', 'advisory', 'training', 'sop', 'memo', 'dpa', 'contract'
    practice_area   VARCHAR(100),
    content         TEXT,
    file_path       TEXT,
    file_hash       VARCHAR(64),
    embedding       VECTOR(3072),
    status          VARCHAR(30) DEFAULT 'active',
    last_reviewed   DATE,
    reviewed_by     UUID,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE document_regulatory_references (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID REFERENCES firm_documents(id),
    instrument_id   UUID REFERENCES legislative_instruments(id),
    section_number  VARCHAR(20),
    reference_type  VARCHAR(30),           -- 'direct_citation', 'implements', 'based_on', 'references'
    reference_text  TEXT,
    confidence      DECIMAL(3,2),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AUTHENTICATION (Simple JWT Auth for MVP)
-- ============================================================

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(30) DEFAULT 'associate',  -- 'admin', 'partner', 'associate', 'paralegal'
    practice_areas  TEXT[],
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    token_hash      VARCHAR(255) NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CHAT & AUDIT
-- ============================================================

CREATE TABLE chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    title           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_message_at TIMESTAMPTZ
);

CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES chat_sessions(id),
    role            VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content         TEXT NOT NULL,
    citations       JSONB,                 -- Array of source references
    tool_calls      JSONB,                 -- Any agent tool calls made
    tokens_used     JSONB,                 -- {"input": N, "output": N, "model": "..."}
    cached          BOOLEAN DEFAULT FALSE, -- Was this response served from cache?
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      VARCHAR(50) NOT NULL,
    entity_type     VARCHAR(50),
    entity_id       UUID,
    user_id         UUID,
    details         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- LLM RESPONSE CACHE (Token Optimisation)
-- ============================================================

CREATE TABLE llm_cache (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash      VARCHAR(64) NOT NULL,  -- SHA-256 of normalised query + context
    model           VARCHAR(100) NOT NULL,
    response        TEXT NOT NULL,
    tokens_input    INTEGER,
    tokens_output   INTEGER,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_llm_cache_hash ON llm_cache(query_hash, model);
```

---

## 11. API Design

### 11.1 Core API Endpoints

#### Authentication (Simple JWT)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a new user (admin only) |
| `POST` | `/api/v1/auth/login` | Login and receive JWT token |
| `POST` | `/api/v1/auth/logout` | Invalidate session |
| `GET` | `/api/v1/auth/me` | Get current user profile |

#### Regulatory Data

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/instruments` | List all legislative instruments (paginated, filterable by sector) |
| `GET` | `/api/v1/instruments/{id}` | Get instrument details with current version |
| `GET` | `/api/v1/instruments/{id}/versions` | List all versions of an instrument |
| `GET` | `/api/v1/instruments/{id}/versions/{v1}/diff/{v2}` | Get diff between two versions |
| `GET` | `/api/v1/instruments/{id}/sections` | List all sections of current version |
| `GET` | `/api/v1/amendments` | List all detected amendments (filterable by date, severity, sector, status) |
| `GET` | `/api/v1/amendments/{id}` | Get amendment details with impact analysis |
| `GET` | `/api/v1/amendments/timeline` | Get amendments organised by commencement timeline |

#### Parliamentary Monitoring

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/parliamentary/signals` | List all parliamentary early warnings |
| `GET` | `/api/v1/parliamentary/signals/{id}` | Get signal details with affected clients |
| `GET` | `/api/v1/parliamentary/bills` | List tracked Bills with progress status |
| `GET` | `/api/v1/parliamentary/bills/{id}/timeline` | Get Bill progress timeline |

#### Impact Analysis (Client-Centric)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/impacts` | List all impact assessments (filterable by severity, sector, client) |
| `GET` | `/api/v1/impacts/{id}` | Get detailed impact assessment |
| `PATCH` | `/api/v1/impacts/{id}` | Update impact status (acknowledge, resolve, dismiss) |
| `GET` | `/api/v1/impacts/by-sector/{sector_code}` | Get all impacts for a specific sector |
| `GET` | `/api/v1/impacts/by-client/{client_id}` | Get all impacts for a specific client |
| `GET` | `/api/v1/impacts/dashboard` | Aggregated dashboard data (counts by severity, sector, status, timeline) |

#### Clients & Matters

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/clients` | List clients (filterable by sector) |
| `POST` | `/api/v1/clients` | Create a new client with sector tags |
| `GET` | `/api/v1/clients/{id}` | Get client details with sector tags and active matters |
| `PUT` | `/api/v1/clients/{id}` | Update client details / sector tags |
| `GET` | `/api/v1/clients/{id}/impacts` | Get all regulatory impacts for a client |
| `GET` | `/api/v1/clients/{id}/early-warnings` | Get parliamentary early warnings relevant to client |
| `GET` | `/api/v1/clients/{id}/matters/{matter_id}/timeline-risk` | Analyse timeline risk for a specific matter |
| `POST` | `/api/v1/clients/{id}/matters` | Create a new matter for a client |

#### Firm Documents

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/documents` | List firm documents (filterable by type, status, client) |
| `POST` | `/api/v1/documents` | Upload / register a new firm document |
| `GET` | `/api/v1/documents/{id}` | Get document details with regulatory references |
| `GET` | `/api/v1/documents/{id}/impacts` | Get all impacts affecting this document |
| `POST` | `/api/v1/documents/{id}/analyse` | Trigger re-analysis of regulatory references |

#### Chatbot

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat/sessions` | Create a new chat session |
| `POST` | `/api/v1/chat/sessions/{id}/messages` | Send a message and get AI response (streaming via SSE) |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | Get chat history for a session |

#### Diff Viewer

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/diff/{instrument_id}?from={v1}&to={v2}` | Get structured diff with annotations |
| `GET` | `/api/v1/diff/{instrument_id}/annotated` | Get annotated diff with client impact data |

#### Sectors

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/sectors` | List all industry sectors |
| `GET` | `/api/v1/sectors/{code}` | Get sector details with linked regulations and clients |
| `GET` | `/api/v1/sectors/{code}/impacts` | Get all impacts affecting this sector |

---

## 12. Frontend Pages & UI Components

### 12.1 Page Map

| Page | Route | Description |
|---|---|---|
| **Login** | `/login` | Simple JWT login page |
| **Dashboard** | `/` | Overview with severity distribution, pending items, timeline, recent changes, parliamentary signals |
| **Amendments Feed** | `/amendments` | Chronological feed of all detected regulatory changes with filters by sector |
| **Amendment Detail** | `/amendments/{id}` | Full detail: what changed, what's affected, severity, timeline, affected clients by sector |
| **Early Warnings** | `/early-warnings` | Parliamentary signals: Bills in progress, Ministerial Statements, estimated timelines |
| **Impact Centre** | `/impacts` | All client impact assessments, grouped by severity/sector/status |
| **Client Overview** | `/clients` | Client list with sector tags and regulatory exposure summary |
| **Client Detail** | `/clients/{id}` | Client-specific impacts, matters, timeline risks, recommended actions |
| **Document Registry** | `/documents` | Firm documents with their regulatory health status (filterable by client) |
| **Document Detail** | `/documents/{id}` | Document details, linked regulations, pending impacts |
| **Diff Viewer** | `/diff/{instrument_id}` | Side-by-side / unified / annotated diff viewer |
| **Chat** | `/chat` | Conversational AI interface |
| **Settings** | `/settings` | Scraper configuration, user management, sector configuration |

### 12.2 Dashboard Wireframe Description

The dashboard should include:

1. **Header Stats Bar**: 5 cards showing:
   - Total pending client impacts (with severity breakdown 🔴🟡🟢)
   - Amendments detected this month
   - Clients needing notification
   - Documents requiring review
   - Active parliamentary signals (Bills in progress)

2. **Severity Distribution**: Donut chart showing Critical / Moderate / Low distribution

3. **Upcoming Timeline**: Horizontal timeline bar showing:
   - Enacted amendments by commencement date (solid markers)
   - Parliamentary signals by estimated commencement (dashed markers)
   - Countdown badges for each

4. **Recent Amendments Feed**: Card list of the 10 most recent changes, each showing:
   - Instrument title and amendment summary
   - Severity badge (🔴🟡🟢)
   - Affected sectors (pill badges: `TECH` `FINSERV` `HEALTH`)
   - Commencement date with countdown
   - Number of affected clients
   - Quick action buttons (View Details, Acknowledge, Assign)

5. **Parliamentary Early Warnings**: Dedicated section showing:
   - Bills currently progressing through Parliament
   - Reading stage indicator (1st → 2nd → 3rd → Enacted)
   - Estimated impact by sector
   - Number of clients potentially affected

6. **Client Alert Queue**: List of clients who should be notified, grouped by sector, with:
   - Client name and sector tags
   - Amendment(s) affecting them
   - Urgency level
   - Draft advisory link

---

## 13. Security & Compliance

### 13.1 Data Security

| Concern | Mitigation |
|---|---|
| **Client confidentiality** | All client data stored locally (on-premise MVP). No client names, matter details, or confidential information sent to OpenRouter/OpenAI — only regulatory text and anonymised/abstracted queries |
| **LLM data privacy** | Queries to OpenRouter are structured to contain only regulatory text (publicly available) and anonymised client context (sector tags, not names). Sensitive details are injected locally after LLM response |
| **Access control** | JWT-based auth with role-based permissions: Admin, Partner, Associate, Paralegal |
| **Audit trail** | Immutable audit log for all system actions, recommendations, and user decisions |
| **Data at rest** | PostgreSQL encryption via `pgcrypto`; Docker volumes with host-level encryption |
| **Data in transit** | HTTPS (TLS 1.3) for all API calls; HTTPS for OpenRouter API calls |
| **Token tracking** | All LLM API calls logged with token counts for cost monitoring |

### 13.2 LLM Privacy-Safe Query Pattern

```python
# NEVER send to LLM:
# - Client names
# - Matter details with identifying information  
# - Actual dollar amounts from client matters
# - Internal fee arrangements

# SAFE to send to LLM:
# - Regulatory text (publicly available)
# - Sector codes (generic: "TECH", "FINSERV")
# - Anonymised scenario descriptions
# - "A company in the technology sector processing personal data..."

# After LLM response, locally enrich with:
# - Actual client names
# - Specific matter references
# - Document links
# - Internal deadlines
```

### 13.3 Professional Conduct Compliance

| Rule | System Design |
|---|---|
| **Legal Professional Privilege** | Chat conversations are marked as internal work product; system does not share between matters without authorisation |
| **Competence obligation** | System is a tool to *assist* lawyers, not replace their judgment; all recommendations clearly labelled as AI-generated |
| **Conflict checks** | Client data is siloed; cross-client analysis only at aggregate/anonymised level (by sector) |
| **Record retention** | Configurable retention policies aligned with firm's record management policy |

---

## 14. Phased Implementation Roadmap

### Phase 1 — Foundation (Weeks 1–4)

> **Goal**: Core infrastructure, data ingestion from primary sources, basic change detection, and simple auth

| Week | Tasks |
|---|---|
| **Week 1** | Project setup: Next.js frontend, FastAPI backend, PostgreSQL + pgvector, Neo4j, Redis. Docker Compose for on-premise deployment. CI/CD pipeline. Simple JWT auth system. Design system and base UI components. Login page |
| **Week 2** | SSO scraper (primary legislation). Gazette RSS monitor. Parliamentary Hansard scraper (initial). Data normalisation pipeline. Instrument version storage with hashing |
| **Week 3** | MAS, PDPC, ACRA scrapers. PairSearch scraper. Generic PDF document scraper (PyMuPDF + pdfplumber + OCR). Section-level parsing and structuring. Basic change detection (hash-based) |
| **Week 4** | Semantic diff engine. Embedding generation (via OpenRouter). Basic amendment detection and storage. Industry sector taxonomy setup. Admin dashboard for scraper monitoring |

**Deliverables**: Working data ingestion pipeline with 6+ source scrapers (including Parliament and PDF). Database populated with current Singapore legislation. Simple auth working. Basic change detection operational.

---

### Phase 2 — Intelligence & Client Focus (Weeks 5–8)

> **Goal**: Client-centric impact analysis, severity classification, sector-based mapping, and parliamentary early warning system

| Week | Tasks |
|---|---|
| **Week 5** | Client and sector data model. Client registration with sector tagging. Sector-regulation mapping (knowledge graph population). Parliamentary signal tracking (Bill progress through readings) |
| **Week 6** | Impact analysis pipeline: amendment → sector → clients. Client impact assessment generation. Severity scoring algorithm implementation. Matter timeline overlap detection |
| **Week 7** | Early Warning Engine: Parliamentary debates → potential amendment signals → affected sectors → affected clients. Confidence scoring for parliamentary signals. Bill progress tracking (First → Second → Third Reading) |
| **Week 8** | Dashboard: severity distribution, timeline view (with parliamentary signals), amendment feed, client alert queue. In-app notification system. Impact detail pages with recommended actions grouped by sector |

**Deliverables**: Working client-centric impact analysis. Severity classification operational. Parliamentary early warnings functional. Dashboard with real-time alerts.

---

### Phase 3 — Conversational AI (Weeks 9–12)

> **Goal**: Chatbot with full contextual awareness of regulations, clients (by sector), and parliamentary signals

| Week | Tasks |
|---|---|
| **Week 9** | Chat infrastructure: session management, message storage, streaming responses (SSE). OpenRouter integration with tiered model routing (gpt-4o for reasoning, gpt-4o-mini for classification). LLM response caching layer. Basic Q&A over regulatory database |
| **Week 10** | Knowledge graph query tools for the agent. Client-sector-aware context assembly. Privacy-safe query pattern (anonymise client details before sending to LLM). Multi-turn conversation with memory. Citation engine |
| **Week 11** | Advanced scenarios: client impact assessment by sector, matter timeline analysis, proactive notification guidance, parliamentary early warning Q&A. Prompt engineering with token optimisation. Legal reasoning validation and guardrails |
| **Week 12** | Chat UI polish: markdown rendering, citation links, suggested questions, conversation history. Token usage dashboard. Integration with impact centre and client pages |

**Deliverables**: Fully functional chatbot with token-optimised OpenRouter integration. Supports complex legal queries about client impacts, timelines, and parliamentary signals.

---

### Phase 4 — Diff Viewer & Polish (Weeks 13–16)

> **Goal**: GitHub-style diff viewer, firm document support, and production readiness for on-premise deployment

| Week | Tasks |
|---|---|
| **Week 13** | Diff viewer: side-by-side view, unified view. Section-aware diffing. Version selector. Syntax highlighting for legal text. Firm document upload and registration. Document regulatory reference extraction |
| **Week 14** | Annotated diff view with LLM-generated impact annotations (including affected clients by sector). Export to PDF/DOCX. Diff viewer integration with impact assessments. Document-level impact analysis |
| **Week 15** | End-to-end testing. Performance optimisation (Redis caching, query optimisation, embedding index tuning). Security audit. Token usage optimisation review. Load testing |
| **Week 16** | Docker Compose production configuration. Documentation. User guide. On-premise deployment instructions. Monitoring and alerting setup. User acceptance testing |

**Deliverables**: Complete platform with all five modules. On-premise Docker Compose deployment. Documentation and deployment guide.

---

## 15. Proposed File & Folder Structure

```
regulasense/
├── frontend/                          # Next.js 15 application
│   ├── src/
│   │   ├── app/                       # App Router pages
│   │   │   ├── login/
│   │   │   │   └── page.tsx           # Login page
│   │   │   ├── (dashboard)/
│   │   │   │   └── page.tsx           # Main dashboard
│   │   │   ├── amendments/
│   │   │   │   ├── page.tsx           # Amendments feed
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx       # Amendment detail
│   │   │   ├── early-warnings/
│   │   │   │   ├── page.tsx           # Parliamentary signals
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx       # Signal detail
│   │   │   ├── impacts/
│   │   │   │   └── page.tsx           # Impact centre
│   │   │   ├── clients/
│   │   │   │   ├── page.tsx           # Client overview (with sector filters)
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx       # Client detail
│   │   │   ├── documents/
│   │   │   │   ├── page.tsx           # Document registry
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx       # Document detail
│   │   │   ├── diff/
│   │   │   │   └── [instrumentId]/
│   │   │   │       └── page.tsx       # Diff viewer
│   │   │   ├── chat/
│   │   │   │   └── page.tsx           # Chatbot
│   │   │   ├── settings/
│   │   │   │   └── page.tsx           # Settings
│   │   │   └── layout.tsx             # Root layout
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn/ui components
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── AuthProvider.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── SeverityChart.tsx
│   │   │   │   ├── TimelineBar.tsx
│   │   │   │   ├── AmendmentFeed.tsx
│   │   │   │   ├── StatsCards.tsx
│   │   │   │   ├── ClientAlertQueue.tsx
│   │   │   │   └── ParliamentarySignals.tsx
│   │   │   ├── amendments/
│   │   │   │   ├── AmendmentCard.tsx
│   │   │   │   ├── SeverityBadge.tsx
│   │   │   │   └── SectorPills.tsx
│   │   │   ├── impacts/
│   │   │   │   ├── ImpactTable.tsx
│   │   │   │   ├── ImpactDetail.tsx
│   │   │   │   └── ClientImpactCard.tsx
│   │   │   ├── clients/
│   │   │   │   ├── ClientCard.tsx
│   │   │   │   ├── SectorFilter.tsx
│   │   │   │   └── MatterTimeline.tsx
│   │   │   ├── parliamentary/
│   │   │   │   ├── BillProgressTracker.tsx
│   │   │   │   ├── EarlyWarningCard.tsx
│   │   │   │   └── ReadingStageIndicator.tsx
│   │   │   ├── diff/
│   │   │   │   ├── DiffViewer.tsx
│   │   │   │   ├── SplitView.tsx
│   │   │   │   ├── UnifiedView.tsx
│   │   │   │   ├── AnnotatedView.tsx
│   │   │   │   └── VersionSelector.tsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── CitationCard.tsx
│   │   │   │   ├── SuggestedQuestions.tsx
│   │   │   │   └── TokenUsageBadge.tsx
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       ├── Header.tsx
│   │   │       └── NotificationBell.tsx
│   │   ├── lib/
│   │   │   ├── api.ts                 # API client (with JWT auth headers)
│   │   │   ├── auth.ts                # Auth utilities
│   │   │   ├── utils.ts
│   │   │   └── types.ts              # TypeScript types
│   │   └── styles/
│   │       └── globals.css
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── next.config.ts
│
├── backend/                           # FastAPI application
│   ├── app/
│   │   ├── main.py                    # FastAPI app entry point
│   │   ├── config.py                  # Configuration (incl. OpenRouter API key)
│   │   ├── database.py                # Database connections (PG + Neo4j)
│   │   ├── auth/                      # Simple JWT auth
│   │   │   ├── jwt.py                 # Token generation / validation
│   │   │   ├── dependencies.py        # Auth dependencies for route protection
│   │   │   └── password.py            # Password hashing (bcrypt)
│   │   ├── models/                    # SQLAlchemy / Pydantic models
│   │   │   ├── instrument.py
│   │   │   ├── amendment.py
│   │   │   ├── parliamentary.py
│   │   │   ├── document.py
│   │   │   ├── client.py
│   │   │   ├── sector.py
│   │   │   ├── impact.py
│   │   │   ├── user.py
│   │   │   └── chat.py
│   │   ├── routers/                   # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── instruments.py
│   │   │   ├── amendments.py
│   │   │   ├── parliamentary.py
│   │   │   ├── documents.py
│   │   │   ├── clients.py
│   │   │   ├── sectors.py
│   │   │   ├── impacts.py
│   │   │   ├── chat.py
│   │   │   └── diff.py
│   │   ├── services/                  # Business logic
│   │   │   ├── scraper/
│   │   │   │   ├── base.py            # Base scraper class
│   │   │   │   ├── sso_scraper.py     # Singapore Statutes Online
│   │   │   │   ├── mas_scraper.py     # MAS notices & circulars
│   │   │   │   ├── gazette_scraper.py # Government Gazette
│   │   │   │   ├── pdpc_scraper.py    # PDPC guidelines
│   │   │   │   ├── acra_scraper.py    # ACRA updates
│   │   │   │   ├── parliament_scraper.py  # Hansard & Bills (NEW)
│   │   │   │   ├── pairsearch_scraper.py  # PairSearch (NEW)
│   │   │   │   ├── pdf_scraper.py     # Generic PDF document scraper (NEW)
│   │   │   │   └── orchestrator.py    # Scraper scheduling & management
│   │   │   ├── analysis/
│   │   │   │   ├── change_detector.py # Detect regulatory changes
│   │   │   │   ├── impact_analyzer.py # Analyse impact on clients by sector
│   │   │   │   ├── severity_scorer.py # Severity classification
│   │   │   │   ├── early_warning.py   # Parliamentary signal analysis (NEW)
│   │   │   │   └── diff_engine.py     # Text diffing with annotations
│   │   │   ├── ai/
│   │   │   │   ├── openrouter_client.py  # OpenRouter API client (NEW)
│   │   │   │   ├── llm_cache.py       # Response caching layer (NEW)
│   │   │   │   ├── model_router.py    # Tiered model routing (NEW)
│   │   │   │   ├── embeddings.py      # Embedding generation
│   │   │   │   ├── chat_agent.py      # LangGraph chatbot agent
│   │   │   │   ├── tools.py           # Agent tools (graph query, search, etc.)
│   │   │   │   ├── prompts.py         # Prompt templates (token-optimised)
│   │   │   │   └── guardrails.py      # Output validation + privacy filter
│   │   │   ├── graph/
│   │   │   │   ├── knowledge_graph.py # Neo4j operations
│   │   │   │   └── queries.py         # Cypher query templates
│   │   │   └── notifications/
│   │   │       └── in_app.py          # In-app notifications
│   │   ├── tasks/                     # Celery tasks
│   │   │   ├── scraping_tasks.py
│   │   │   ├── analysis_tasks.py
│   │   │   ├── parliamentary_tasks.py # Parliamentary monitoring tasks (NEW)
│   │   │   └── cache_tasks.py         # Cache maintenance tasks (NEW)
│   │   └── utils/
│   │       ├── pdf_parser.py          # Multi-strategy PDF extraction
│   │       ├── text_processing.py
│   │       ├── legal_reference_parser.py
│   │       └── token_counter.py       # Token counting utility (NEW)
│   ├── tests/
│   │   ├── test_scrapers/
│   │   ├── test_analysis/
│   │   ├── test_api/
│   │   ├── test_chat/
│   │   └── test_auth/
│   ├── alembic/                       # Database migrations
│   │   └── versions/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── celeryconfig.py
│
├── docker-compose.yml                 # On-premise deployment (MVP)
├── docker-compose.prod.yml            # Production-ready configuration
├── .env.example                       # Environment variable template
│                                      # (incl. OPENROUTER_API_KEY)
├── .github/
│   └── workflows/
│       └── ci.yml                     # CI pipeline (tests + lint)
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── user-guide.md
│   ├── deployment.md                  # On-premise Docker deployment guide
│   └── openrouter-setup.md           # OpenRouter configuration guide
├── IMPLEMENTATION_PLAN.md             # This document
└── README.md
```

---

## 16. Docker Compose Configuration (On-Premise MVP)

```yaml
# docker-compose.yml — On-Premise MVP Deployment
version: "3.9"

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8001
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://regulasense:${DB_PASSWORD}@postgres:5432/regulasense
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - REDIS_URL=redis://redis:6379/0
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
      - JWT_SECRET=${JWT_SECRET}
      - JWT_EXPIRY_HOURS=24
    depends_on:
      - postgres
      - neo4j
      - redis
    volumes:
      - scraped_docs:/app/data/scraped

  celery_worker:
    build: ./backend
    command: celery -A app.tasks worker -l info -c 4
    environment:
      - DATABASE_URL=postgresql://regulasense:${DB_PASSWORD}@postgres:5432/regulasense
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - REDIS_URL=redis://redis:6379/0
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
    depends_on:
      - postgres
      - neo4j
      - redis
    volumes:
      - scraped_docs:/app/data/scraped

  celery_beat:
    build: ./backend
    command: celery -A app.tasks beat -l info
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=regulasense
      - POSTGRES_USER=regulasense
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data

  neo4j:
    image: neo4j:5
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  pg_data:
  neo4j_data:
  scraped_docs:
```

---

## 17. Key Risk Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Scraper breakage** (source website changes layout) | High | Medium | Multiple fallback strategies per source; automated health checks; alert on consecutive failures; PDF scraping as universal fallback |
| **LLM hallucination** (fabricated legal provisions) | Medium | Critical | Citation-mandatory responses; validation against database; legal-specific guardrails; human review for Severity 1 items |
| **OpenRouter downtime** | Low | High | Response caching reduces dependency; graceful degradation (show cached results); retry with exponential backoff |
| **Token cost overrun** | Medium | Medium | Tiered model routing; aggressive caching; token budget alerts; monthly cost monitoring dashboard |
| **False positive impacts** (flagging unaffected clients) | Medium | Low | Sector-based filtering; confidence scoring; human review workflow; feedback loop to improve accuracy |
| **False negative impacts** (missing affected clients) | Low | Critical | Dual detection (graph traversal + semantic search); periodic manual audit; completeness metrics |
| **Parliamentary signal inaccuracy** (Bill changes before enactment) | Medium | Medium | Clear "EARLY WARNING" labelling; confidence levels; auto-update as Bill progresses; track amendments during committee stage |
| **PDF extraction failures** (scanned/image PDFs) | Medium | Medium | Multi-strategy extraction (text → table → OCR); manual upload fallback; extraction quality scoring |
| **Stale data** (scraper misses an update) | Low | High | Multi-source cross-referencing; daily reconciliation checks; manual override capability |
| **Performance degradation** (as data grows) | Medium | Medium | Pagination, caching (Redis), database indexing, embedding index optimisation, archival policy |

---

## 18. Success Metrics

| Metric | Target | Measurement |
|---|---|---|
| **Change Detection Latency** | < 6 hours from gazette publication | Time between gazette publication and system detection |
| **Parliamentary Signal Latency** | < 24 hours from Hansard publication | Time between Hansard release and early warning generation |
| **Client Impact Accuracy** | > 85% precision (correct sector mapping) | Validated against manual lawyer review (quarterly audit) |
| **Severity Classification Accuracy** | > 85% agreement with lawyer assessment | Compared against senior lawyer re-classification |
| **Chatbot Response Accuracy** | > 90% factually correct (with citations) | Evaluated by legal review panel |
| **Token Cost Efficiency** | < $50/month for 50-client firm | Monthly OpenRouter billing vs. query volume |
| **Mean Time to Client Notification** | 50% reduction vs. pre-system baseline | From detection to all Severity 1 client notifications sent |
| **Client Coverage** | > 95% of active clients registered with sector tags | Count of registered vs. total active clients |
| **User Adoption** | > 80% of lawyers actively using the system weekly | Weekly active users / total lawyer headcount |
| **PDF Extraction Success Rate** | > 90% of PDFs extracted without manual intervention | Auto-extracted vs. total PDFs processed |

---

## 19. Verification Plan

### Automated Tests

```bash
# Backend unit tests
cd backend && pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend && npm run test

# Integration tests (requires Docker Compose stack)
docker-compose up -d
pytest tests/integration/ -v

# Scraper health checks (all sources including Parliament + PairSearch)
python -m app.services.scraper.orchestrator --health-check

# LLM response validation (via OpenRouter)
pytest tests/test_chat/test_guardrails.py -v

# Auth tests
pytest tests/test_auth/ -v

# PDF extraction tests
pytest tests/test_scrapers/test_pdf_scraper.py -v
```

### Manual Verification

1. **Scraper Accuracy**: Compare scraped data against SSO website for 20 randomly selected instruments
2. **Parliamentary Scraper**: Verify 10 Hansard entries are correctly parsed and linked to target Acts
3. **PDF Extraction**: Test with 20 PDFs of varying quality (text, table-heavy, scanned) from MAS, PDPC, ACRA
4. **Client-Sector Mapping**: Register 10 test clients with sector tags; trigger 5 known amendments; verify correct client alerts
5. **Severity Scoring**: Have 3 lawyers independently classify 20 amendments; compare against system scores
6. **Chatbot Quality**: Run 30 predefined legal questions through the chatbot; evaluate responses with a legal review panel
7. **Diff Viewer**: Verify 10 legislative diffs against official gazette records
8. **End-to-End Flow**: Simulate a new gazette publication → system detects → analyses impact → identifies affected clients by sector → alerts appropriate lawyers → chatbot can answer questions about it
9. **Parliamentary Early Warning Flow**: Simulate a Bill at Second Reading → system generates early warning → identifies affected sectors and clients → dashboard shows estimated timeline
10. **Token Efficiency**: Monitor 1 week of chatbot usage; verify actual costs against projected budget
11. **Auth Flow**: Test login, token expiry, role-based access restrictions, and logout
