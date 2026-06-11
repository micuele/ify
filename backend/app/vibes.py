from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class VibeCategory:
    slot: int
    key: str
    label: str
    description: str
    music_tags: frozenset[str]
    film_genres: frozenset[str]
    keywords: frozenset[str]
    traits: frozenset[str] = frozenset()

    @property
    def image_key(self) -> str:
        return f"{self.slot:02d}"


def _terms(value: str) -> frozenset[str]:
    return frozenset(term.strip() for term in value.split("|") if term.strip())


VIBE_CATEGORIES = (
    VibeCategory(1, "pop-comedy", "Pop & Comedy", "Pop, upbeat music, comedy, friendship, celebration, and feel-good stories.", _terms("pop|feel-good|happy|upbeat|sunshine pop|power pop|motown|ska|reggae|calypso"), _terms("comedy"), _terms("joy|joyful|sunny|summer|friendship|celebration|fun|hopeful|heartwarming"), _terms("daytime")),
    VibeCategory(2, "romance-soul", "Romance & Soul", "Romance films and warm R&B, soul, ballads, intimacy, love, and relationships.", _terms("r&b|romantic|love|ballad|neo-soul|contemporary r&b|soul|soft rock"), _terms("romance"), _terms("love|romance|romantic|desire|wedding|relationship|intimate|passion|tender")),
    VibeCategory(3, "drama-melancholy", "Drama & Melancholy", "Drama, emo, heartbreak, grief, loneliness, bittersweet stories, and sad music.", _terms("sad|sad songs|melancholic|emo|indie folk|slowcore|heartbreak"), _terms("drama"), _terms("grief|loss|heartbreak|mourning|bittersweet|tears|lonely|farewell|memory")),
    VibeCategory(4, "indie-introspection", "Indie & Introspection", "Indie, alternative, acoustic, singer-songwriter, solitude, identity, and reflective stories.", _terms("alternative|indie|introspective|minimal|acoustic|minimalism|chamber pop|piano|singer-songwriter"), _terms(""), _terms("solitude|isolated|quiet|reflection|identity|personal|diary|alone|contemplative"), _terms("low_activity")),
    VibeCategory(5, "fantasy-dream-pop", "Fantasy & Dream Pop", "Fantasy films with dream pop, shoegaze, magic, dreams, and otherworldly imagery.", _terms("dream pop|shoegaze|ethereal|dreampop|cloud rap|reverb|ambient pop|space rock"), _terms("fantasy"), _terms("dream|dreamlike|ethereal|angel|heaven|magic|fairy|enchanted|floating")),
    VibeCategory(6, "ambient-slow", "Ambient & Slow", "Ambient, chill, lo-fi, downtempo, minimal, peaceful, meditative, and slow experiences.", _terms("ambient|chill|downtempo|lo-fi|new age|meditation|drone|chillout"), _terms(""), _terms("calm|peaceful|meditative|ocean|water|silence|relaxing|slow|tranquil"), _terms("low_activity")),
    VibeCategory(7, "folk-country-western", "Folk, Country & Western", "Folk, country, Americana, roots music, westerns, rural life, nature, and home.", _terms("folk|americana|country|bluegrass|roots|folk rock|world|traditional"), _terms("western"), _terms("nature|rural|village|farm|forest|mountain|earth|land|wilderness|home")),
    VibeCategory(8, "classics-history-nostalgia", "Classics, History & Nostalgia", "Older films and music, history, rewatches, retro styles, childhood, and memories.", _terms("retro|80s|70s|60s|oldies|classic rock|synth-pop|new wave|vintage"), _terms("history|tv movie"), _terms("nostalgia|nostalgic|childhood|past|vintage|retro|memories|reunion|coming of age"), _terms("rewatch|older_catalog")),
    VibeCategory(9, "animation-family-indie-pop", "Animation, Family & Indie Pop", "Animation and family films with indie pop, cute, playful, colorful, and imaginative themes.", _terms("bubblegum pop|indie pop|twee|chiptune|8-bit|kawaii|novelty|music box"), _terms("animation|family"), _terms("whimsical|playful|cute|colorful|child|toy|mischief|adventure|imagination")),
    VibeCategory(10, "jazz-blues-style", "Jazz, Blues & Style", "Jazz, blues, lounge, elegant settings, fashion, luxury, charm, and smooth style.", _terms("jazz|blues|cool jazz|smooth jazz|trip hop|lounge|acid jazz|sophisti-pop|bossa nova"), _terms(""), _terms("stylish|cool|fashion|luxury|charming|smooth|elegant|heist|nightclub")),
    VibeCategory(11, "dance-electronic-music", "Dance, Electronic & Music", "Dance music, EDM, house, disco, techno, concerts, clubs, festivals, and performance films.", _terms("dance|edm|house|disco|club|dance-pop|trance|eurodance|techno"), _terms("music"), _terms("party|dance|club|festival|stage|performance|concert|celebration|fame"), _terms("high_activity|evening")),
    VibeCategory(12, "latin-global-rhythm", "Latin & Global Rhythm", "Latin and global dance styles including salsa, reggaeton, Afrobeat, samba, and carnival.", _terms("latin|salsa|reggaeton|afrobeat|samba|cumbia|bachata|flamenco|dancehall"), _terms(""), _terms("rhythm|tropical|carnival|latin|heat|island|samba|flamenco")),
    VibeCategory(13, "hip-hop-urban", "Hip-Hop & Urban Stories", "Hip-hop, rap, trap, city life, street stories, ambition, money, and power.", _terms("hip hop|rap|trap|grime|drill|gangsta rap|urban|g-funk"), _terms(""), _terms("street|city|gang|money|hustle|ambition|rapper|power")),
    VibeCategory(14, "rock-punk-rebellion", "Rock, Punk & Rebellion", "Rock, punk, grunge, protest, youth rebellion, outsiders, resistance, and DIY culture.", _terms("rock|alternative rock|indie rock|punk|hardcore punk|post-punk|garage rock|grunge|riot grrrl|anarcho-punk|ska punk"), _terms(""), _terms("rebellion|rebel|protest|revolution|resistance|outsider|youth|authority|riot")),
    VibeCategory(15, "metal-action-adrenaline", "Metal, Action & Adrenaline", "Metal and hard rock with action, combat, revenge, chases, survival, and high intensity.", _terms("metal|heavy metal|death metal|thrash metal|metalcore|hard rock|hardcore|drum and bass"), _terms("action"), _terms("fight|battle|revenge|explosion|warrior|violent|chase|survival|combat"), _terms("high_activity")),
    VibeCategory(16, "horror-gothic-dark", "Horror, Gothic & Dark Music", "Horror films with gothic, darkwave, black metal, haunted, supernatural, and macabre themes.", _terms("gothic|darkwave|black metal|industrial|horror punk|deathrock|doom metal|witch house"), _terms("horror"), _terms("ghost|haunted|demon|monster|death|curse|vampire|witch|evil|nightmare"), _terms("night")),
    VibeCategory(17, "thriller-industrial-tension", "Thriller, Industrial & Tension", "Thrillers with industrial and dark electronic music, danger, paranoia, escape, and suspense.", _terms("dark ambient|industrial techno|post-industrial|power electronics|tense|minimal techno"), _terms("thriller"), _terms("danger|escape|kidnap|conspiracy|paranoia|threat|stalker|trapped|terror|race against")),
    VibeCategory(18, "crime-mystery-noir", "Crime, Mystery & Noir", "Crime and mystery films with detectives, murder, investigation, corruption, secrets, and noir style.", _terms("jazz noir|dark jazz|smoky|noir"), _terms("mystery|crime"), _terms("detective|murder|secret|mystery|investigation|noir|corruption|missing|case"), _terms("night")),
    VibeCategory(19, "psychedelia-surrealism", "Psychedelia & Surrealism", "Psychedelic music and surreal, hallucinatory, symbolic, bizarre, and reality-bending stories.", _terms("psychedelic|psychedelic rock|neo-psychedelia|psytrance|acid rock|krautrock|hypnotic"), _terms(""), _terms("surreal|hallucination|psychedelic|bizarre|reality|vision|metaphor|strange")),
    VibeCategory(20, "experimental-art-house", "Experimental & Art House", "Experimental music and unconventional art-house work: abstract, nonlinear, avant-garde, and underground.", _terms("experimental|avant-garde|noise|free jazz|musique concrete|art rock|art pop|abstract|field recording"), _terms(""), _terms("experimental|abstract|unconventional|art|artist|essay|nonlinear|installation|underground"), _terms("high_diversity")),
    VibeCategory(21, "sci-fi-electronic-future", "Sci-Fi, Electronic & Future", "Science fiction with electronic music, technology, space, aliens, robots, cyberpunk, and dystopia.", _terms("electronic|synthwave|cyberpunk|electro|futuristic|space ambient"), _terms("science fiction"), _terms("future|space|alien|robot|technology|virtual|cyber|computer|android|dystopia")),
    VibeCategory(22, "adventure-war-epic", "Adventure, War & Epic", "Adventure and war films with orchestral music, quests, heroes, kingdoms, battles, and cinematic scale.", _terms("epic|orchestral|soundtrack|film score|power metal|post-rock|symphonic|cinematic|opera"), _terms("adventure|war"), _terms("hero|kingdom|quest|empire|journey|legend|battle|historic|destiny|world")),
    VibeCategory(23, "documentary-classical-ideas", "Documentary, Classical & Ideas", "Documentaries and intellectual work with classical, progressive, scientific, political, and philosophical themes.", _terms("classical|progressive rock|math rock|jazz fusion|modern classical|idm|technical|complex"), _terms("documentary"), _terms("philosophy|science|politics|society|mind|theory|intellectual|biography|documentary|truth"), _terms("high_diversity")),
    VibeCategory(24, "hyperpop-satire-chaos", "Hyperpop, Satire & Chaos", "Hyperpop, breakcore, satire, absurdity, anarchy, maximalism, unpredictability, and mayhem.", _terms("hyperpop|breakcore|experimental pop|digital hardcore|mathcore|plunderphonics|deconstructed club|chaotic"), _terms(""), _terms("chaos|chaotic|absurd|madness|wild|anarchy|satire|unpredictable|frenzy|mayhem")),
)


