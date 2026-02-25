# Project Context: 08_Utlity_Datatagger_Organizer

## Cold Zone — Stable Knowledge

### Overview
FastAPI-based video tagging and organization backend. Manages video metadata enrichment via VLM (Vision Language Model), intensity scoring, trailer generation, and cloud worker orchestration. Targets DigitalOcean GPU droplets for cloud processing.

### Architecture
- `main.py` — FastAPI entry point, API routes
- `src/worker/` — Cloud worker subsystem (SSH probing, RunPod fallback)
- `src/vlm/` — Vision Language Model integration for video tagging
- `src/db/` — SQLite database operations
- `src/gui/` — GUI components (gui_v2.py is current)
- `VideoUtils.get_duration` — Video metadata extraction
- Data flow: Videos → VLM tagging → Intensity scoring → Auto-trailer generation → Organized output

### Key Files
- `main.py` — FastAPI app, all API endpoints
- `config.json` — Local config (runpod_api_key, video paths, addon paths, digitalocean_droplet_ip)
- `gui_v2.py` — Current GUI implementation (replaced legacy UI)
- `deep_scan.py` — Initial video discovery
- `intensity.py` — VLM intensity scoring logic
- `fix_trailers.py` — Auto-trailer generation (1:1 crop based on VLM score)
- `find_video.py` — Video lookup utilities
- `debug_db.py` — Database debugging utilities

### Decisions & Patterns
- VLM-based tagging with intensity scores (0-10 scale)
- **Manual field preservation**: VLM text generation no longer overwrites manually input fields
- Quick Toy Selector: Predefined toy list with "massage gun"
- System status indicators: Green light for droplet, boot info display
- **Droplet migration**: Moving from RunPod to persistent DigitalOcean H100/A100 GPU droplet (manual creation required via DO dashboard, SSH key: `C:/Users/nicho/.ssh/id_ed25519.pub`)
- **Planning mode active**: Model selection in progress (Gemini 3.1 Pro High, Claude Sonnet 4.6 Thinking)

### Gotchas
- 🟢 **UI Revert Bug FIXED** — VLM text generation no longer resets manual fields
- 🟢 **Quick Toy Selector FIXED** — Removed popup, added massage gun
- 🟢 **Re-judge Button FIXED** — Working properly
- 🟢 **Auto-Trailer Generation FIXED** — 1:1 crop using VLM Intensity Score
- 🟡 **Pending: Lazy Enrichment** — Add trigger in `gui_v2.py` preview pane for `pending_meta` files, fetch tags dynamically from UI instead of bulk scanning
- 🟡 **Pending: Remote SSH Probing** — `VideoUtils.get_duration` needs correct SSH probe execution for cloud clips
- 🟡 **Pending: Bulk Addon Exporting** — Test deployment with attached addon to ensure copy routines are solid

## Hot Zone — Current State

### Active State
- **Agent status**: idle
- **Current branch**: unknown (not provided)
- **Errors: 0 | Warnings: 0**
- **Open tabs: 0**
- User in **Planning mode** — actively selecting model from options: **Gemini 3.1 Pro (High/Low)**, **Claude Sonnet 4.6 (Thinking)**, **Claude Opus 4.6 (Thinking)**, **GPT-OSS 120B (Medium)**
- Planning conversation active (Session 5 priorities)

### Recent Work
- [Today] Fix Re-judge Button — Complete
- [Today] Fix UI Revert Bug — Complete (VLM preserves manual inputs)
- [Today] Fix Quick Toy Selector — Complete (removed popup, added massage gun)
- [Today] Add System Status Indicators — Complete (green light, boot info)
- [Today] Implement Auto-Trailer Generation — Complete (1:1 crop using VLM Intensity Score)

### Pending Tasks (from brain artifacts)
- **Implement Lazy Enrichment**:
  - [ ] Add trigger in `gui_v2.py` preview pane for `pending_meta` files
  - [ ] Fetch tags dynamically from UI instead of bulk scanning
- **Stress-Test Remote SSH Probing**:
  - [ ] Update `VideoUtils.get_duration` to handle correct SSH probe execution for cloud clips
- **Verify Bulk Addon Exporting**:
  - [ ] Test deployment with an attached addon to ensure copy routines are solid

### Recent File Activity
- [~] `.agents\context_summary.md` — Modified
- [~] `.gravity\context-cache.md` — Modified (×9)

## Meta
- **Last distilled**: 2025-01-09 12:30:00
- **Signals received**: 6
- **Delta: No changes required** — All 6 signals confirm existing state. Session 5 fixes remain verified complete. Planning mode ongoing with unchanged model options. Pending tasks identical. Agent status idle. No errors, warnings, or file changes requiring cache updates. Cold Zone stable, Hot Zone unchanged.
- Sections never populated: None