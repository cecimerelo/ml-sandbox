# PRD Addendum — TFM

Material that informed the PRD but belongs in downstream documents (architecture, thesis literature review, UX spec).

---

## Research Bibliography

14 sources on algorithm selection and meta-learning were identified during PRD discovery. All are marked `[FOUND]` — located via web search, not deeply read. Ceci intends to read them independently.

Full bibliography: see `research-bibliography.md` in this workspace.

**Priority reading order:**
1. Rivolli et al. 2022 — most comprehensive meta-features survey
2. AMLBID 2022 — named upper-bound baseline in the thesis proposal
3. Sklearn flowchart + Azure ML cheat sheet — directly comparable tools
4. Rice 1976 — foundational theoretical framing

---

## Rejected Alternatives

**Step-by-step wizard vs. dashboard layout**
An early design considered a step-by-step guided flow (EDA → Recommendation → Results → Compare). Rejected in favour of a single-page dashboard with collapsible EDA section — gives users more control and feels more like a playground than a tutorial.

**Live reactive updates vs. button-triggered**
Considered updating the dashboard on every form change (live mode). Rejected — model training is too expensive to trigger on every input change. "Get Recommendation" button chosen instead.

**Client-side ML vs. backend ML**
Briefly considered running model training in the browser (WebAssembly / ONNX). Rejected — training 20 supervised methods on a real dataset with cross-validation exceeds what's practical client-side. Backend handles all ML inference.

---

## Architecture Notes (for downstream architecture doc)

- Backend needed for: in-memory dataset processing, ML training/inference, benchmark model serving, permanent storage of anonymized decision records and feedback
- Dataset never written to persistent storage — processed in memory only
- Tech stack decision deferred (Frontend: React/Vue/Streamlit? Backend: FastAPI/Flask?) — open question in PRD
- Benchmark re-run cadence: open question — fixed at thesis submission or periodic?
