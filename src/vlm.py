import requests
import json
import base64
import os
import re
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.lexicon import TAG_LEXICON

VLM_CODE_VERSION = "v5.2-debug-trace"  # Change detection stamp
print(f"[VLM] Code loaded: {VLM_CODE_VERSION}")

# Structured tag taxonomy for adult content cataloging
TAG_TAXONOMY = {
    "subject": ["solo", "duo", "trio", "group", "pov", "self-shot"],
    "acts": [
        "masturbation", "oral", "penetration", "anal", "riding",
        "footjob", "facesitting", "grinding", "joi", "deepthroat",
        "fingering", "squirting", "scissoring",
        "teasing"
    ],
    "fetish_kink": [
        "bdsm", "bondage", "domination", "submission", "humiliation", "edging",
        "forced-orgasm", "overstimulation", "denial", "cbt", "cnc", "hucow",
        "pet-play", "puppy-play", "predicament", "electro-play", "wax-play",
        "choking", "spanking", "degradation", "worship", "femdom", "rope"
    ],
    "setting_mood": [
        "bedroom", "dungeon", "outdoor", "shower", "pov-camera", "dark-aesthetic",
        "neon", "rave", "christmas", "halloween", "easter", "romantic", "rough"
    ],
    "outfit_body": [
        "lingerie", "stockings", "latex", "harness", "skirt", "nude", "topless",
        "bikini", "bodysuit", "fishnets", "thigh-highs", "corset", "choker"
    ]
}

# Toys/gear are MANUAL ONLY — the AI should NOT guess these
MANUAL_TAGS = [
    "dildo", "vibrator", "wand", "drilldo", "estim", "fucking-machine", "butt-plug",
    "strap-on", "cage", "restraints", "collar", "leash", "gag", "clamps",
    "one-bar-prison", "grinder", "suction-toy", "anal-beads"
]

# Only AI-detectable tags go to the model
ALL_TAGS = []
for cat_tags in TAG_TAXONOMY.values():
    ALL_TAGS.extend(cat_tags)

# Cosplay tags (AI can try to detect costumes — kept separate for clarity)
COSPLAY_TAGS = [
    "cosplay", "frieren", "harley-quinn", "jinx", "shadowheart", "miku",
    "zelda", "marcille", "pikachu", "sonico", "ramona", "anby", "ubel",
    "succubus", "vampire", "elf", "maid", "bunny-girl", "catgirl",
    "nurse", "schoolgirl", "goth"
]
ALL_TAGS.extend(COSPLAY_TAGS)

SYSTEM_PROMPT = (
    "You describe adult video content factually for a professional catalog. "
    "IMPORTANT: All performers in these videos are FEMALE. There are NO men. "
    "Never mention cock, penis, or any male body parts. Never use 'he' or 'his'. "
    "You describe ONLY what is physically happening: sexual acts, body parts being touched, and what is touching them. "
    "You use porn vocabulary: pussy, tits, ass, clit. "
    "You NEVER describe rooms, lighting, hair, outfits, or camera angles. "
    "You NEVER write fiction or feelings. You NEVER use words like: moaning, arching, begging, throbbing, ecstasy. "
    "You describe ONLY what a viewer would SEE happening physically."
)

# Synthesis system prompt
SYNTHESIS_SYSTEM = (
    "You write factual video descriptions for a porn website. "
    "You describe what HAPPENS in the video like a product listing. "
    "You say what acts occur, what body parts are involved, and what toys are used. "
    "You NEVER write fiction, fantasy, or what someone 'feels'. "
    "You NEVER use words like: moaning, arching, begging, throbbing, pulsing, craving, aching. "
    "You describe ONLY what a viewer would SEE. "
    "You NEVER start with 'Here is' or 'Based on'."
)

