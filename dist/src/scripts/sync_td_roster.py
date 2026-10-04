#!/usr/bin/env python3

"""Rebuild the digimon roster in td_lore.html from the Trello board + repo file list.

Sources: trello.com/b/Z5gjWmkN board JSON (the 5 evolution-tier lists, plus
the untiered "Done Mons Not Yet Implemented" list - its cards get filed
under their real tier if they turn out to already be implemented, otherwise
into a dedicated "Additional Planned Models" group under Model Only), the
digimon/ data folder and en_us.json lang file in themodderg/The-Digimod.

A card is "in the mod" if its name slugifies straight to an implemented
file, or is in CONFIRMED_ALIASES (a manually-verified Trello/repo spelling
mismatch). Anything else gets checked against every implemented digimon's
actual in-game display name (lang file) + evo_stage for a possible match,
printed as a SUGGESTION - never applied automatically, since the mod's own
lang file has real duplicate/mislabeled entries that can look like a match.

Also updates the digimon-count sentence in the About The Mod text
(src/scripts/js/texts/the_digimod.js) with the current in-mod/planned totals.

Per-digimon "spawn_biomes" (vanilla + modded biome resource ids it can
naturally spawn in) is computed from the mod's own biome_modifier + tag
files under data/thedigimod/ - see build_spawn_biomes_map(). That data is
read straight off a local checkout (mod_source_root) regardless of whether
--local was passed for the digimon json/lang fetches, since it's static mod
config, not per-digimon content.
"""

from pathlib import Path
import difflib
import html
import json
import re
import subprocess
import sys
import urllib.request

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
TD_LORE_HTML = REPO_ROOT / "pages" / "td" / "td_lore.html"
THE_DIGIMOD_JS = REPO_ROOT / "src/scripts/js/texts/the_digimod.js"
ROSTER_DIR = REPO_ROOT / "src/assets/images/the_digimod/roster"
MODELERS_IMG_DIR = REPO_ROOT / "src/assets/images/the_digimod/modelers"
MODELER_PLACEHOLDER_IMG = "./src/assets/images/the_digimod/modelers/placeholder.png"


def modeler_image_for(name: str) -> str:
	"""Return the wiki path for a modeler avatar, falling back to the shared
	placeholder. Any file matching `<slug>.png` under the modelers dir is used,
	where slug lowercases the name and strips non-alphanumeric chars."""
	slug = re.sub(r"[^a-z0-9]+", "", name.lower())
	if slug and (MODELERS_IMG_DIR / f"{slug}.png").is_file():
		return f"./src/assets/images/the_digimod/modelers/{slug}.png"
	return MODELER_PLACEHOLDER_IMG

# Trello credit strings that aren't a modeler name at all - either card
# status labels the board uses when no author is set, or grouping markers.
# Anything matching this set (case-insensitive) is dropped from the modelers
# roster entirely instead of showing up as a fake contributor.
NON_MODELER_CREDITS = {
	"in mod",
	"extras",
	"done",
}

# Regex: any credit that starts with "done" (e.g. "DONE! - Added in 1.7") is
# a status label, not a name. Checked in addition to NON_MODELER_CREDITS.
NON_MODELER_CREDIT_PREFIXES = ("done!", "added in ")

TRELLO_BOARD_URL = "https://trello.com/b/Z5gjWmkN/the-digimod-needed-models.json"
GITHUB_API_URL = (
	"https://api.github.com/repos/themodderg/The-Digimod/contents/"
	"src/main/resources/data/thedigimod/digimon"
)
DIGIMON_JSON_URL_TMPL = (
	"https://raw.githubusercontent.com/themodderg/The-Digimod/main/"
	"src/main/resources/data/thedigimod/digimon/{slug}.json"
)
LANG_URL = (
	"https://raw.githubusercontent.com/themodderg/The-Digimod/main/"
	"src/main/resources/assets/thedigimod/lang/en_us.json"
)
MOD_ID = "thedigimod"

# Cached per-digimon json so re-runs don't re-fetch 138+ files every time.
DIGIMON_CACHE_DIR = Path(__file__).resolve().parent / ".td_digimon_cache"
LANG_CACHE_FILE = Path(__file__).resolve().parent / ".td_digimon_cache" / "_lang.json"

# Optional local override: when set (via `--local [path]`), read digimon json
# and the lang file straight from an unreleased local copy of the mod source
# instead of hitting GitHub. Lets the roster reflect additions that aren't
# pushed yet. Set in main() from argv; default local path is the standard
# dev checkout under ~/raid/mods/digimods/digimod.
LOCAL_MOD_ROOT: Path | None = None
DEFAULT_LOCAL_MOD_ROOT = Path.home() / "raid/mods/digimods/digimod"

# Which evo_stage indices are valid for a card filed under each Trello tier.
# Trello collapses the game's "Perfect" and "Ultimate" stages into one list.
TIER_STAGE_INDEXES = {
	"Babies I in The Mod": {0},
	"Babies II In The Mod": {1},
	"Rookies In The Mod": {2},
	"Champions In The Mod": {3},
	"Ultimates In The Mod": {4, 5},
}

TIER_LISTS = [
	("Babies I in The Mod", "Babies I", "baby1"),
	("Babies II In The Mod", "Babies II", "baby2"),
	("Rookies In The Mod", "Rookies", "rookie"),
	("Champions In The Mod", "Champions", "champion"),
	("Ultimates In The Mod", "Ultimates", "ultimate"),
]
TIER_SLUG_BY_KEY = {key: slug for key, _title, slug in TIER_LISTS}

# Evo stage label to show for planned (not-yet-implemented) cards based on
# which Trello tier list they came from. Trello merges Perfect + Ultimate
# under one list, so we surface both in that case. The untiered extra list
# has no tier info, so entries there don't get a stage label.
TIER_STAGE_LABEL = {
	"Babies I in The Mod": "Baby I",
	"Babies II In The Mod": "Baby II",
	"Rookies In The Mod": "Rookie",
	"Champions In The Mod": "Champion",
	"Ultimates In The Mod": "Perfect / Ultimate",
}

# Reverse of TIER_STAGE_INDEXES: which tier bucket a *matched* card from the
# untiered extra list belongs under, based on its own json's evo_stage.
STAGE_TO_TIER_KEY = {
	0: "Babies I in The Mod",
	1: "Babies II In The Mod",
	2: "Rookies In The Mod",
	3: "Champions In The Mod",
	4: "Ultimates In The Mod",
	5: "Ultimates In The Mod",
}

