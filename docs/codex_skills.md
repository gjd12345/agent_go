# Codex Skills For agent_go

This repository includes project-local skills under `codex_skills/`.
Install them after cloning so Codex can route TOCC research, PPT, diagram, and pseudocode tasks consistently.

## Install

From the repository root:

```bash
bash scripts/install_codex_skills.sh
```

Then restart Codex so newly installed skills are loaded.

Use force mode to overwrite older local copies:

```bash
bash scripts/install_codex_skills.sh --force
```

## Project-local skills

| Skill | Purpose |
|---|---|
| `tocc-research-workflow` | TOCC experiments, traces, card selection, reports, best-code records |
| `tocc-presentation` | PPT/deck planning, draw.io architecture diagrams, code-evolution visuals |
| `tocc-pseudocode` | Paper-ready pseudocode for TOCC, RAG context construction, card synthesis |

## External / bundled skills used by this project

These are not vendored in the repository because they are maintained outside this project:

| Skill | Source | Notes |
|---|---|---|
| `algo-reconstruct` | `HuiyuLi-2000/gen-pseudocode-skill` | Used for polished LaTeX pseudocode generation |
| `drawio` | local/company skill registry or existing Codex skill install | Used for editable architecture diagrams and exported PNG/SVG |
| `presentations:Presentations` | Codex bundled plugin | Used for editable PPTX creation and QA |
| `imagegen` | Codex system skill/tool | Optional raster polish for deck visuals |

The install script attempts to install `algo-reconstruct` from GitHub when the system `skill-installer` is available.
For `drawio` and `presentations`, install/enable them through the local Codex skill or plugin registry used by your environment.

## Expected post-clone setup

1. Clone the repository.
2. Install Python dependencies: `python3 -m pip install -r requirements.txt`.
3. Install project skills: `bash scripts/install_codex_skills.sh`.
4. Restart Codex.
5. Verify the repository:

```bash
PYTHONPATH=. python3 -m pytest tests -q
python3 -m compileall -q eoh_go
go build -o /tmp/eoh_go_mainbin .
```