def normalize_signal(value: str) -> str:
    value = value.lower().replace("&", " and ").replace("-", " ")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", value)).strip()


def text_signals(values: Iterable[str]) -> Counter[str]:
    signals: Counter[str] = Counter()
    for value in values:
        normalized = normalize_signal(value)
        words = normalized.split()
        signals.update(words)
        for size in (2, 3):
            signals.update(
                " ".join(words[index:index + size])
                for index in range(len(words) - size + 1)
            )
    return signals


def classify_vibe(
    *,
    music_tags: Counter[str] | None = None,
    film_genres: Counter[str] | None = None,
    text: Counter[str] | None = None,
    traits: Counter[str] | None = None,
    seed: str = "ify",
) -> dict[str, object]:
    music: Counter[str] = Counter()
    genres: Counter[str] = Counter()
    words: Counter[str] = Counter()
    for key, value in (music_tags or {}).items():
        music[normalize_signal(key)] += value
    for key, value in (film_genres or {}).items():
        genres[normalize_signal(key)] += value
    for key, value in (text or {}).items():
        words[normalize_signal(key)] += value
    profile_traits = Counter(traits or {})
    ranked: list[tuple[float, int, VibeCategory, list[str]]] = []

    for category in VIBE_CATEGORIES:
        score = 0.0
        evidence: list[tuple[float, str]] = []

        for term in category.music_tags:
            weight = music.get(normalize_signal(term), 0) * 4.0
            if weight:
                score += weight
                evidence.append((weight, term))
        for term in category.film_genres:
            weight = genres.get(normalize_signal(term), 0) * 5.0
            if weight:
                score += weight
                evidence.append((weight, term))
        for term in category.keywords:
            weight = words.get(normalize_signal(term), 0) * 1.5
            if weight:
                score += weight
                evidence.append((weight, term))
        for trait in category.traits:
            weight = profile_traits.get(trait, 0) * 2.0
            if weight:
                score += weight
                evidence.append((weight, trait.replace("_", " ")))

        tie_break = int(hashlib.sha256(f"{seed}:{category.key}".encode()).hexdigest()[:8], 16)
        ranked.append((score, tie_break, category, [item[1] for item in sorted(evidence, reverse=True)[:5]]))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    score, _, winner, evidence = ranked[0]
    runner_up = ranked[1][0]
    confidence = 0.0 if score <= 0 else round((score - runner_up) / score, 3)

    return {
        "slot": winner.slot,
        "key": winner.key,
        "image_key": winner.image_key,
        "label": winner.label,
        "description": winner.description,
        "match_score": round(score, 2),
        "confidence": confidence,
        "evidence": evidence,
    }


def category_catalog() -> list[dict[str, object]]:
    return [
        {
            "slot": category.slot,
            "key": category.key,
            "image_key": category.image_key,
            "label": category.label,
            "description": category.description,
        }
        for category in VIBE_CATEGORIES
    ]