# A 6th Trello list, not organized by evolution stage - a mix of digimon that
# have a finished 3D model but (per the list's own name) aren't coded into
# the mod yet. In practice some of them already are (the list isn't kept
# perfectly in sync with mod progress), so every card here still goes
# through the same resolve_slug() check as the 5 tiered lists: a match gets
# filed under its real tier (from its own evo_stage), everything else lands
# in Model Only under a dedicated "Additional Planned Models" group, since we
# have no tier info for cards that aren't implemented yet.
EXTRA_LIST_NAME = "Done Mons Not Yet Implemented"
EXTRA_LIST_TIER_KEY = "__extra_unplaced__"
EXTRA_LIST_TITLE = "Additional Planned Models"
TIER_STAGE_INDEXES[EXTRA_LIST_TIER_KEY] = {0, 1, 2, 3, 4, 5}

MAX_ICON_SIDE = 800

# "xps" in each digimon json is a list of indices into this tag (order taken
# from data/thedigimod/tags/items/xps/xps.json) - not raw XP amounts, but
# which "Data" item that digimon drops.
XP_ITEMS = [
	("dragon_data", "Dragon Data"),
	("beast_data", "Beast Data"),
	("plantinsect_data", "Plant/Insect Data"),
	("aquan_data", "Aquan Data"),
	("wind_data", "Wind Data"),
	("machine_data", "Machine Data"),
	("earth_data", "Earth Data"),
	("nightmare_data", "Nightmare Data"),
	("holy_data", "Holy Data"),
]

EVO_STAGE_LABELS = ["Baby I", "Baby II", "Rookie", "Champion", "Perfect", "Ultimate"]

# Trello-vs-repo spelling mismatches, confirmed as the same digimon by hand.
# suggest_slug_candidates() surfaces candidates from the mod's en_us.json
# lang file + evo_stage, but never applies them automatically - the mod has
# real duplicate/mislabeled lang entries (e.g. conomon.json's lang key
# incorrectly says "Cocomon", which would otherwise collide with the actual,
# separate, not-yet-implemented "Cocomon" baby digimon card). Every entry
# below was checked against BOTH the lang display name AND evo_stage/tier
# before being added - do the same before adding more.
CONFIRMED_ALIASES: dict[str, str] = {
	"Yarmon": "keemon",  # lang: "entity.thedigimod.keemon" = "Yarmon" (mod's
		# own file/entity slug is "keemon", but its actual in-game display name
		# is "Yarmon" - a separate rename/mixup bug from the "Keemon" one below).
		# Confirmed by ModderG (mod author): Yarmon and Keemon are two distinct
		# already-implemented digimon, not a duplicate card for the same one.
		# See SLUG_OVERRIDES for how "Keemon" itself resolves to a different
		# file ("kiimon.json") instead of colliding with this one.
	"DarkTyranomon": "darktyrannomon",  # lang: "Dark Tyrannomon"
	"Darklizamon": "darklizardmon",  # lang: "DarkLizardmon"
	"Flarelizamon": "flarerizamon",  # lang: "Flarerizamon"
	"RedV-dramon": "redveedramon",  # lang: "RedVeedramon"
	"V-dramon": "veedramon",  # lang: "Veedramon"
	"BlackGrowmon": "blackgrowlmon",  # lang: "BlackGrowmon"
	"Growmon": "growlmon",  # lang: "Growmon"
	"Growmon (Data)": "growlmondata",  # lang: "Growmon(Data)"
	"Chackmon": "chakmon",  # lang: "Chakmon"
	"Wizarmon": "wizardmon",  # lang: "Wizardmon" - Trello card dropped the "d"
		# ("Wizarmon") so it no longer slugifies to the "wizardmon" file; the
		# lang display still reads "Wizardmon" so lang_slug_map can't bridge it.
	"Tyranomon": "tyrannomon",  # lang: "Tyrannomon"
	"Grizzmon": "grizzlymon",  # lang: "Grizzlymon"
	"Dogmon": "doggymon",  # lang: "Dogmon" - file slug is unrelated to the name
	"Gokimon": "roachmon",  # lang: "Gokimon" - file slug is unrelated to the name
	"AlturKabuterimon (Red)": "alturkabuterimon",  # lang: "AlturKabuterimon" (base
		# file has no color suffix, unlike "alturkabuterimonblue" - confirmed by
		# the actual entity texture being red/maroon, matching the card art)
	"Algomon (BabyII)": "algomonbaby2",  # lang: "Algomon (Baby II)"
	"Algomon (Child)": "algomonrookie",  # lang: "Algomon (Child)"
	"Algomon (Adult)": "algomonchampion",  # lang: "Algomon (Adult)"
	"Algomon (Perfect)": "algomonultimate",  # lang: "Algomon (Perfect)"
	"Coredramon (Blue)": "coredramon",  # lang: "Coredramon (Blue)" - the mod's
		# single Coredramon file is the blue variant (green is not implemented)
	"Greymon (Blue)": "greymonvirus",  # lang: "Greymon (Blue)" - canonically
		# the virus/blue Greymon are the same variant
	"Pucchiemon (Green)": "greenpucchiemon",  # lang: "Pucchiemon (Green)"
	"Guardromon (Gold)": "goldguardromon",  # lang: "Guardromon (Gold)"
	"Shoutmon (King Ver.)": "kingshoutmon",  # lang: "Shoutmon (King Ver.)"
	"Dorulumon": "dolurumon",  # lang: "Dorulumon" - romanisation typo in file slug
	"Zassoumon": "weedmon",  # lang: "Zassoumon" - "weed" is the EN localisation
	"Jyureimon": "cherrymon",  # lang: "Jyureimon" - JP name; EN is Cherrymon
	"Cockatrimon": "kokatorimon",  # lang: "Cockatrimon" - romanisation of the JP file slug
	"Pyocomon": "yokomon",  # confirmed by ModderG (mod author): yokomon.json is
		# the digimon the community calls "Pyocomon" - "pyocomon.json" doesn't
		# exist, and the "Yokomon" lang name is itself a mistake on the mod's
		# side (to be renamed in a future version). "Hyokomon" (a separate,
		# similarly-named Trello card) is NOT this or any other implemented
		# digimon - don't alias it.
	# Cocomon -> conomon.json, Pipimon -> datirimon.json, and
	# "V-dramon (Black)" -> veedramonblack.json used to need entries here too
	# (all confirmed by ModderG, mod author), but as of build_lang_slug_map()
	# they resolve automatically since their Trello names match the mod's own
	# lang display name exactly - kept out of this dict to avoid duplicating
	# what resolve_slug() already does on its own.
}