# PASS 1: Natural language burst description (4 frames per call)
VISION_BURST_PROMPT = (
    "Look at these frames from an adult video. ALL performers are FEMALE — there are NO men.\n\n"
    "In 1-2 sentences, describe what SEXUAL ACTIVITY is happening.\n\n"
    "You MUST include:\n"
    "- How many women are visible (1, 2, or 3+)\n"
    "- What sexual act is happening (teasing, masturbation, oral, fingering, toy play, anal, etc.)\n"
    "- What body parts are involved and what is touching them\n"
    "- If a toy is being used, mention it\n"
    "- If you see SQUIRTING (visible liquid spraying or gushing from the vagina), you MUST mention it explicitly and score it INTENSITY: 10/10.\n"
    "- At the very end of your description, you MUST include 'INTENSITY: X/10' where X is a score from 1-10 (1=teasing, 5=fingering/oral, 8=hardcore toy penetration, 10=squirting/orgasm with visible liquid).\n\n"
    "COUNTING PEOPLE — COUNT CAREFULLY (CRITICAL STEP):\n"
    "- 1. First, scan the image for FACES. Counting distinct faces is the most reliable way to count people.\n"
    "- 2. Next, look for distinct torsos and limbs. This catches people whose faces are hidden.\n"
    "- 3. Look closely for extra hands or limbs. If someone else's body parts are in the frame, count them!\n"
    "- Reflections in mirrors or shiny surfaces are NOT a separate person.\n"
    "- If you count 1 person, say 'Solo'. If exactly 2 people, say 'Duo'. If exactly 3 people, say 'Trio'. If 4 or more, say 'Group'.\n"
    "- WARNING: Do NOT just say 'Duo' if you clearly see 3 distinct faces or bodies. Take your time to carefully count them all.\n\n"
    "DO NOT HALLUCINATE — STRICT RULES (READ CAREFULLY):\n"
    "- ONLY describe what you can PHYSICALLY SEE in the frames. Do NOT guess, assume, or infer.\n"
    "- If you do not CLEARLY see a body part or a sexual act, DO NOT mention it. It is better to say 'teasing' than to guess incorrectly.\n"
    "- 'Oral' means you can clearly see a MOUTH physically touching a PUSSY. If you cannot see mouth-on-pussy contact, do NOT say oral.\n"
    "- If only ONE woman is visible, she CANNOT be performing oral. Solo girls masturbate, finger, or use toys.\n"
    "- Do NOT say 'eating pussy', 'licking', or 'sucking' unless you can literally see a tongue or mouth on genitals.\n"
    "- Do NOT say 'fingering' or 'penetration' unless you clearly see fingers or a toy inside or directly on the genitals.\n"
    "- Do NOT assume what is happening off-camera or under blankets/clothing.\n"
    "- If you are unsure what act is happening, say 'teasing' or 'masturbation' — NEVER guess a more extreme act.\n\n"
    "RULES:\n"
    "- ALL performers are WOMEN. Never say 'he', 'his', 'cock', or 'penis'.\n"
    "- Use porn vocabulary: pussy, tits, ass, clit\n"
    "- Do NOT describe rooms, furniture, lighting, or outfits\n"
    "- Do NOT describe faces, hair, or body types\n"
    "- If nothing sexual is happening, say 'teasing / showing off body'\n"
    "- Be specific: 'she fingers her pussy' NOT 'she touches herself'\n\n"
    "GOOD examples:\n"
    "'Solo. She rubs her pussy with her fingers, then inserts a vibrator. INTENSITY: 7/10'\n"
    "'Duo. One girl eats the other\\'s pussy while she sits on her face. INTENSITY: 8/10'\n"
    "'Solo. Teasing — she shows off her tits and ass, no sexual contact yet. INTENSITY: 2/10'\n"
    "'Trio. Three girls take turns licking each other\\'s pussies. INTENSITY: 9/10'"
)

# PASS 2: Synthesis (combine burst descriptions into a listing)
SYNTHESIS_PROMPT_TEMPLATE = (
    "Here are descriptions of different segments of an adult video:\n\n"
    "{burst_descriptions}\n\n"
    "Write a short description for this video's listing on a porn site.\n\n"
    "Rules:\n"
    "- 1-3 sentences, under 40 words total\n"
    "- ALWAYS start the description with the exact phrase 'In this scene,' followed by the number of girls, then the action.\n"
    "- ALL performers are FEMALE. Never mention men, cock, penis, or use 'he'/'his'.\n"
    "- Describe the PROGRESSION: what happens first, then what escalates\n"
    "- Use porn vocabulary: pussy, tits, ass, clit\n"
    "- DO NOT write fiction or feelings — only describe what HAPPENS\n"
    "- DO NOT mention rooms, furniture, or settings\n"
    "- ONLY include an act if it appears in at least 2 of the segment descriptions above. If only 1 segment mentions oral, DO NOT include oral in the final description.\n"
    "- If ANY segment mentions multiple girls (Duo, Trio), the final description MUST reflect the highest number of girls. DO NOT downgrade to Solo if multiple people appear in the scene at any point.\n\n"
    "GOOD examples:\n"
    "'In this scene, one girl starts with teasing and tit play. She fingers her pussy, then fucks herself with a toy until she cums.'\n"
    "'In this scene, two girls eat each other\\'s pussies, then they scissor. Toys come out for the finish.'\n"
    "'In this scene, three girls take turns licking each other\\'s pussies and using a double-ended dildo.'\n\n"
    "Description:"
)

# PASS 3: Tag Extraction (porn-site search tags)
AUDIT_PROMPT_TEMPLATE = (
    "You are tagging a porn video for a website's search system.\n"
    "IMPORTANT: All performers are FEMALE. There are NO men in these videos.\n\n"
    "VIDEO DESCRIPTION:\n{description}\n\n"
    "AVAILABLE TAGS (pick from these ONLY):\n{taxonomy}\n\n"
    "Tag this video. Pick 4-8 tags from the list above.\n\n"
    "You MUST include:\n"
    "- At least 1 tag from: solo, duo, trio, group, pov\n"
    "- At least 1-2 tags for acts that happen (masturbation, oral, fingering, etc.)\n"
    "- Any relevant outfit or fetish tags\n\n"
    "Definitions to avoid mistakes:\n"
    "- 'masturbation' = any self-stimulation (fingers, toy, grinding)\n"
    "- 'oral' = mouth on pussy (girl-on-girl). Licking lips is NOT oral.\n"
    "- 'anal' = PENETRATION of the anus (toy only). Surface play is NOT anal.\n"
    "- 'penetration' = toy or fingers inside pussy or ass\n"
    "- 'solo' = ONE woman on screen\n"
    "- 'duo' = TWO women on screen\n"
    "- 'trio' = THREE women on screen\n"
    "- 'group' = FOUR or more women\n"
    "- 'scissoring' = two women rubbing pussies together\n\n"
    "Respond with ONLY a comma-separated list.\n\n"
    "Tags:"
)

