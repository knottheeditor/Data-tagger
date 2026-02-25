"""
TAG_LEXICON: Structured Tag Definitions for Content Cataloging.

Format per Boss Spec:
  "tag_name": {
      "description": "What to look for (plain English)",
      "related": ["related_tag_1", "related_tag_2"]
  }

Toys/gear tags are MANUAL-ONLY (human applies these).
The AI uses this lexicon for action/fetish/setting tags.
"""

TAG_LEXICON = {

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ACTS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "masturbation": {
        "description": "Self-stimulation of genitalia using hands or toys.",
        "related": ["fingering", "solo", "nude"]
    },
    "oral": {
        "description": "Physical contact between mouth/tongue and genitalia.",
        "related": ["blowjob", "deepthroat"]
    },
    "blowjob": {
        "description": "Mouth/lips making contact with a penis.",
        "related": ["oral", "deepthroat", "pov"]
    },
    "penetration": {
        "description": "Object or body part visibly entering a body orifice.",
        "related": ["dildo", "fucking-machine", "riding"]
    },
    "anal": {
        "description": "Penetration or stimulation of the anus.",
        "related": ["butt-plug", "anal-beads", "penetration"]
    },
    "riding": {
        "description": "Subject on top, bouncing/grinding on a toy or partner.",
        "related": ["penetration", "grinding"]
    },
    "handjob": {
        "description": "Manual stimulation of a penis using hands.",
        "related": ["pov", "cumshot"]
    },
    "footjob": {
        "description": "Stimulation of genitalia using feet.",
        "related": ["worship"]
    },
    "facesitting": {
        "description": "Subject sitting on another person's face for oral stimulation.",
        "related": ["oral", "domination", "femdom"]
    },
    "grinding": {
        "description": "Rhythmic rubbing of genitalia against a surface, toy, or body.",
        "related": ["riding", "masturbation"]
    },
    "fingering": {
        "description": "Fingers making contact with or entering the vulva/vagina.",
        "related": ["masturbation", "solo"]
    },
    "squirting": {
        "description": "Fluids coming out of vagina, projectile or heavy flow.",
        "related": ["overstimulation", "forced-orgasm", "fingering"]
    },
    "creampie": {
        "description": "Visible ejaculate inside or leaking from an orifice after penetration.",
        "related": ["penetration", "cumshot"]
    },
    "cumshot": {
        "description": "Visible ejaculation onto body or surface.",
        "related": ["blowjob", "handjob"]
    },
    "titfuck": {
        "description": "Penis thrusting between breasts.",
        "related": ["cumshot"]
    },
    "scissoring": {
        "description": "Two subjects rubbing genitalia together.",
        "related": ["duo", "grinding"]
    },
    "deepthroat": {
        "description": "Full insertion of penis into throat, often with gagging.",
        "related": ["blowjob", "oral"]
    },
    "joi": {
        "description": "Jerk-off instruction — subject verbally directing viewer to masturbate.",
        "related": ["pov", "solo", "self-shot"]
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TOYS & GEAR (Manual tagging — AI should not guess these)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "dildo": {
        "description": "Non-vibrating phallic object. Solid, no motor.",
        "related": ["penetration", "masturbation"]
    },
    "vibrator": {
        "description": "Vibrating toy — sleek/curved, has internal motor.",
        "related": ["masturbation", "overstimulation"]
    },
    "wand": {
        "description": "Large vibrator with a rounded spherical head and long handle.",
        "related": ["vibrator", "overstimulation", "forced-orgasm"]
    },
    "drilldo": {
        "description": "Power drill body with a dildo attached to the chuck.",
        "related": ["fucking-machine", "penetration", "overstimulation"]
    },
    "estim": {
        "description": "Electrical stimulation — control box with wires/leads to body.",
        "related": ["electro-play", "overstimulation"]
    },
    "fucking-machine": {
        "description": "Motorized mechanical device that thrusts a dildo attachment.",
        "related": ["penetration", "drilldo", "overstimulation"]
    },
    "butt-plug": {
        "description": "Flared-base plug inserted into the anus.",
        "related": ["anal"]
    },
    "strap-on": {
        "description": "Harness-mounted dildo worn by one partner for penetrating another.",
        "related": ["penetration", "femdom", "duo"]
    },
    "cage": {
        "description": "Metal/plastic enclosure for genitalia (chastity device).",
        "related": ["denial", "bdsm", "submission"]
    },
    "restraints": {
        "description": "Cuffs, ropes, chains, or belts physically constricting limbs or torso.",
        "related": ["bondage", "bdsm", "rope"]
    },
    "collar": {
        "description": "Band around the neck, often with D-ring or leash attachment.",
        "related": ["leash", "pet-play", "submission"]
    },
    "leash": {
        "description": "Rope or chain attached to a collar, held by another person.",
        "related": ["collar", "domination", "pet-play"]
    },
    "gag": {
        "description": "Ball, tape, or fabric in/over the mouth to prevent speech.",
        "related": ["bdsm", "bondage", "submission"]
    },
    "clamps": {
        "description": "Pinching devices attached to nipples or genitalia.",
        "related": ["bdsm", "pain"]
    },
    "one-bar-prison": {
        "description": "Single vertical bar/rod that the subject straddles.",
        "related": ["predicament", "penetration"]
    },
    "grinder": {
        "description": "Motorized saddle or pad designed for grinding/riding stimulation.",
        "related": ["grinding", "riding", "masturbation"]
    },
    "suction-toy": {
        "description": "Device that uses suction/air pulses on the clitoris or nipples.",
        "related": ["masturbation", "overstimulation"]
    },
    "anal-beads": {
        "description": "String of graduated beads for anal insertion/removal.",
        "related": ["anal"]
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FETISH & KINK
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "bdsm": {
        "description": "Bondage, discipline, dominance, submission activities present.",
        "related": ["bondage", "domination", "submission", "restraints"]
    },
    "bondage": {
        "description": "Physical restraint of the body using ropes, cuffs, or chains.",
        "related": ["restraints", "rope", "bdsm"]
    },
    "domination": {
        "description": "One person exerting control/authority over another.",
        "related": ["femdom", "submission", "humiliation"]
    },
    "submission": {
        "description": "Person yielding control, obeying commands or being restrained.",
        "related": ["domination", "collar", "leash"]
    },
    "humiliation": {
        "description": "Verbal or physical degradation of the submissive.",
        "related": ["degradation", "domination"]
    },
    "edging": {
        "description": "Bringing someone close to orgasm then stopping repeatedly.",
        "related": ["denial", "overstimulation"]
    },
    "forced-orgasm": {
        "description": "Continued stimulation through/past orgasm, often while restrained.",
        "related": ["overstimulation", "restraints", "wand"]
    },
    "overstimulation": {
        "description": "Excessive stimulation causing involuntary reactions (shaking, squirting).",
        "related": ["forced-orgasm", "squirting", "wand"]
    },
    "denial": {
        "description": "Orgasm is deliberately prevented or delayed.",
        "related": ["edging", "cage", "submission"]
    },
    "cbt": {
        "description": "Cock and ball torture — pain/pressure applied to male genitalia.",
        "related": ["bdsm", "domination"]
    },
    "cnc": {
        "description": "Consensual non-consent roleplay.",
        "related": ["bdsm", "rough"]
    },
    "hucow": {
        "description": "Human cow roleplay — breast milking/pumping fetish.",
        "related": ["pet-play", "clamps"]
    },
    "pet-play": {
        "description": "Subject acts as an animal (often puppy or kitten) with accessories.",
        "related": ["puppy-play", "collar", "leash"]
    },
    "puppy-play": {
        "description": "Specific pet-play where subject acts as a dog with mask/tail.",
        "related": ["pet-play", "collar", "butt-plug"]
    },
    "predicament": {
        "description": "Subject placed in a position where any movement causes stimulation or discomfort.",
        "related": ["bondage", "one-bar-prison"]
    },
    "electro-play": {
        "description": "Use of electrical stimulation devices during play.",
        "related": ["estim", "bdsm"]
    },
    "wax-play": {
        "description": "Dripping hot wax onto the body.",
        "related": ["bdsm"]
    },
    "choking": {
        "description": "Hand or accessory around the throat applying pressure.",
        "related": ["domination", "rough"]
    },
    "spanking": {
        "description": "Striking the buttocks with hand or implement.",
        "related": ["bdsm", "domination", "rough"]
    },
    "degradation": {
        "description": "Verbal or physical acts to debase/humiliate the subject.",
        "related": ["humiliation", "domination"]
    },
    "worship": {
        "description": "Devoted attention to a body part (feet, ass, etc.).",
        "related": ["footjob", "submission"]
    },
    "femdom": {
        "description": "Female-led domination.",
        "related": ["domination", "strap-on", "facesitting"]
    },
    "rope": {
        "description": "Shibari or rope bondage — decorative or functional tying.",
        "related": ["bondage", "restraints"]
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SUBJECT COUNT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "solo": {
        "description": "Single performer only.",
        "related": ["masturbation", "self-shot"]
    },
    "duo": {
        "description": "Two performers interacting.",
        "related": ["scissoring", "oral"]
    },
    "trio": {
        "description": "Three performers interacting.",
        "related": ["group", "duo"]
    },
    "group": {
        "description": "Four or more performers.",
        "related": ["trio"]
    },
    "pov": {
        "description": "Camera perspective from one participant's point of view.",
        "related": ["self-shot", "blowjob", "joi"]
    },
    "self-shot": {
        "description": "Subject is filming themselves (holding camera or using tripod).",
        "related": ["solo", "pov"]
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # OUTFIT & BODY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "nude": {
        "description": "Complete absence of clothing.",
        "related": ["topless"]
    },
    "topless": {
        "description": "Upper body exposed, nipples visible.",
        "related": ["nude"]
    },
    "lingerie": {
        "description": "Decorative underwear — bra, panties, garters, etc.",
        "related": ["stockings", "corset"]
    },
    "stockings": {
        "description": "Hosiery covering legs, often thigh-high.",
        "related": ["lingerie", "thigh-highs"]
    },
    "latex": {
        "description": "Shiny rubber/latex clothing.",
        "related": ["bdsm", "fetish"]
    },
    "harness": {
        "description": "Strappy body harness, often leather or elastic.",
        "related": ["bdsm", "lingerie"]
    },
    "fishnets": {
        "description": "Net-pattern hosiery or clothing.",
        "related": ["stockings"]
    },
    "thigh-highs": {
        "description": "Socks or stockings reaching upper thigh.",
        "related": ["stockings"]
    },
    "corset": {
        "description": "Structured garment cinching the waist.",
        "related": ["lingerie"]
    },
    "choker": {
        "description": "Tight band around the neck (fashion, not BDSM collar).",
        "related": ["collar"]
    },
    "bodysuit": {
        "description": "One-piece garment covering the torso.",
        "related": ["lingerie"]
    },
    "bikini": {
        "description": "Two-piece swimwear.",
        "related": []
    },
    "skirt": {
        "description": "Short skirt, often pleated or mini.",
        "related": ["schoolgirl"]
    },
}