# Trello-vs-repo name collisions where the direct slugify() match would grab
# the WRONG implemented file - checked before the direct-match/CONFIRMED_ALIASES
# lookup in resolve_slug(). Every entry here is a case where two DIFFERENT
# already-implemented digimon have file/lang names that cross over.
SLUG_OVERRIDES: dict[str, str] = {
	"Keemon": "kiimon",  # slugify("Keemon") == "keemon", which IS an
		# implemented file - but keemon.json's actual in-game name is "Yarmon"
		# (see CONFIRMED_ALIASES above), not Keemon. The real "Keemon" (lang:
		# "Keemon"/"Keemon Digitama") is a separate file, kiimon.json, which
		# evolves into keemon.json (Yarmon). Confirmed by ModderG (mod author).
}

# Checked and rejected: these look like matches (same/similar display name in
# the lang file, or similar spelling) but are NOT the same digimon. Listed so
# nobody re-adds them after seeing them in the suggestions output.
#   'ShoutmonX5' ~ shoutmonx3.json  (canonically distinct Shoutmon fusion
#                                     forms, just a similar naming pattern -
#                                     texture doesn't clearly match either)
#   'Hyokomon'   ~ yokomon.json      (NOT the same digimon - confirmed by
#                                     ModderG; see "Pyocomon" above for the
#                                     card that actually is yokomon.json.
#                                     Hyokomon is a separate, not-yet-
#                                     implemented digimon)
#   'Youkomon'   ~ yokomon.json      (a duplicate card for the same Pyocomon/
#                                     Yokomon confusion, already claimed by
#                                     "Pyocomon" above)


def fetch_json(url: str) -> dict:
	req = urllib.request.Request(url, headers={"User-Agent": "codderg-wiki-sync"})
	with urllib.request.urlopen(req) as resp:
		return json.loads(resp.read())


def clean_card_name(raw_name: str) -> str:
	# Card names are "<Digimon> [(<variant tag>)] (<credited author(s)>)" - only
	# the LAST parenthetical is the credit, strip that one and stop. A variant
	# tag paren earlier in the name (e.g. "Agumon (Black) (ModderG)") must stay.
	return re.sub(r"\s*\([^()]*\)\s*$", "", raw_name)


def extract_credit(raw_name: str) -> str | None:
	# The credit is that same trailing parenthetical clean_card_name() strips -
	# pull it back out so the roster can show who modeled each digimon. Cards
	# with no trailing paren at all (rare, but seen on a few untiered-list
	# entries) have no credit to show.
	match = re.search(r"\(([^()]*)\)\s*$", raw_name)
	return match.group(1).strip() if match else None


def slugify(name: str) -> str:
	return re.sub(r"[^a-z0-9]", "", name.lower())


def download(url: str, dest: Path) -> None:
	subprocess.run(["curl", "-sL", "-o", str(dest), url], check=True)


def fetch_digimon_json(slug: str) -> dict:
	if LOCAL_MOD_ROOT is not None:
		# Local mode: read straight from the working copy, skip the cache
		# entirely (cache holds stale GitHub content and local files are
		# fast enough that caching them buys nothing).
		path = LOCAL_MOD_ROOT / "src/main/resources/data/thedigimod/digimon" / f"{slug}.json"
		return json.loads(path.read_text(encoding="utf-8"))
	DIGIMON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
	cache_file = DIGIMON_CACHE_DIR / f"{slug}.json"
	if cache_file.exists():
		return json.loads(cache_file.read_text(encoding="utf-8"))
	data = fetch_json(DIGIMON_JSON_URL_TMPL.format(slug=slug))
	cache_file.write_text(json.dumps(data), encoding="utf-8")
	return data


def fetch_lang_display_map() -> dict:
	# entity.thedigimod.<slug> -> in-game display name, straight from the
	# mod's own translation file. Used to auto-resolve Trello cards whose
	# name doesn't match the file slug (typos, unrelated internal slugs).
	if LOCAL_MOD_ROOT is not None:
		lang = json.loads(
			(LOCAL_MOD_ROOT / "src/main/resources/assets/thedigimod/lang/en_us.json")
			.read_text(encoding="utf-8")
		)
	else:
		LANG_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
		if LANG_CACHE_FILE.exists():
			lang = json.loads(LANG_CACHE_FILE.read_text(encoding="utf-8"))
		else:
			lang = fetch_json(LANG_URL)
			LANG_CACHE_FILE.write_text(json.dumps(lang), encoding="utf-8")

	prefix = "entity.thedigimod."
	return {k[len(prefix):]: v for k, v in lang.items() if k.startswith(prefix)}


def list_implemented_slugs() -> set:
	"""Return the set of implemented digimon slugs, from the local mod source
	when `--local` is active, or from the GitHub contents API otherwise."""
	if LOCAL_MOD_ROOT is not None:
		digimon_dir = LOCAL_MOD_ROOT / "src/main/resources/data/thedigimod/digimon"
		return {p.stem for p in digimon_dir.glob("*.json")}
	entries = fetch_json(GITHUB_API_URL)
	return {
		e["name"].removesuffix(".json")
		for e in entries
		if e["type"] == "file" and e["name"].endswith(".json")
	}


def build_lang_slug_map(lang_display: dict, implemented: set) -> dict[str, str]:
	"""Map slugify(in-game display name) -> file slug, for every implemented
	digimon. Used by resolve_slug() as an EXACT-match fallback so a Trello
	card whose name matches the mod's own displayed name auto-resolves, even
	when the file slug itself differs (e.g. conomon.json displaying as
	"Cocomon").

	This is safe where the fuzzy suggest_slug_candidates() isn't: an exact
	slug match doesn't suffer from the near-miss false positives that come
	from string similarity (e.g. "Hyokomon" vs. "Yokomon" - two different
	slugs, so this map correctly leaves that one alone). If two implemented
	digimon happen to slugify to the same display name (not currently the
	case, but the mod's lang file has had duplicates before), that slug is
	dropped from the map entirely rather than guessing which one a card
	means.
	"""
	by_lang_slug: dict[str, list[str]] = {}
	for file_slug, display in lang_display.items():
		if file_slug not in implemented or not display:
			continue
		by_lang_slug.setdefault(slugify(display), []).append(file_slug)
	return {k: v[0] for k, v in by_lang_slug.items() if len(v) == 1}