# PASS 3: Metadata Synthesis
BANNED_WORDS = [
    "room", "indoor", "outdoor", "neon", "curtain", "background", 
    "setting", "labeled", "platform", "wall", "floor", "tub", "pool",
    "expression", "glitter", "paint", "temperature", 
    "identity", "ambient", "effect", "fabric", "lycra", "aqua-bloom",
    "costume", "outfit", "clothing", "swimsuit", "close-up", "overview", 
    "camera angle", "interacts with", "visible",
    "yardworks", "hairstyle", "bobbed", "sparkly", "interior",
    "teal-tailed", "closely", "silicone", 
    "bathroom", "proximity", "hued", "teal", "cooperative", "reflection",
    "moaning", "arching", "begging", "throbbing", "pulsing", "craving", "aching",
    "yearning", "quivering", "trembling", "writhing", "ecstasy", "undeniable",
    "breathtaking", "stunning", "unforgettable", "incredible",
    "body begging", "drove her", "drives her", "closer to the edge",
    "bonus segment",
    # Male terms — impossible in female-only content
    "cock", "penis", "dick", "balls", "his ", " he ", "blowjob", "handjob",
    "cumshot", "creampie", "titfuck", "semen", "ejacul"
]


class VLMClient:
    def __init__(self, api_url, model_name="gemma3:12b", audit_model=None, ssh_config=None):
        self.api_url = api_url.rstrip('/')
        self.model_name = model_name
        self.audit_model = audit_model or model_name
        self.ssh_config = ssh_config  # Expects {'host': str, 'port': int, 'ssh_key': str}
        self._result_cache = {} # Simple in-memory cache for the current session

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_frames(self, image_paths, prompt, system_prompt=None, model_override=None, pre_encoded_images=None):
        """Sends multiple frames to the VLM via the native Ollama API using SSH transport."""
        target_model = model_override or self.model_name
        
        images = []
        if pre_encoded_images is not None:
            images = pre_encoded_images
        else:
            for path in image_paths:
                images.append(self._encode_image(path))
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": prompt,
            "images": images if images else None
        })
        
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 16384
            }
        }
        
        # Cache Lookup: Hash the payload to simplify
        payload_hash = hashlib.md5(json.dumps(payload).encode()).hexdigest()
        if payload_hash in self._result_cache:
            print(f"DEBUG: VLM Cache Hit (Model: {target_model})", flush=True)
            return self._result_cache[payload_hash]

        try:
            # If SSH config is provided, we pipe the request directly to the pod's local port
            if self.ssh_config and self.ssh_config.get("host"):
                from subprocess import Popen, PIPE
                import traceback as _tb
                host = self.ssh_config["host"]
                port = self.ssh_config["port"]
                key = self.ssh_config["ssh_key"]
                
                # We use curl on the pod's side to talk to its local loopback
                # This bypasses the RunPod Web Proxy entirely
                ssh_cmd = [
                    "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=30",
                    "-i", key, "-p", str(port), f"root@{host}",
                    "curl -s -X POST http://127.0.0.1:11434/api/chat -d @-"
                ]
                
                payload_json = json.dumps(payload)
                print(f"DEBUG: VLM SSH Request -> {host}:{port} (Model: {target_model})", flush=True)
                print(f"DEBUG: Internal Payload size: {len(payload_json)} bytes", flush=True)
                
                # Explicitly use utf-8 to avoid charmap decode errors on Windows
                proc = Popen(ssh_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True, encoding='utf-8')
                stdout, stderr = proc.communicate(input=payload_json, timeout=240)
                
                print(f"DEBUG: SSH returncode={proc.returncode}, stdout_len={len(stdout)}, stderr_len={len(stderr)}", flush=True)
                
                if proc.returncode != 0:
                    print(f"VLM SSH ERROR (rc={proc.returncode}): {stderr[:500]}", flush=True)
                    return None
                    
                if not stdout.strip():
                    print(f"VLM SSH ERROR: Empty stdout. stderr={stderr[:500]}", flush=True)
                    return None

                # Debug: show raw response before parsing
                print(f"DEBUG: VLM raw response ({len(stdout)} chars): {stdout[:300]}...", flush=True)
                
                try:
                    result = json.loads(stdout)
                    content = result.get('message', {}).get('content')
                    return content
                except json.JSONDecodeError as je:
                    print(f"VLM JSON PARSE ERROR: {je}", flush=True)
                    print(f"VLM RAW STDOUT: {stdout[:500]}", flush=True)
                    return None
            else:
                # Fallback to standard HTTP (proxy)
                native_url = self.api_url.replace("/v1", "/api/chat")
                print(f"DEBUG: VLM Proxy Request -> {native_url} (Model: {target_model})")
                print(f"DEBUG: Payload size: {len(json.dumps(payload))} bytes")
                response = requests.post(native_url, json=payload, timeout=240)
                response.raise_for_status()
                result = response.json()
                content = result.get('message', {}).get('content')
                if content:
                    self._result_cache[payload_hash] = content
                return content
                
        except Exception as e:
            import traceback as _tb
            print(f"VLM EXCEPTION: {type(e).__name__}: {e}", flush=True)
            _tb.print_exc()
            return None

    def get_metadata(self, image_path):
        """Analyze a single thumbnail frame (Legacy support, single pass)."""
        # For single frame metadata, we can stick to a simplified single-pass for speed
        prompt = f"Analyze this frame for metadata. Return JSON with description and 7 tags from: {', '.join(ALL_TAGS)}"
        response = self.analyze_frames([image_path], prompt, system_prompt=SYSTEM_PROMPT)
        return self._parse_json(response)

    def _parse_json(self, response):
        if not response: return None
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)
            
            json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                if "tags" in data:
                    data["tags"] = [t.lower().strip() for t in data["tags"] if t.strip()]
                return data
            return None
        except:
            return None

    def _preprocess_for_synthesis(self, burst_logs):
        """Condense verbose per-frame burst logs into clean segment summaries for synthesis."""
        segment_labels = ["Start", "Early", "Middle", "Late", "End", "Extra"]
        summaries = []
        max_performers = 1
        scene_types_seen = set()
        
        for idx, log in enumerate(burst_logs):
            normalized = log.replace('\r\n', '\n').replace('\r', '\n')
            
            # Strip AI preamble from individual burst
            for prefix in ["Okay, I will", "Here's the breakdown", "Here is the"]:
                if prefix.lower() in normalized.lower()[:80]:
                    for field in ["performer_count", "scene_type", "action_verb"]:
                        av_pos = normalized.lower().find(field)
                        if av_pos > 0:
                            normalized = normalized[av_pos:]
                            break
            
            # Extract performer count
            pc_matches = re.findall(r'PERFORMER_COUNT:\s*(\S+)', normalized, re.IGNORECASE)
            for pc in pc_matches:
                pc_clean = pc.strip().rstrip('.')
                if '3' in pc_clean:
                    max_performers = max(max_performers, 3)
                elif '2' in pc_clean or '+' in pc_clean:
                    max_performers = max(max_performers, 2)
            
            # Extract scene type
            st_matches = re.findall(r'SCENE_TYPE:\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            for st in st_matches:
                scene_types_seen.add(st.strip().rstrip('.').lower())
            
            # Extract position
            positions = re.findall(r'POSITION:\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            position = None
            for p in positions:
                p_clean = p.strip().rstrip('.').lower()
                if p_clean not in ['n/a', 'none', '']:
                    position = p_clean
            
            # Extract all action/body/contact from this burst
            verbs = re.findall(r'ACTION_VERB:\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            bodies = re.findall(r'BODY_PART:\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            contacts = re.findall(r'(?:CONTACT|TOOL_USED):\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            
            # Clean up values
            verbs = [v.strip().rstrip('.') for v in verbs]
            bodies = [b.strip().rstrip('.') for b in bodies]
            contacts = [c.strip().rstrip('.') for c in contacts]
            
            # Deduplicate within this segment
            unique_actions = []
            seen = set()
            for i in range(max(len(verbs), len(bodies), len(contacts))):
                v = verbs[i] if i < len(verbs) else ""
                b = bodies[i] if i < len(bodies) else ""
                c = contacts[i] if i < len(contacts) else ""
                key = (v.lower(), b.lower(), c.lower())
                if key not in seen:
                    seen.add(key)
                    unique_actions.append((v, b, c))
            
            if not unique_actions:
                continue
            
            label = segment_labels[idx] if idx < len(segment_labels) else f"Part {idx+1}"
            
            # Build clean per-action descriptions
            action_parts = []
            for v, b, c in unique_actions:
                if v.lower() in ["posing", "none"]:
                    body_word = self._body_to_porn_word(b)
                    action_parts.append(f"teasing — showing off {body_word}")
                else:
                    action_parts.append(self._action_to_phrase(v, b, c))
            
            # Add position context for duo scenes
            current_summary = '. '.join(action_parts)
            if position:
                current_summary += f" ({position})"
            
            # Deduplicate consecutive identical segments
            if summaries and summaries[-1].split(": ", 1)[1].rstrip('.') == current_summary:
                continue

            summaries.append(f"{label}: {current_summary}.")
        
        # Prepend performer context if duo/trio detected
        self._detected_performer_count = max_performers
        if max_performers >= 3:
            summaries.insert(0, "Context: This is a TRIO scene with 3 performers.")
            print(f"PERFORMER DETECTION: Trio scene detected ({max_performers} performers)", flush=True)
        elif max_performers >= 2:
            summaries.insert(0, "Context: This is a DUO scene with 2 performers.")
            print(f"PERFORMER DETECTION: Duo scene detected ({max_performers} performers)", flush=True)
        else:
            print(f"PERFORMER DETECTION: Solo scene detected", flush=True)
        
        # Log scene types detected
        if scene_types_seen:
            print(f"SCENE TYPES DETECTED: {', '.join(scene_types_seen)}", flush=True)
        
        context_str = "\n".join(summaries)
        
        # Simple generic toy flag for context
        toy_detected = False
        for log in burst_logs:
            if "CONTACT: Toy" in log or "CONTACT: toy" in log:
                toy_detected = True
                break
        
        if toy_detected:
            context_str += f"\n\nContext: She uses a toy."
            
        return context_str if summaries else "No clear actions detected."
    
    def _body_to_porn_word(self, body_part):
        """Convert clinical body part names to porn vocabulary."""
        mapping = {
            'breasts': 'tits', 'breast': 'tits', 'tits': 'tits',
            'buttocks': 'ass', 'buttock': 'ass', 'ass': 'ass',
            'vulva': 'pussy', 'vagina': 'pussy', 'clitoris': 'clit',
            'pussy': 'pussy', 'clit': 'clit',
            'thighs': 'thighs', 'mouth': 'mouth', 'face': 'face',
            'anus': 'ass', 'penis': 'cock', 'cock': 'cock', 'neck': 'neck',
        }
        return mapping.get(body_part.lower().strip(), body_part.lower().strip())

    def _action_to_phrase(self, verb, body, contact):
        """Convert verb+body+contact into a natural porn phrase."""
        v = verb.lower().strip()
        b = self._body_to_porn_word(body)
        c = contact.lower().strip() if contact else ""
        
        # Handle empty contact
        no_contact = c in ['', 'none', 'n/a']
        
        # === DUO VERBS ===
        if v in ['fucking', 'penetrating']:
            if 'penis' in c or 'cock' in c:
                return f"getting fucked in her {b}"
            if 'toy' in c:
                return f"getting fucked in her {b} with a toy"
            return f"getting fucked in her {b}"
        if v in ['sucking', 'blowing', 'deepthroating']:
            return f"{v} cock"
        if v == 'eating':
            if b in ['pussy', 'clit', 'vulva']:
                return "getting her pussy eaten"
            return f"eating her {b}"
        if v == 'gagging':
            return "gagging on cock"
        
        # === SOLO/COMMON VERBS ===
        if v in ['pumping', 'inserting', 'thrusting'] and 'toy' in c:
            return f"fucking her {b} with a toy"
        if v in ['pumping', 'inserting', 'thrusting'] and 'finger' in c:
            return f"fingering her {b}"
        if v in ['pumping', 'inserting', 'thrusting'] and 'penis' in c:
            return f"getting fucked in her {b}"
        if v == 'rubbing' and no_contact:
            return f"rubbing her {b}"
        if v == 'rubbing' and 'hand' in c:
            if b in ['pussy', 'clit']: return f"fingering her {b}"
            return f"rubbing her {b}"
        if v == 'rubbing' and 'finger' in c:
            return f"fingering her {b}"
        if v == 'rubbing' and 'toy' in c:
            return f"using a toy on her {b}"
        if v == 'fingering':
            return f"fingering her {b}"
        if v == 'licking' and b == 'mouth':
            return f"licking her lips"
        if v == 'licking':
            if b == 'pussy': return "eating her pussy"
            if b in ['cock', 'penis']: return "licking his cock"
            return f"licking her {b}"
        if v == 'grinding':
            tool = f" on a toy" if 'toy' in c else (f" on a {c}" if not no_contact else "")
            return f"grinding her {b}{tool}"
        if v == 'riding' and 'toy' in c:
            return f"riding a toy"
        if v == 'riding' and 'penis' in c:
            return f"riding cock"
        if v == 'riding':
            return f"riding"
        if v == 'spanking':
            return f"spanking her {b}"
        if v == 'choking':
            return f"choking her"
        if v == 'stroking':
            if b in ['cock', 'penis']: return "giving a handjob"
            return f"stroking her {b}"
        if v == 'squirting':
            return f"squirting"
        
        # Fallback: natural format
        contact_str = f" with {c}" if not no_contact else ""
        return f"{v} her {b}{contact_str}"

    def _strip_preamble(self, text):
        """Remove AI chat preambles like 'Here's a description...' from the start."""
        # Common patterns the model prefixes responses with
        preamble_patterns = [
            r"^here'?s?\s+(a|the|my)?\s*(description|breakdown|summary|answer).*?:\s*\n*",
            r"^based on\s+(the|your|my)?\s*(provided|above|given)?\s*.*?:\s*\n*",
            r"^sure[,!.]?\s*(here'?s?)?.*?:\s*\n*",
            r"^okay[,!.]?\s*(here'?s?)?.*?:\s*\n*",
            r"^certainly[,!.]?\s*.*?:\s*\n*",
            r"^description:\s*\n*",
        ]
        result = text.strip()
        for pattern in preamble_patterns:
            result = re.sub(pattern, '', result, count=1, flags=re.IGNORECASE)
        return result.strip()

    def _sanitize_description(self, text):
        """Greedy Sentence Killer: Deletes sentences with banned words and logs the action."""
        if not text: return "Kinetic interaction involving anatomy and mechanical stimulation."
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        clean_sentences = []
        
        for s in sentences:
            has_banned = False
            s_lower = s.lower()
            for word in BANNED_WORDS:
                pattern = r'\b' + re.escape(word.lower()) + r'\b'
                if re.search(pattern, s_lower):
                    print(f"FORENSIC AUDIT: Deleting banned sentence (Keyword: {word}): \"{s}\"")
                    has_banned = True
                    break
            if not has_banned:
                clean_sentences.append(s)
        
        result = " ".join(clean_sentences).strip()
        # Fallback for 100% fluff cases
        if not result or len(result) < 15:
            print("FORENSIC AUDIT: 100% Fluff detected. Using fallback kinetic description.")
            return "Physical, mechanical interaction involving anatomy and stimulation tools."
        return result

    def _build_description_from_bursts(self, burst_logs, combined_logs):
        """Parse structured fields from burst logs and build a sequential narrative description."""
        actions_seen = []
        
        for log in burst_logs:
            action = {}
            # Normalize line endings (SSH can send \r\n)
            normalized = log.replace('\r\n', '\n').replace('\r', '\n')
            
            verb_match = re.search(r'ACTION_VERB:\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            body_match = re.search(r'BODY_PART:\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            tool_match = re.search(r'(?:CONTACT|TOOL_USED):\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            toy_acc_match = re.search(r'TOY_LABELS:\s*(.+?)(?:\n|$)', normalized, re.IGNORECASE)
            
            if verb_match:
                action['verb'] = verb_match.group(1).strip().rstrip('.')
            if body_match:
                action['body'] = body_match.group(1).strip().rstrip('.')
            if tool_match:
                action['contact'] = tool_match.group(1).strip().rstrip('.')
            if toy_acc_match:
                # Discarding toy_acc_match as per user request to move to manual tagging
                pass
            
            if action.get('verb') and action['verb'].lower() not in ['none', 'n/a', 'unknown', '']:
                actions_seen.append(action)
                print(f"  PARSED: verb={action.get('verb')} body={action.get('body')} contact={action.get('contact')}")
            else:
                print(f"  PARSE MISS: No structured fields found in this burst. Raw: {normalized[:100]}...")
        
        if not actions_seen:
            # Structured parsing failed — extract keywords from raw text instead
            print("BUILDER: Structured fields not found. Extracting keywords from raw text...")
            return self._extract_from_raw_text(combined_logs)
        
        # Narrative Builder Logic v2 (Aggregation + Flow)
        import collections
        
        # 1. Group by Verb/Action to aggregate body parts
        # Format: [ {'verb': 'rubbing', 'bodies': {'tits', 'ass'}, 'contact': 'oil'}, ... ]
        timeline = []
        
        for a in actions_seen:
            verb = a.get('verb', 'posing').lower()
            body = a.get('body', 'body').lower()
            toy_desc = a.get('toys', 'none').lower()
            contact = a.get('contact', 'none').lower()
            
            # Merge with previous if same verb AND same contact type
            if timeline and timeline[-1]['verb'] == verb and timeline[-1]['contact'] == contact:
                timeline[-1]['bodies'].add(body)
                if toy_desc != 'none': timeline[-1]['toys'].add(toy_desc)
            else:
                initial_toys = {toy_desc} if toy_desc != 'none' else set()
                timeline.append({
                    'verb': verb,
                    'bodies': {body},
                    'contact': contact,
                    'toys': initial_toys
                })
        
        if not timeline:
            return "Video contains unidentified separate distinct actions."

        sentences = []
        
        # --- OPENER ---
        first = timeline[0]
        f_bodies = list(first['bodies'])
        f_bodies_str = self._format_body_list(f_bodies)
        
        if first['verb'] in ['posing', 'teasing', 'showing off']:
            sentences.append(f"The video begins with teasing displays of her {f_bodies_str}.")
        else:
            sentences.append(f"The video begins with her {self._action_to_phrase(first['verb'], f_bodies_str, first['contact'])}.")
            
        # Check if any part of the timeline used a toy
        any_toy = any(event.get('contact', '').lower() == 'toy' for event in timeline)
        if any_toy:
            sentences.append(f"She uses a toy.")
            
        # --- MIDDLE FLOW ---
        for event in timeline[1:-1]:
            verb = event['verb']
            bodies = list(event['bodies'])
            contact = event['contact']
            
            # Skip posing in middle
            if verb in ['posing', 'teasing']: continue
            
            phrase = self._action_to_phrase(verb, self._format_body_list(bodies), contact)
            sentences.append(f"She then escalates to {phrase}.")
            
        # --- CLOSER ---
        if len(timeline) > 1:
            last = timeline[-1]
            l_bodies = list(last['bodies'])
            phrase = self._action_to_phrase(last['verb'], self._format_body_list(l_bodies), last['contact'])
            sentences.append(f"The sequence concludes with {phrase}.")

        result = " ".join(sentences)
        print(f"BUILDER: Constructed Narrative: {result}")
        return result

    def _format_body_list(self, bodies):
        """Converts ['tits', 'ass', 'legs'] -> 'tits, ass, and legs'"""
        porn_bodies = sorted(list({self._body_to_porn_word(b) for b in bodies}))
        if not porn_bodies: return "body"
        if len(porn_bodies) == 1: return porn_bodies[0]
        if len(porn_bodies) == 2: return f"{porn_bodies[0]} and {porn_bodies[1]}"
        return f"{', '.join(porn_bodies[:-1])}, and {porn_bodies[-1]}"

    def _extract_from_raw_text(self, raw_text):
        """Smart fallback: scan raw text for action/body keywords and build a description."""
        text_lower = raw_text.lower()
        
        # Known action keywords to look for
        action_map = {
            'rubbing': 'Rubbing', 'inserting': 'Inserting', 'thrusting': 'Thrusting',
            'fingering': 'Fingering', 'grinding': 'Grinding', 'pumping': 'Pumping',
            'vibrating': 'Vibrating', 'licking': 'Licking', 'squirting': 'Squirting',
            'stroking': 'Stroking', 'spanking': 'Spanking', 'riding': 'Riding',
            'penetrat': 'Penetration', 'masturb': 'Masturbation', 'stimulat': 'Stimulation',
            'choking': 'Choking', 'sucking': 'Sucking', 'orgasm': 'Orgasm',
        }
        body_map = {
            'vulva': 'vulva', 'clitoris': 'clitoris', 'vagina': 'vagina',
            'anus': 'anus', 'penis': 'penis', 'breast': 'breasts',
            'nipple': 'nipples', 'buttock': 'buttocks', 'thigh': 'thighs',
            'mouth': 'mouth', 'throat': 'throat',
        }
        contact_map = {
            'finger': 'fingers', 'dildo': 'a toy', 'vibrator': 'a toy',
            'wand': 'a toy', 'toy': 'a toy', 'tongue': 'tongue', 'hand': 'hand',
        }
        
        actions_found = []
        bodies_found = []
        contacts_found = []
        
        for key, val in action_map.items():
            if key in text_lower and val not in actions_found:
                actions_found.append(val)
        for key, val in body_map.items():
            if key in text_lower and val not in bodies_found:
                bodies_found.append(val)
        for key, val in contact_map.items():
            if key in text_lower and val not in contacts_found:
                contacts_found.append(val)
        
        if not actions_found:
            print("BUILDER FALLBACK: No action keywords found in raw text either.")
            return "Sexual activity detected but details could not be determined."
        
        # Build description from found keywords
        action_str = actions_found[0]
        body_str = bodies_found[0] if bodies_found else "genitalia"
        contact_str = f" with {contacts_found[0]}" if contacts_found else ""
        
        parts = [f"{action_str} of {body_str}{contact_str}."]
        
        # Add extra actions if found
        for extra in actions_found[1:3]:  # Max 2 extras
            parts.append(f"Also includes {extra.lower()}.")
        
        result = " ".join(parts)
        print(f"BUILDER FALLBACK: Extracted {len(actions_found)} actions, {len(bodies_found)} body parts from raw text.")
        return result

    def _format_contact(self, contact):
        """Format the CONTACT field into a natural language phrase."""
        if not contact or contact.lower() in ['none', 'n/a', '']:
            return ""
        c = contact.lower()
        if c == 'fingers':
            return " using fingers"
        elif c == 'toy':
            return " with a toy"
        elif c == 'tongue':
            return " with tongue"
        elif c == 'penis':
            return " with penis"
        elif c == 'hand':
            return " with hand"
        else:
            return f" with {contact}"

    def get_metadata_from_video(self, image_paths):
        """Full pipeline: Burst descriptions → Synthesis → Visual Tag Audit."""
        if not image_paths: return None
        
        # Performance: Pre-encode all frames once
        print(f"PIPELINE: Pre-encoding {len(image_paths)} frames...", flush=True)
        all_encoded = {path: self._encode_image(path) for path in image_paths}
        
        # PASS 1: Natural language burst descriptions (Parallel)
        bursts = [image_paths[i:i + 4] for i in range(0, len(image_paths), 4)]
        segment_labels = ["Opening", "Early", "Build-up", "Mid-1", "Mid-2", "Mid-3", "Late-1", "Late-2", "Finale", "Bonus"]
        print(f"PIPELINE: Describing {len(bursts)} segments in parallel...", flush=True)
        
        burst_descriptions_map = {} # Using map to preserve order
        burst_intensities_map = {}
        
        with ThreadPoolExecutor(max_workers=min(4, len(bursts))) as executor:
            future_to_burst = {}
            for i, burst_frames in enumerate(bursts):
                label = segment_labels[i] if i < len(segment_labels) else f"Part {i+1}"
                encoded_burst = [all_encoded[p] for p in burst_frames]
                
                future = executor.submit(
                    self.analyze_frames, 
                    [], # empty paths since we provide pre_encoded 
                    VISION_BURST_PROMPT, 
                    system_prompt=SYSTEM_PROMPT,
                    pre_encoded_images=encoded_burst
                )
                future_to_burst[future] = (i, label)
            
            for future in as_completed(future_to_burst):
                idx, label = future_to_burst[future]
                try:
                    desc = future.result()
                    if desc:
                        desc = self._strip_preamble(desc).strip().strip('"\'')
                        burst_descriptions_map[idx] = f"{label}: {desc}"
                        
                        all_matches = re.findall(r'INTENSITY:\s*["\']?(?:\w+\s*)?["\']?\s*(\d+)', desc, re.IGNORECASE)
                        if all_matches:
                            best_score = max(int(m) for m in all_matches)
                            burst_intensities_map[idx] = best_score
                        else:
                            burst_intensities_map[idx] = -1
                    else:
                        print(f"    Warning: Segment {idx+1} ({label}) returned nothing.", flush=True)
                except Exception as exc:
                    print(f"    Error: Segment {idx+1} ({label}) generated an exception: {exc}", flush=True)

        # Re-assemble in order
        burst_descriptions = [burst_descriptions_map[i] for i in sorted(burst_descriptions_map.keys())]
        burst_intensities = [burst_intensities_map[i] for i in sorted(burst_intensities_map.keys())]

        if not burst_descriptions:
            print("FAILURE: All burst descriptions failed.")
            return None

        combined_logs = "\n".join(burst_descriptions)
        print(f"\n{'='*60}")
        print(f"BURST DESCRIPTIONS:")
        print(combined_logs)
        print(f"{'='*60}\n")

        # PASS 2: Synthesize into a single listing description
        print("PIPELINE: Synthesizing video description...", flush=True)
        synthesis_prompt = SYNTHESIS_PROMPT_TEMPLATE.format(burst_descriptions=combined_logs)
        raw_description = self.analyze_frames([], synthesis_prompt, system_prompt=SYNTHESIS_SYSTEM)
        
        if raw_description:
            print(f"RAW AI DESCRIPTION: {raw_description}")
            raw_description = self._strip_preamble(raw_description)
            raw_description = raw_description.strip('"\'')
            clean_description = self._sanitize_description(raw_description)
        else:
            print("AI synthesis failed — using best burst description as fallback.")
            # Use the longest burst description as fallback
            clean_description = max(burst_descriptions, key=len).split(": ", 1)[-1]
        
        print(f"\n{'='*60}")
        print(f"FINAL DESCRIPTION: {clean_description}")
        print(f"{'='*60}\n")

        # PASS 3: Visual tag audit — vision model with frames picks tags
        print("PIPELINE: Extracting search tags (with vision)...", flush=True)
        audit_prompt = AUDIT_PROMPT_TEMPLATE.format(
            description=clean_description,
            taxonomy=", ".join(ALL_TAGS)
        )
        tag_frames = image_paths[::max(1, len(image_paths) // 6)][:6]
        tags_raw = self.analyze_frames(
            tag_frames, audit_prompt,
            system_prompt="You tag porn videos for search. ALL performers are FEMALE — no men. ONLY tag what you can visually confirm. Do NOT guess."
        )
        
        # Clean tags — only keep tags that exist in our taxonomy
        tags = []
        if tags_raw:
            clean_tags_str = tags_raw.replace("Tags:", "").strip()
            all_tags_lower = [t.lower() for t in ALL_TAGS]
            for t in clean_tags_str.split(","):
                tag = t.strip().lower()
                if tag in all_tags_lower and tag not in tags:
                    tags.append(tag)
        
        print(f"TAGS: {tags}")
        print("PIPELINE SUCCESS.")
        
        best_burst_index = 0
        max_intensity = -1
        if burst_intensities:
            max_intensity = max(burst_intensities)
            if max_intensity > -1:
                # In the event of a tie, prioritize the LAST occurrence (the climax)
                best_burst_index = len(burst_intensities) - 1 - burst_intensities[::-1].index(max_intensity)
        
        print(f"\n{'='*60}")
        print(f"TRAILER TARGETING: All intensities: {burst_intensities}")
        print(f"TRAILER TARGETING: Best burst index: {best_burst_index} ({segment_labels[best_burst_index] if best_burst_index < len(segment_labels) else 'Unknown'})")
        print(f"TRAILER TARGETING: Max intensity: {max_intensity}/10")
        print(f"{'='*60}\n")

        return {
            "description": clean_description,
            "tags": tags,
            "sensor_log_raw": combined_logs,
            "best_burst_index": best_burst_index,
            "max_intensity": max_intensity
        }




    def re_judge_metadata(self, sensor_log):
        """Re-runs Synthesis and Tagging using existing sensor logs without extracting frames."""
        print("PIPELINE: Re-judging video description...", flush=True)
        synthesis_prompt = SYNTHESIS_PROMPT_TEMPLATE.format(burst_descriptions=sensor_log)
        raw_description = self.analyze_frames([], synthesis_prompt, system_prompt=SYNTHESIS_SYSTEM)
        
        if raw_description:
            print(f"RAW AI DESCRIPTION: {raw_description}")
            raw_description = self._strip_preamble(raw_description)
            raw_description = raw_description.strip('"\'')
            clean_description = self._sanitize_description(raw_description)
        else:
            print("AI synthesis failed during re-judge.")
            clean_description = ""
        
        print(f"\n{'='*60}")
        print(f"FINAL DESCRIPTION: {clean_description}")
        print(f"{'='*60}\n")

        print("PIPELINE: Extracting search tags...", flush=True)
        audit_prompt = AUDIT_PROMPT_TEMPLATE.format(
            description=clean_description,
            taxonomy=", ".join(ALL_TAGS)
        )
        
        # During re-judge, we don't have frames, so we rely purely on the text description
        tags_raw = self.analyze_frames(
            [], audit_prompt,
            system_prompt="You tag porn videos for search. ALL performers are FEMALE — no men. Base tags ONLY on the provided description."
        )
        
        tags = []
        if tags_raw:
            clean_tags_str = tags_raw.replace("Tags:", "").strip()
            all_tags_lower = [t.lower() for t in ALL_TAGS]
            for t in clean_tags_str.split(","):
                tag = t.strip().lower()
                if tag in all_tags_lower and tag not in tags:
                    tags.append(tag)
        
        print(f"TAGS: {tags}")
        print("RE-JUDGE PIPELINE SUCCESS.")

        return {
            "description": clean_description,
            "tags": tags,
            "sensor_log_raw": sensor_log,
        }
