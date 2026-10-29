# Intended use draft for owner review — BoneScope Stage 11

**Status: PROPOSED / NOT LOCKED / NOT APPROVED.** This draft consolidates the repository's documented behavior to help the project owner and qualified reviewers make a decision. It is not an intended-use determination, regulatory classification, clinical authorization, or substitute for signatures. Until accepted and signed, G1 remains OPEN and downstream gates remain dependent on unresolved scope.

**Draft date:** 29 October 2026  
**Evidence basis:** `xray_api.py`, `rag/retrieval.py`, `case_api.py`, local privacy/security review, README and launch guidance. Reconfirm against the exact release snapshot before signature.

## Proposed scope by function

| Function | Proposed purpose and users | Inputs and outputs | Proposed excluded uses / limits | Decision still required |
|---|---|---|---|---|
| X-ray classifier | Local coursework and research-methods demonstration for supervised users inspecting software behavior; not intended to inform care. | Bone X-ray image; returns ranked class labels and normalized softmax scores. | No diagnosis, screening, triage, treatment, referral, prognosis, patient-specific advice or probability claim. Scores are not calibrated for clinical use. Not validated for any patient population or clinical workflow. | Owner must decide whether to retain research/education-only scope; whether any formal research protocol or ethics review applies; exact population and image-use conditions. |
| Text RAG retrieval | Local research demonstration over a frozen, curated text corpus; returns candidate passages/sources or `insufficient_evidence` / `out_of_scope`. | Text query only; passages and source metadata. | Does not accept or interpret images; no generated answer API; a candidate hit does not establish support/entailment; no case-specific interpretation or care recommendation. `answer_ready=false`. | Owner must approve query audience, source update policy, permitted claims, and whether the text function is kept strictly non-clinical. |
| Case storage/API and dashboard | Local demonstration using synthetic or otherwise non-identifiable data only, pending privacy/security and data-governance approval. | Case fields can include image filename/hash, metadata, model scores, comments and corrections. | No real patient or identifiable health data; no shared host or public-network deployment; no reliance on case IDs as access control. Current review identifies missing authentication/per-user authorization, encryption-at-rest and retention/deletion controls. | System owner and privacy/security reviewers must confirm actual data flows, storage, access controls, retention and operational boundary. |
| Deployment | Single-worker local development service bound to `127.0.0.1`, only for supervised local demonstration. | Local operator actions and local files/services. | No public network, shared machine, clinical site, production use, or real-patient data until separately reviewed and approved. | Owner must confirm deployment boundary and prohibit unsupported configurations in release/runbook. |

## Observed implementation facts for owner/reviewer confirmation

These are static observations from the repository snapshot, not assertions about a running or deployed instance. Bind them to the exact release commit, model/corpus hashes and launch configuration before adopting the draft:

- **Image classifier:** `POST /predict` accepts a raster X-ray plus exactly 22 metadata fields (`age`, `gender`, 20 binary anatomy/view indicators); supported formats are JPEG/PNG/BMP/TIFF, upload limit is 30 MiB, dimensions are capped at 25 million pixels, and multi-frame images are rejected. It returns ranked scores for 10 labels, including Top-1/Top-3 and normalized softmax outputs. The API notice says these scores are not calibrated disease probabilities. The metadata schema and labels must be confirmed against the release model.
- **Image and prediction lifecycle:** image bytes are written to a temporary directory for inference; the API response includes an image SHA-256 and opaque prediction ID. A prediction record is held in process memory for at most 10 minutes. Saving is a separate `/cases` action; the SQLite record stores the validated metadata, scores, hash, model hash and generic uploaded filename, not image pixels. The source/UI workflow offers history, comments and corrections. Confirm temp-volume behavior, exact DB path, retention, backups and deletion at runtime.
- **Text retrieval:** the repository has a local text-only RAG retrieval pipeline; current UI has no chatbot and does not combine X-ray pixels with RAG. Retrieval returns candidate passages/source metadata or an abstention/out-of-scope state; current code sets `answer_ready=false`. A candidate is not a verified answer or clinical recommendation.
- **Supported launch boundary:** the documented launcher binds to `127.0.0.1` with one worker. This is a launch instruction, not an enforcement boundary in every possible invocation; direct Uvicorn/configuration changes could expose routes. Case endpoints have no per-user authentication/authorization in the reviewed router. Keep synthetic/non-identifiable data only until a qualified privacy/security reviewer approves the actual runtime and threat model.

**Owner decision still required:** confirm whether all four functions above are in scope, who may use each, whether the 22-field metadata may contain real subject information, whether persistent case history is part of the allowed demo, and which launch modes are permitted. If the intended scope excludes storage or metadata use, remove or disable those functions in the release and verify that change before signing G1.

## Shared draft limits

- No clinical benefit, diagnostic accuracy, safety, generalization, calibration, or regulatory-compliance claim is authorized by this draft.
- Stage 11 dev results are in-sample and/or agent-authored; they do not establish independent validity. The image checkpoint's training/split provenance remains insufficient for independent BTXRD evaluation.
- Do not combine the classifier, text retrieval and case storage into one broad intended-use statement; evaluate each function and any integrated workflow separately.
- Changes to users, claims, input/output, population, market, hosting, data handling, or model/corpus version require owner review and gate impact assessment.

## Questions the owner and reviewers must resolve

1. Is this strictly an educational/research software demonstration, and what exact activities are allowed?
2. Which user groups, population, jurisdictions, deployment, and data types are permitted?
3. Are classifier output labels visible to end users, and under what labeling/caveat controls?
4. Is any research involving human subjects, identifiable data, or institutional data planned, requiring separate ethics/data approval?
5. Who is accountable for release control, incidents, source/model updates, retention, and withdrawal?
6. Which regulatory, privacy, security and safety reviewers are qualified for each intended market and function?

## Required sign-off before G1 can close

| Role | Confirmation | Name / qualification | Signature reference | UTC date |
|---|---|---|---|---|
| Project/product owner | Accept or revise each function, user, claim, exclusions and deployment boundary |  |  |  |
| Qualified regulatory reviewer | Comment on stated functions and named jurisdictions only |  |  |  |
| Privacy/data-governance reviewer | Confirm proposed data types, flow and storage boundary |  |  |  |
| Clinical safety lead, if scope may affect care | Confirm hazard/oversight implications |  |  |  |

Until those decisions are documented, intended use is **not locked**, the register stays **G1 OPEN**, and `answer_ready=false`.

**Evidence links:** [intended-use lock template](STAGE11_INTENDED_USE_LOCK_TEMPLATE_VI.md) · [local privacy/security review](STAGE11_LOCAL_PRIVACY_SECURITY_REVIEW_20261029.md) · [regulatory applicability review](STAGE11_REGULATORY_APPLICABILITY_REVIEW_VI.md) · [acceptance gate status register](stage11_acceptance_gate_status_20261029.csv).