def resolve_slug(
	clean_name: str,
	tier_key: str,
	implemented: set,
	lang_slug_map: dict[str, str] | None = None,
) -> str | None:
	"""Return the implemented slug for a card, or None if not in the mod.

	Checked in order: a SLUG_OVERRIDES entry (a direct-match would grab the
	wrong file), the Trello name slugified directly against file slugs, the
	same slugified name against every implemented digimon's actual in-game
	display name (lang_slug_map - exact match only, see build_lang_slug_map()
	for why that's safe), or a manual CONFIRMED_ALIASES override for anything
	that still doesn't line up. Deliberately NOT fuzzy beyond that - see
	suggest_slug_candidates() for why.
	"""
	if clean_name in SLUG_OVERRIDES:
		override = SLUG_OVERRIDES[clean_name]
		return override if override in implemented else None
	direct = slugify(clean_name)
	if direct in implemented:
		return direct
	if lang_slug_map and direct in lang_slug_map:
		return lang_slug_map[direct]
	alias = CONFIRMED_ALIASES.get(clean_name)
	return alias if alias in implemented else None


def suggest_slug_candidates(clean_name: str, tier_key: str, implemented: set, lang_display: dict) -> list[str]:
	"""Suggest (never apply) implemented slugs that might be this card, by
	fuzzy-comparing the Trello name against every implemented digimon's
	actual in-game display name (en_us.json) - close-but-not-exact matches
	only, gated by the evo_stage being valid for the card's tier.

	Exact display-name matches are handled automatically by resolve_slug()
	via build_lang_slug_map() and never reach this function. This one is for
	near-misses only (e.g. "Hyokomon" vs. the implemented "Yokomon"), which
	really can be a different digimon that just has a similar name - those
	must be checked by hand and added to CONFIRMED_ALIASES once confirmed.
	"""
	target = slugify(clean_name)
	valid_stages = TIER_STAGE_INDEXES.get(tier_key, set())
	candidates = []
	for slug in implemented:
		display = lang_display.get(slug, "")
		if not display:
			continue
		if fetch_digimon_json(slug).get("evo_stage") not in valid_stages:
			continue
		display_norm = slugify(display)
		ratio = difflib.SequenceMatcher(None, target, display_norm).ratio()
		if ratio >= 0.9:
			candidates.append(f"{slug!r} (lang: {display!r}, similarity {ratio:.2f})")
	return candidates


def build_spawn_biomes_map(mod_source_root: Path) -> dict[str, list[str]]:
	"""Map digimon slug -> sorted list of biome resource ids (vanilla + modded)
	it can naturally spawn in, computed from the mod's own biome/spawn config:

	  data/thedigimod/forge/biome_modifier/*.json  (type add_tag_spawns /
	    add_tag_monster_spawns) pairs a biome tag with an entity tag - e.g.
	    "#thedigimod:grassy" spawns everything in
	    "thedigimod:spawns/rookies/grassy_biomes".
	  data/thedigimod/tags/worldgen/biome/<name>.json resolves a biome tag to
	    its actual biome ids (a flat list - no nested tag refs in this mod's
	    files, confirmed by inspection). Optional-mod-compat entries are
	    `{"id": "...", "required": false}` objects instead of plain strings.
	  data/thedigimod/tags/entity_types/<path>.json resolves an entity tag to
	    its digimon entity ids the same way.

	This is read straight off disk (not fetched from GitHub) since it's static
	mod config unrelated to per-digimon json/lang content, and a local
	checkout is always available (mod_source_root, whether or not --local was
	passed for the digimon json fetches themselves)."""
	data_root = mod_source_root / "src/main/resources/data/thedigimod"
	biome_mod_dir = data_root / "forge/biome_modifier"
	biome_tag_dir = data_root / "tags/worldgen/biome"
	entity_tag_dir = data_root / "tags/entity_types"
	if not biome_mod_dir.is_dir():
		return {}

	def resolve_tag_values(path: Path) -> list[str]:
		data = json.loads(path.read_text(encoding="utf-8"))
		return [v if isinstance(v, str) else v["id"] for v in data.get("values", [])]

	mapping: dict[str, set] = {}
	for f in sorted(biome_mod_dir.glob("*.json")):
		d = json.loads(f.read_text(encoding="utf-8"))
		if d.get("type") not in ("thedigimod:add_tag_spawns", "thedigimod:add_tag_monster_spawns"):
			continue
		biome_ns, biome_name = d["biomes"].lstrip("#").split(":", 1)
		entity_ns, entity_name = d["entity_tag"].split(":", 1)
		if biome_ns != MOD_ID or entity_ns != MOD_ID:
			continue
		biomes = resolve_tag_values(biome_tag_dir / f"{biome_name}.json")
		entities = resolve_tag_values(entity_tag_dir / f"{entity_name}.json")
		for e in entities:
			slug = e.split(":", 1)[1]
			mapping.setdefault(slug, set()).update(biomes)

	return {slug: sorted(biomes) for slug, biomes in mapping.items()}


def build_evolves_from_map(all_slugs: set) -> dict:
	# "evolves_from" isn't a field in any single digimon's json - it only
	# exists as the reverse of every OTHER digimon's "evolutions" keys, so it
	# has to be computed from the full implemented set, not per-card.
	reverse: dict[str, list[str]] = {}
	for slug in all_slugs:
		data = fetch_digimon_json(slug)
		for child in (data.get("evolutions") or {}).keys():
			reverse.setdefault(child, []).append(slug)
	return {k: sorted(v) for k, v in reverse.items()}


