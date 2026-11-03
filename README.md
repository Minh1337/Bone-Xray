# BoneScope

> Local research studio for educational bone X-ray experiments, metadata-aware image classification, and provenance-aware retrieval-augmented exploration.

[![Status: educational prototype](https://img.shields.io/badge/status-educational%20prototype-21695c)](#scope-and-safety)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4)](#requirements)

BoneScope combines a local deep-learning inference pipeline with a local RAG research studio. The integrated demo lets a user upload an educational X-ray case, enter the required metadata, inspect Top-3 model outputs, and ask follow-up questions against a provenance-tracked document collection.

The project is intentionally scoped as an **educational and experimental report**. It is not a medical device, diagnostic service, clinical decision-support system, or patient-facing application.

## Highlights

- **Metadata-aware X-ray inference** using a Swin-based classifier with metadata processing and cross-attention.
- **22-field case workflow** with image validation, metadata validation, review-before-run, and explicit confirmation.
- **Local Research Studio** with responsive light/dark UI, mobile navigation, accessible dialogs, retry/stop controls, and Markdown export.
- **Multi-turn conversation** with recent context, document-only mode, source citations (`[S1]`, `[S2]`), and conservative out-of-scope handling.
- **RAG retrieval and provenance** with source metadata, licenses, chunk identifiers, corpus/index audits, deterministic replay, and evaluation reports.
- **Privacy-conscious architecture**: image and case metadata stay in the local inference service; the optional LLM provider receives only the data described in the project documentation.
- **Fail-closed readiness state**: generated content remains marked `answer_ready=false`; acceptance gates are not silently closed.

## Screenshots

The latest UI exploration images are stored in [`.stitch/designs/`](.stitch/designs/). They are design references, not claims of clinical performance.

## Architecture

```text
Educational X-ray + 22 metadata fields
                 │
                 ▼
       Local validation and inference
       Swin + metadata cross-attention
                 │
                 ▼
          Top-3 labels and scores
                 │
                 ▼
     Transparent label-to-topic mapping
                 │
                 ▼
  Local RAG retrieval + optional draft generation
                 │
                 ▼
     Cited passages, limitations, and abstention
```

### Main components

| Area | Entry points |
| --- | --- |
| X-ray API and local UI | [`xray_api.py`](xray_api.py), [`xray_ui.py`](xray_ui.py) |
| Model definition and inference | [`model_definition.py`](model_definition.py), [`inference.py`](inference.py) |
| Case validation and storage | [`case_api.py`](case_api.py), [`database.py`](database.py) |
| RAG retrieval and policy | [`rag/retrieval.py`](rag/retrieval.py), [`rag/policy.py`](rag/policy.py) |
| Conversation and generation | [`rag/conversation.py`](rag/conversation.py), [`rag/generation.py`](rag/generation.py) |
| Integrated chatbot API | [`rag/demo_api.py`](rag/demo_api.py) |
| Research Studio frontend | [`rag/demo_web/`](rag/demo_web/) |
| Evaluation and audit tools | [`tools/`](tools/), [`rag/audit.py`](rag/audit.py) |

## Requirements

- Windows 10/11
- Python 3.11, 64-bit
- Git
- NVIDIA GPU with a compatible CUDA/PyTorch installation is recommended; CPU mode is supported but slower
- Optional: Groq or OpenAI API credentials for draft generation

The repository includes local model/runtime assets needed for the current prototype. Do not commit additional datasets, patient data, runtime databases, logs, API keys, or generated caches.

## Quick start

### 1. Create the environment

From PowerShell:

```powershell
git clone https://github.com/Minh1337/Bone-Xray.git
cd Bone-Xray

.\01_setup.bat
.\04_setup_api.bat
```

The setup scripts create `.venv` and install the model/API dependencies. To set up the RAG environment separately:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_rag.txt
```

### 2. Run the X-ray application

```powershell
.\07_start_ui.bat
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 3. Run the integrated Research Studio

```powershell
.\.venv\Scripts\python.exe -m uvicorn rag.demo_api:app --host 127.0.0.1 --port 8765
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/).

Do not open `rag/demo_web/index.html` directly: the frontend is served by the FastAPI application and requires the local API routes.

### 4. Optional LLM configuration

Create a local `.env` from [`.env.example`](.env.example):

```powershell
Copy-Item .env.example .env
```

Then configure the provider on your machine:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=replace-with-a-local-secret
```

OpenAI is also supported through `LLM_PROVIDER=openai`. Never commit `.env` or paste credentials into issues, pull requests, screenshots, or logs.

## RAG index setup

The current retrieval bundle contains 22 provenance-tracked sources and 794 chunks. Build or refresh local retrieval assets with:

```powershell
.\.venv\Scripts\python.exe rag\build_index.py --download-model
.\.venv\Scripts\python.exe -m rag.audit --report-dir docs\reference\local_audit
.\.venv\Scripts\python.exe rag\evaluate.py
```

The generated `rag/index/`, `rag/models/`, and `rag/source_cache/` directories are local runtime assets and are ignored by Git. Audit success means artifact integrity and provenance checks passed; it does not establish medical validity or clinical safety.

## Validation

Run the complete regression suite:

```powershell
.\.venv\Scripts\python.exe -m pytest api_tests rag/tests tests ui_tests -q
```

The latest integrated verification recorded:

- 162 tests passed
- 132 subtests passed
- provenance audit: `PASS`
- deterministic replay: `16/16 PASS`
- JavaScript syntax check: `PASS`
- `answer_ready=false`
- acceptance gates G1–G7 remain `OPEN`

See the [integrated verification record](docs/reference/stage12_integrated_chatbot_verification_20261103.json) and the [latest UI checkpoint](checkpoints/20261103_stage12_ui_completion/manifest.json) for reproducibility details.

## Scope and safety

BoneScope is for **local educational experimentation only**.

- Do not use it to diagnose, triage, monitor, or treat a person.
- Do not upload real patient data or personally identifiable information.
- Model scores are not calibrated probabilities and are not clinical confidence.
- The BTXRD measurements in this repository are in-source development/reference experiments, not independent external validation.
- RAG passages are retrieval candidates; citations do not automatically prove that a generated claim is entailed.
- The prototype deliberately keeps `answer_ready=false` and does not claim clinical acceptance.

Read the [Vietnamese project guide](README_VI.md), [chatbot readiness notes](docs/reference/STAGE11_CHATBOT_READINESS_VI.md), and [handoff record](START_HERE_NEXT_CODEX_VI.md) before extending the system.

## Repository layout

```text
BONESCOPE/
├── rag/                 # Retrieval, policy, conversation, API, and Research Studio
├── model/               # Local model weights and configuration
├── xray_web/            # X-ray application frontend
├── docs/                # Guides, reports, provenance, and verification records
├── api_tests/           # API and case-management tests
├── rag/tests/           # Retrieval, conversation, and chatbot tests
├── tests/               # End-to-end and model evaluation tests
├── ui_tests/            # UI route tests
├── tools/               # Evaluation and checkpoint utilities
├── xray_api.py          # X-ray FastAPI service
├── xray_ui.py           # X-ray UI entry point
└── rag/demo_api.py      # Research Studio FastAPI service
```

## Contributing

This repository is maintained as an experimental learning project. Before opening a change:

1. Keep changes local, reproducible, and narrowly scoped.
2. Do not add secrets, patient data, or unlicensed source material.
3. Preserve provenance and update directly related documentation.
4. Run the focused tests and the full regression suite when behavior crosses components.
5. Do not change `answer_ready`, acceptance-gate status, or evaluation claims without the corresponding evidence and review record.

For detailed Vietnamese instructions, see [`README_VI.md`](README_VI.md).

## License and data provenance

Review the provenance and license metadata for every source before redistributing corpus text, images, model weights, or generated artifacts. Repository documentation records the current source-screening decisions; those records are not a substitute for checking upstream terms at the time of use.
