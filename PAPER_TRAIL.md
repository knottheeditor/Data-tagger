# 📝 Data Forager: Paper Trail

**Latest Session**: 2026-02-18

---

## 🏆 Session Wins — Feb 18

- **Export Pipeline Standardization**: 
  - Standardized all dates to dashes (`-`) for legacy compatibility.
  - Enforced all-caps asset prefixes (`TRAILER_`, `THUMBNAIL_`).
  - Corrected metadata templates to include file extensions and exact field formats.
- **Aspect Ratio Precision**: Implemented triple-auto-probing for Movie, Trailer, and Thumbnail to ensure 1:1 metadata accuracy.
- **Custom Addons Subsystem**: Added UI and backend to link multiple "Extra" files (VODs, Tweets) to any scene with standardized naming (`ADDON_...`).
- **Heavy-VOD Optimization (v1)**: Increased probe timeouts (300s-600s) and added high-density headers to stop hangs on large stream files.
- **New Pod Deployment**: Streamlined pod configuration and resolved FFmpeg binary path issues on pod `hs5yr4u67hocfi`.

---

## 🏆 Session Wins — Feb 17

- **Recursive Scanning Fix**: Enabled `os.walk` to find all videos in subdirectories.
- **Path-Link Recovery**: Fixed path mismatch where local files were hidden by "remote" (do:) ghost records.
- **Narrative Logic Restoration**:
  - Fixed "Posing" deletion bug; restored "The video begins with teasing..." openers.
  - Implemented **Toy Counter Context Injection**: The AI now receives a validated "hint" about the unique toy count for natural integration.
- **Console Hardening**: Suppressed high-volume FFmpeg corruption logs to keep the terminal readable.
- **UI Cleanup**: Removed unneeded Intensity Score field.

- **The Great Description War (v1 → v4)**:
  - **v1**: "Forensic Auditor" persona prompt → AI still described rooms and costumes.
  - **v2**: "Sentence Killer" code filter → Killed everything, generic fallback only.
  - **v3**: Structured fill-in-the-blank (ACTION_VERB/BODY_PART/TOOL_USED) → Eliminated prose, but model hallucinated wrong tools.
  - **v4**: Code-built sequential descriptions → Python assembles narratives from parsed fields. No more AI prose.
- **Frame Extraction Overhaul**:
  - 12 → 24 frames (6 burst clusters), 896px → 1280px, 2x brightness/contrast boost.
- **Visual Toy Lexicon**:
  - Structural markers for Wand, Dildo, Drilldo, Estim, Fucking Machine in `lexicon.py`.
- **Banned Words System**:
  - 60+ keywords auto-delete entire sentences (bathroom, catgirl, slime, costume, mirror, etc.)

## 🏆 Session Wins — Feb 12

- **Mechanical Sensor Protocol**: Stripped the AI of narrative fluff; enforced strict bulleted frame-range reporting.
- **The Lexicon Audit**: Created a forensic `TAG_LEXICON.py` with technical markers (e.g., "metallic glint" for restraints).
- **True Multi-Pass Architecture**: Split analysis into three isolated steps: **Vision Ingestion**, **Forensic Judge**, and **Metadata Editor**.
- **Multi-Model Orchestration**: Paired `gemma3` (vision) with `qwen2.5` (reasoning judge).
- **Critical Pod Recovery**: Resolved 100% full root FS by migrating Ollama data to `/workspace` mount.

## 🧱 Hard Blocks

- **Model Capability Ceiling**: Gemma 3 Heretic 12B cannot reliably distinguish between adult toy types (wand vs dildo vs drilldo). This is the primary accuracy bottleneck.
- **Fix Path**: Evaluate alternative models (LLaVA-Next, Qwen-VL, InternVL2) or create a fine-tuning dataset.

## 💡 Key Learnings

- **Don't let AI write prose**: Code-assembled descriptions from structured fields eliminate 100% of environmental fluff.
- **Fewer tool choices = fewer hallucinations**: Removing exotic options (Estim, Fucking Machine) from the prompt reduced misidentification.
- **The "Sentence Killer" works, but it's a blunt instrument**: Better to prevent bad output than to filter it after the fact.
- **Always version-stamp your code**: Adding `VLM_CODE_VERSION` print on import saved hours of debugging stale-code issues.

## 🚀 Momentum & Next Steps

- **Status**: Pipeline architecture solid. Model accuracy is the bottleneck.
- **Next**: Model evaluation sprint + fine-tuning dataset preparation.
- **ETA to production**: Feb 28, 2026.

---

*Updated by Antigravity — Feb 14, 2026* 🌌