def fetch_digimon_stats(slug: str, evolves_from_map: dict, spawn_biomes_map: dict) -> dict:
	data = fetch_digimon_json(slug)

	evolutions = data.get("evolutions") or {}
	xp_drops = []
	for i in data.get("xps") or []:
		if isinstance(i, int) and 0 <= i < len(XP_ITEMS):
			item_slug, label = XP_ITEMS[i]
			xp_drops.append(
				{
					"label": label,
					"img": f"./src/assets/images/the_digimod/xp_items/{item_slug}.png",
					# Data items always get a td_item_<slug>.html page from sync_td_items.py.
					"href": f"./td_item_{item_slug}.html",
				}
			)

	evo_stage = data.get("evo_stage")
	if isinstance(evo_stage, int) and 0 <= evo_stage < len(EVO_STAGE_LABELS):
		evo_stage = EVO_STAGE_LABELS[evo_stage]

	default_move = data.get("default_sp_move")

	# DigimonJsonDataManager.applyJsonData() only calls setDiet() when the
	# json actually has a "diet" key - otherwise the entity keeps the diet
	# DigimonEntity's constructor assigns unconditionally, DietInit.REGULAR_DIET
	# (confirmed in themodderg/The-Digimod source: DigimonEntity.java sets
	# `this.diet = DietInit.REGULAR_DIET;`, and DietInit.getDiet()'s switch
	# also falls to REGULAR_DIET for any unrecognized string). So a missing
	# "diet" key is a real in-game "regular", not a data gap - reflect that
	# instead of leaving the roster's Diet row blank for these entries.
	diet = data.get("diet") or "regular"

	return {
		"entity_id": f"{MOD_ID}:{slug}",
		"profession": data.get("profession"),
		"diet": diet,
		"evo_stage": evo_stage,
		"default_move": default_move,
		# Every default move has a matching chip_<move>.html page from
		# sync_td_items.py - it's a Special Attack Chip item id by convention.
		"default_move_href": f"./td_item_chip_{default_move}.html" if default_move else None,
		"xp_drops": xp_drops,
		"evolves_into": sorted(evolutions.keys()),
		"evolves_from": evolves_from_map.get(slug, []),
		"spawn_biomes": spawn_biomes_map.get(slug, []),
	}


def split_modeler_credit(credit: str | None) -> list[str]:
	"""Split a Trello credit string like 'ModderG & Fapdos' into individual
	modeler names, dropping status-label credits (see NON_MODELER_CREDITS).
	Returns [] if the credit is empty, a pure status label, or resolves to
	no real names."""
	if not credit:
		return []
	# Trello credits use ' & ' as the collab separator; a handful of cards
	# use ' and ' instead ("Jawoon and Tymander") - normalise so both split
	# the same way and roll up under the same modeler entries.
	normalised = re.sub(r"\s+and\s+", " & ", credit)
	parts = [p.strip() for p in re.split(r"\s*&\s*", normalised) if p.strip()]
	names = []
	for name in parts:
		lower = name.lower()
		if lower in NON_MODELER_CREDITS:
			continue
		if any(lower.startswith(pref) for pref in NON_MODELER_CREDIT_PREFIXES):
			continue
		names.append(name)
	return names


def build_modelers_data(all_cards: list, js_entries: list) -> list[dict]:
	"""Aggregate Trello credit strings into per-modeler contribution lists.

	Each modeler entry surfaces two lists:
	  - 'sole': digimon where they are the only credited modeler
	  - 'collab': digimon where they share the credit with someone else

	Names are folded case-insensitively (NoahRed3603 vs Noahred3603 collapse
	to one entry) but the most common casing is kept as the display name.
	Entries are sorted by total contribution count desc, then by name."""
	# Map from normalized name to {canon_name: str, casings: Counter, sole, collab}.
	# Normalization strips whitespace and underscores in addition to case-folding,
	# so `Megadrive_Menace`, `MegadriveMenace`, and `Megadrive Menace` all collapse
	# to one modeler. On top of that, MODELER_ALIASES handles typos that the
	# whitespace/case rules can't catch (missing letter, digit swap, etc.).
	# Keys and values must both be in normalized form (lowercase, no spaces/underscores).
	MODELER_ALIASES = {
		"moddeg": "modderg",              # missing 'r' in ModdeG
		"noadred3603": "noahred3603",     # 'd' typo for 'h' in NoadRed3603
		"tennythomas1": "tennythomas",    # stray trailing '1'
		"vampirestartfish": "vampirestarfish",  # extra 't'
		"kronoschaos979": "kronoschaos",  # trailing '979' variant
		"majorgigimon": "majorsirius",    # same person, alt handle
		"gwen": "thetwizzler",            # Gwen is a made-up placeholder for The Twizzler
		"tisthehuman": "kan",             # "tis the human" is Kan's alt handle
	}

	# Display-name overrides for buckets whose collapsed key doesn't match any
	# name that appears in the Trello cards (or when we want to force a specific
	# casing/handle). Keyed by the normalized bucket key.
	MODELER_DISPLAY_OVERRIDES = {
		"thetwizzler": "The Twizzler",
	}

	def modeler_key(name: str) -> str:
		k = re.sub(r"[\s_]+", "", name).lower()
		return MODELER_ALIASES.get(k, k)

	buckets: dict[str, dict] = {}
	# Build a card-name -> js_entries idx map so the rotator can jump into
	# the mob roster when a digimon is clicked inside a modeler's panel.
	name_to_idx = {e["name"]: i for i, e in enumerate(js_entries)}

	for card in all_cards:
		modelers = split_modeler_credit(card.get("credit"))
		if not modelers:
			continue
		idx = name_to_idx.get(card["clean_name"])
		is_collab = len(modelers) > 1
		# Deduplicate collaborators that only differ in whitespace/underscore/case
		# on the same card so partners lists don't double up the same person.
		seen_keys: dict[str, str] = {}
		for name in modelers:
			seen_keys.setdefault(modeler_key(name), name)
		unique_modelers = list(seen_keys.values())
		is_collab = len(unique_modelers) > 1
		for name in modelers:
			key = modeler_key(name)
			bucket = buckets.setdefault(
				key,
				{"canon": name, "casings": {}, "sole": [], "collab": []},
			)
			bucket["casings"][name] = bucket["casings"].get(name, 0) + 1
			entry = {"name": card["clean_name"]}
			if idx is not None:
				entry["idx"] = idx
			if is_collab:
				# Store partner keys for now; resolve to canonical display names
				# in a second pass once every bucket's canon is known.
				entry["_partner_keys"] = [
					modeler_key(n) for n in unique_modelers if modeler_key(n) != key
				]
				bucket["collab"].append(entry)
			else:
				bucket["sole"].append(entry)

	# Pick the most-used casing per modeler as the display name so we don't
	# arbitrarily pick whichever one happened to appear first. Then apply
	# MODELER_DISPLAY_OVERRIDES to force a specific name for buckets where the
	# aliased identity has a different display name than any Trello card uses.
	for key, bucket in buckets.items():
		if key in MODELER_DISPLAY_OVERRIDES:
			bucket["canon"] = MODELER_DISPLAY_OVERRIDES[key]
		else:
			bucket["canon"] = max(bucket["casings"].items(), key=lambda kv: kv[1])[0]

	# Resolve partner keys to canonical display names now that every bucket
	# has its canon assigned.
	key_to_canon = {k: b["canon"] for k, b in buckets.items()}
	for bucket in buckets.values():
		for entry in bucket["collab"]:
			partner_keys = entry.pop("_partner_keys", [])
			entry["partners"] = [key_to_canon.get(k, k) for k in partner_keys]

	modelers = []
	for bucket in buckets.values():
		modelers.append(
			{
				"name": bucket["canon"],
				"img": modeler_image_for(bucket["canon"]),
				"sole": sorted(bucket["sole"], key=lambda e: e["name"].lower()),
				"collab": sorted(bucket["collab"], key=lambda e: e["name"].lower()),
			}
		)

	modelers.sort(key=lambda m: (-(len(m["sole"]) + len(m["collab"])), m["name"].lower()))
	return modelers


def build_modeler_charts_data(all_cards: list, modelers: list) -> dict:
	"""Aggregate counts for the four charts under the modelers list:

	- stageCounts: digimon per evolution stage, split into "in mod" vs
	  "planned only" so the roster's progress is visible at a glance.
	- topContributors: modelers ranked by total contributions (solo + collab).
	- topSolo: modelers ranked by solo models only.
	- topTeams: multi-modeler teams (sorted signature) ranked by how many
	  cards they collaborated on together.
	"""
	# Stage chart: only in-mod cards are counted, because the "modeled but
	# not implemented" cards all live in Trello's untiered extra list and
	# don't carry stage info. Perfect and Ultimate get merged into a single
	# row because the game treats them as one late-game tier (and Trello's
	# Ultimates list holds both).
	stage_bucket_order = ["Baby I", "Baby II", "Rookie", "Champion", "Perfect / Ultimate"]
	stage_alias = {
		"Baby I": "Baby I",
		"Baby II": "Baby II",
		"Rookie": "Rookie",
		"Champion": "Champion",
		"Perfect": "Perfect / Ultimate",
		"Ultimate": "Perfect / Ultimate",
	}
	stage_counts = {label: 0 for label in stage_bucket_order}
	for card in all_cards:
		if not card["in_mod"]:
			continue
		stage = (card.get("stats") or {}).get("evo_stage")
		bucket = stage_alias.get(stage)
		if bucket:
			stage_counts[bucket] += 1
	stage_chart = [
		{"label": label, "count": stage_counts[label]}
		for label in stage_bucket_order
	]

	# Modeler ranking — already sorted by total desc inside build_modelers_data.
	# No truncation: the chart body scrolls and shows every modeler.
	top_contrib = [
		{"name": m["name"], "count": len(m["sole"]) + len(m["collab"])}
		for m in modelers
	]
	top_solo = sorted(
		[{"name": m["name"], "count": len(m["sole"])} for m in modelers],
		key=lambda r: (-r["count"], r["name"].lower()),
	)
	top_solo = [r for r in top_solo if r["count"] > 0]

	top_collab = sorted(
		[{"name": m["name"], "count": len(m["collab"])} for m in modelers],
		key=lambda r: (-r["count"], r["name"].lower()),
	)
	top_collab = [r for r in top_collab if r["count"] > 0]

	# Histogram of solo-model counts across modelers. Log-ish bins so the
	# long tail (100+) doesn't get lost next to the "made 1-2 things" crowd.
	solo_bins = [
		("1-2", 1, 2),
		("3-5", 3, 5),
		("6-10", 6, 10),
		("11-20", 11, 20),
		("21-50", 21, 50),
		("51-100", 51, 100),
		("100+", 101, 10**9),
	]
	solo_histogram = []
	for label, lo, hi in solo_bins:
		n = sum(1 for m in modelers if lo <= len(m["sole"]) <= hi)
		solo_histogram.append({"label": label, "count": n})

	# Teams: for every collab entry, form a sorted tuple of (canon modeler +
	# canon partners), tally how many distinct cards share the same team.
	# A single card only counts once no matter how many modelers report it,
	# so we key by (team, card_name) and then dedupe.
	team_cards: dict[tuple, set] = {}
	for m in modelers:
		for entry in m["collab"]:
			team = tuple(sorted(set([m["name"]] + list(entry.get("partners", [])))))
			if len(team) < 2:
				continue
			team_cards.setdefault(team, set()).add(entry["name"])
	teams = [
		{"members": list(team), "count": len(cards)}
		for team, cards in team_cards.items()
	]
	teams.sort(key=lambda r: (-r["count"], ", ".join(r["members"]).lower()))
	# Drop the long tail of one-off teams — a team that only ever teamed up
	# once isn't a "recurring team," and would flood the chart otherwise.
	top_teams = [t for t in teams if t["count"] > 1]

	return {
		"stageCounts": stage_chart,
		"topContributors": top_contrib,
		"topSolo": top_solo,
		"topCollaborators": top_collab,
		"topTeams": top_teams,
		"soloHistogram": solo_histogram,
	}


def main() -> int:
	global LOCAL_MOD_ROOT
	argv = sys.argv[1:]
	if "--local" in argv:
		i = argv.index("--local")
		# Allow either `--local` (use default checkout) or `--local <path>`.
		if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
			LOCAL_MOD_ROOT = Path(argv[i + 1]).expanduser().resolve()
		else:
			LOCAL_MOD_ROOT = DEFAULT_LOCAL_MOD_ROOT
		if not (LOCAL_MOD_ROOT / "src/main/resources/data/thedigimod/digimon").is_dir():
			print(f"ERROR: --local path has no digimon dir: {LOCAL_MOD_ROOT}", file=sys.stderr)
			return 2
		print(f"Local mode: reading mod data from {LOCAL_MOD_ROOT}", file=sys.stderr)

	board = fetch_json(TRELLO_BOARD_URL)
	lists_by_name = {l["name"]: l["id"] for l in board["lists"]}

	implemented = list_implemented_slugs()
	# Only trust alias targets that still resolve to a real digimon file. A mod
	# rename can leave an alias pointing at a file that no longer exists; warn
	# and drop it instead of letting the whole sync crash on the missing json.
	stale_aliases = {k: v for k, v in CONFIRMED_ALIASES.items() if v not in implemented}
	for card, target in stale_aliases.items():
		print(f"WARNING: stale alias {card!r} -> {target!r} (no such file); dropping", file=sys.stderr)
	implemented |= {v for v in CONFIRMED_ALIASES.values() if v in implemented}
	lang_display = fetch_lang_display_map()
	lang_slug_map = build_lang_slug_map(lang_display, implemented)

	evolves_from_map = build_evolves_from_map(implemented)
	spawn_biomes_map = build_spawn_biomes_map(LOCAL_MOD_ROOT or DEFAULT_LOCAL_MOD_ROOT)

	ROSTER_DIR.mkdir(parents=True, exist_ok=True)

	js_entries: list[dict] = []
	suggestion_notes: list[str] = []

	all_tier_titles = {key: title for key, title, _slug in TIER_LISTS}
	all_tier_titles[EXTRA_LIST_TIER_KEY] = EXTRA_LIST_TITLE
	group_order = [key for key, _t, _s in TIER_LISTS] + [EXTRA_LIST_TIER_KEY]

	def add_group(label_id: str, label: str, cards: list, include_header: bool = True) -> list[str]:
		lines = []
		if include_header:
			lines.append(f'            <li id="{label_id}" class="mob-group-label">{html.escape(label)}</li>')
		for tier_key in group_order:
			tier_cards = [c for c in cards if c["tier_key"] == tier_key]
			if not tier_cards:
				continue
			lines.append(f'            <li class="mob-tier-label">{html.escape(all_tier_titles[tier_key])}</li>')
			for card in tier_cards:
				idx = len(js_entries)
				lines.append(f'            <li data-idx="{idx}">{html.escape(card["clean_name"])}</li>')
				entry = {
					"name": card["clean_name"],
					"img": card["img_rel_path"],
					"stats": card["stats"],
					"credit": card["credit"],
				}
				# Planned (not-in-mod) cards have no stats block, but for tiered
				# lists we still know their evo stage from which list they came
				# from - surface it so the sidebar isn't just a credit line.
				if not card["in_mod"] and card.get("planned_stage"):
					entry["evo_stage"] = card["planned_stage"]
				js_entries.append(entry)
		return lines

	def process_card(card: dict, source_tier_key: str, source_tier_slug: str) -> dict | None:
		clean_name = clean_card_name(card["name"])
		credit = extract_credit(card["name"])
		resolved_slug = resolve_slug(clean_name, source_tier_key, implemented, lang_slug_map)
		slug = resolved_slug or slugify(clean_name)
		in_mod = resolved_slug is not None

		# A match from the untiered extra list gets filed under its real
		# tier (known from its own json), not left in the untiered bucket.
		tier_key, tier_slug = source_tier_key, source_tier_slug
		if in_mod and source_tier_key == EXTRA_LIST_TIER_KEY:
			stage = fetch_digimon_json(slug).get("evo_stage")
			tier_key = STAGE_TO_TIER_KEY.get(stage, source_tier_key)
			tier_slug = TIER_SLUG_BY_KEY.get(tier_key, source_tier_slug)

		if not in_mod:
			candidates = suggest_slug_candidates(clean_name, source_tier_key, implemented, lang_display)
			if candidates:
				suggestion_notes.append(f"{clean_name!r}: {', '.join(candidates)}")

		cover_id = card.get("cover", {}).get("idAttachment")
		attachments = card.get("attachments", [])
		att = next((a for a in attachments if a["id"] == cover_id), None) or (
			attachments[0] if attachments else None
		)
		if not att:
			print(f"WARNING: no cover image for {card['name']!r}, skipping", file=sys.stderr)
			return None

		fname = f"{tier_slug}_{slugify(clean_name)}.png"
		dest = ROSTER_DIR / fname
		if not dest.exists():
			raw_dest = dest.with_suffix(".raw")
			download(att["url"], raw_dest)
			im = Image.open(raw_dest).convert("RGBA")
			w, h = im.size
			scale = MAX_ICON_SIDE / max(w, h)
			if scale < 1:
				im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
			im.save(dest, "PNG", optimize=True)
			raw_dest.unlink()

		return {
			"tier_key": tier_key,
			"clean_name": clean_name,
			"resolved_slug": slug if in_mod else None,
			"img_rel_path": f"./src/assets/images/the_digimod/roster/{fname}",
			"in_mod": in_mod,
			"stats": fetch_digimon_stats(slug, evolves_from_map, spawn_biomes_map) if in_mod else None,
			"credit": credit,
			"planned_stage": TIER_STAGE_LABEL.get(source_tier_key) if not in_mod else None,
		}

	all_cards = []
	for tier_key, tier_title, tier_slug in TIER_LISTS:
		list_id = lists_by_name.get(tier_key)
		if not list_id:
			print(f"WARNING: list {tier_key!r} not found on board", file=sys.stderr)
			continue
		cards = sorted(
			(c for c in board["cards"] if c["idList"] == list_id and not c.get("closed")),
			key=lambda c: c["pos"],
		)
		for card in cards:
			result = process_card(card, tier_key, tier_slug)
			if result:
				all_cards.append(result)

	extra_list_id = lists_by_name.get(EXTRA_LIST_NAME)
	if not extra_list_id:
		print(f"WARNING: list {EXTRA_LIST_NAME!r} not found on board", file=sys.stderr)
	else:
		extra_cards = sorted(
			(c for c in board["cards"] if c["idList"] == extra_list_id and not c.get("closed")),
			key=lambda c: c["pos"],
		)
		for card in extra_cards:
			result = process_card(card, EXTRA_LIST_TIER_KEY, "planned")
			if result:
				all_cards.append(result)

	in_mod_cards = [c for c in all_cards if c["in_mod"]]
	modeled_cards = [c for c in all_cards if not c["in_mod"]]

	# The "In The Mod" group label + the live search box are hardcoded in
	# td_lore.html, immediately before the TD-ROSTER:LIST markers, so this
	# resync must not regenerate that header line (it would duplicate it).
	list_lines = add_group("section-mobs-in-mod", "In The Mod", in_mod_cards, include_header=False)
	list_lines += add_group("section-mobs-modeled", "Model Only — Not Yet Implemented", modeled_cards)

	# Regex match starts at "<!--"/"//", existing indentation before it is
	# kept as-is - don't re-add indentation here or it doubles per run.
	list_block = (
		"<!-- TD-ROSTER:LIST:START (generated by src/scripts/sync_td_roster.py, do not hand-edit) -->\n"
		+ "\n".join(list_lines)
		+ "\n            <!-- TD-ROSTER:LIST:END -->"
	)

	entries_lines = [
		"// TD-ROSTER:ENTRIES:START (generated by src/scripts/sync_td_roster.py, do not hand-edit)"
	]
	entries_lines += [
		"        " + json.dumps(e) + ("," if i < len(js_entries) - 1 else "")
		for i, e in enumerate(js_entries)
	]
	entries_lines.append("        // TD-ROSTER:ENTRIES:END")
	entries_block = "\n".join(entries_lines)

	modelers = build_modelers_data(all_cards, js_entries)
	charts_data = build_modeler_charts_data(all_cards, modelers)

	# Section list: one clickable <li> per modeler, under a single group
	# label. Same class hooks the mobs list uses so the .modelers-overview
	# selectors in sections.css can piggyback on the existing mob styles.
	modelers_list_lines = [
		'            <li id="section-modelers-list" class="mob-group-label">Modelers</li>'
	]
	for i, m in enumerate(modelers):
		total = len(m["sole"]) + len(m["collab"])
		modelers_list_lines.append(
			f'            <li data-modeler-idx="{i}">'
			f'{html.escape(m["name"])} <span class="modeler-count">({total})</span>'
			f'</li>'
		)
	modelers_list_block = (
		"<!-- TD-MODELERS:LIST:START (generated by src/scripts/sync_td_roster.py, do not hand-edit) -->\n"
		+ "\n".join(modelers_list_lines)
		+ "\n            <!-- TD-MODELERS:LIST:END -->"
	)

	modelers_entries_lines = [
		"// TD-MODELERS:ENTRIES:START (generated by src/scripts/sync_td_roster.py, do not hand-edit)"
	]
	modelers_entries_lines += [
		"        " + json.dumps(m) + ("," if i < len(modelers) - 1 else "")
		for i, m in enumerate(modelers)
	]
	modelers_entries_lines.append("        // TD-MODELERS:ENTRIES:END")
	modelers_entries_block = "\n".join(modelers_entries_lines)

	charts_block = (
		"// TD-MODELER-CHARTS:DATA:START (generated by src/scripts/sync_td_roster.py, do not hand-edit)\n"
		"      var MODELER_CHART_DATA = " + json.dumps(charts_data) + ";\n"
		"      // TD-MODELER-CHARTS:DATA:END"
	)

	content = TD_LORE_HTML.read_text(encoding="utf-8")

	content = re.sub(
		r"<!-- TD-ROSTER:LIST:START.*?<!-- TD-ROSTER:LIST:END -->",
		lambda _: list_block,
		content,
		flags=re.DOTALL,
	)
	content = re.sub(
		r"// TD-ROSTER:ENTRIES:START.*?// TD-ROSTER:ENTRIES:END",
		lambda _: entries_block,
		content,
		flags=re.DOTALL,
	)
	content = re.sub(
		r"<!-- TD-MODELERS:LIST:START.*?<!-- TD-MODELERS:LIST:END -->",
		lambda _: modelers_list_block,
		content,
		flags=re.DOTALL,
	)
	content = re.sub(
		r"// TD-MODELERS:ENTRIES:START.*?// TD-MODELERS:ENTRIES:END",
		lambda _: modelers_entries_block,
		content,
		flags=re.DOTALL,
	)
	content = re.sub(
		r"// TD-MODELER-CHARTS:DATA:START.*?// TD-MODELER-CHARTS:DATA:END",
		lambda _: charts_block,
		content,
		flags=re.DOTALL,
	)
	if js_entries:
		content = re.sub(
			r'(id="mobs-rotator-img" src=")[^"]*(")',
			lambda m: m.group(1) + js_entries[0]["img"] + m.group(2),
			content,
			count=1,
		)

	TD_LORE_HTML.write_text(content, encoding="utf-8")

	about_sentence = (
		f"It currently adds {len(in_mod_cards)} digimon, with {len(modeled_cards)} more "
		f"already modeled and being worked into the mod."
	)
	about_js = THE_DIGIMOD_JS.read_text(encoding="utf-8")
	about_js = re.sub(
		r"<!-- TD-ABOUT-COUNTS:START.*?<!-- TD-ABOUT-COUNTS:END -->",
		lambda _: (
			"<!-- TD-ABOUT-COUNTS:START (generated by src/scripts/sync_td_roster.py, do not hand-edit) -->"
			+ about_sentence
			+ "<!-- TD-ABOUT-COUNTS:END -->"
		),
		about_js,
		flags=re.DOTALL,
	)
	THE_DIGIMOD_JS.write_text(about_js, encoding="utf-8")

	# A card can change tier_slug between runs (e.g. resolve_slug starts
	# matching it, moving it from the untiered "planned_" bucket to its real
	# tier) - clean up whatever PNG that leaves behind under the old name.
	used_files = {Path(c["img_rel_path"]).name for c in all_cards}
	for png in ROSTER_DIR.glob("*.png"):
		if png.name not in used_files:
			png.unlink()
			print(f"Removed orphaned roster image: {png.name}", file=sys.stderr)

	print(f"in_mod={len(in_mod_cards)} modeled={len(modeled_cards)} total={len(all_cards)}")
	if suggestion_notes:
		print(
			f"SUGGESTIONS: {len(suggestion_notes)} modeled card(s) have a possible lang-file match "
			f"- verify by hand (lang name AND evo_stage/tier) before adding to CONFIRMED_ALIASES:",
			file=sys.stderr,
		)
		for note in suggestion_notes:
			print(f"  {note}", file=sys.stderr)
	unmatched_implemented = implemented - {c["resolved_slug"] for c in in_mod_cards}
	if unmatched_implemented:
		print(
			f"NOTE: {len(unmatched_implemented)} implemented digimon have no matching Trello card "
			f"in the tier lists: {sorted(unmatched_implemented)}",
			file=sys.stderr,
		)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
