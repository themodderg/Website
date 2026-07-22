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
TD_LORE_HTML = REPO_ROOT / "td_lore.html"
THE_DIGIMOD_JS = REPO_ROOT / "src/scripts/js/texts/the_digimod.js"
ROSTER_DIR = REPO_ROOT / "src/assets/images/the_digimod/roster"

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
	"DarkTyranomon": "darktyrannomon",  # lang: "Dark Tyrannomon"
	"Darklizamon": "darklizardmon",  # lang: "DarkLizardmon"
	"Flarelizamon": "flarerizamon",  # lang: "Flarerizamon"
	"RedV-dramon": "redveedramon",  # lang: "RedVeedramon"
	"V-dramon": "veedramon",  # lang: "Veedramon"
	"Vegimon": "vegiemon",  # lang: "Vegiemon"
	"BlackGrowmon": "blackgrowlmon",  # lang: "BlackGrowmon"
	"Growmon": "growlmon",  # lang: "Growmon"
	"Growmon (Data)": "growlmondata",  # lang: "Growmon(Data)"
	"Chackmon": "chakmon",  # lang: "Chakmon"
	"Tyranomon": "tyrannomon",  # lang: "Tyrannomon"
	"Grizzmon": "grizzlymon",  # lang: "Grizzlymon"
	"Dogmon": "doggymon",  # lang: "Dogmon" - file slug is unrelated to the name
	"Gokimon": "roachmon",  # lang: "Gokimon" - file slug is unrelated to the name
	"AlturKabuterimon (Red)": "alturkabuterimon",  # lang: "AlturKabuterimon" (base
		# file has no color suffix, unlike "alturkabuterimonblue" - confirmed by
		# the actual entity texture being red/maroon, matching the card art)
	"Pyocomon": "yokomon",  # confirmed by ModderG (mod author): yokomon.json is
		# the digimon the community calls "Pyocomon" - "pyocomon.json" doesn't
		# exist, and the "Yokomon" lang name is itself a mistake on the mod's
		# side (to be renamed in a future version). "Hyokomon" (a separate,
		# similarly-named Trello card) is NOT this or any other implemented
		# digimon - don't alias it.
}

# Checked and rejected: these look like matches (same/similar display name in
# the lang file, or similar spelling) but are NOT the same digimon. Listed so
# nobody re-adds them after seeing them in the suggestions output.
#   'Cocomon'    ~ conomon.json     (lang wrongly says "Cocomon" - mod bug)
#   'Pipimon'    ~ datirimon.json   (lang wrongly says "Pipimon" - mod bug)
#   'Yarmon'     ~ keemon.json      (lang wrongly says "Yarmon" - mod bug;
#                                     keemon.json is already correctly claimed
#                                     by our own "Keemon" card)
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


def slugify(name: str) -> str:
	return re.sub(r"[^a-z0-9]", "", name.lower())


def download(url: str, dest: Path) -> None:
	subprocess.run(["curl", "-sL", "-o", str(dest), url], check=True)


def fetch_digimon_json(slug: str) -> dict:
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
	LANG_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
	if LANG_CACHE_FILE.exists():
		lang = json.loads(LANG_CACHE_FILE.read_text(encoding="utf-8"))
	else:
		lang = fetch_json(LANG_URL)
		LANG_CACHE_FILE.write_text(json.dumps(lang), encoding="utf-8")

	prefix = "entity.thedigimod."
	return {k[len(prefix):]: v for k, v in lang.items() if k.startswith(prefix)}


def resolve_slug(clean_name: str, tier_key: str, implemented: set) -> str | None:
	"""Return the implemented slug for a card, or None if not in the mod.

	Only two ways to match: the Trello name slugified directly, or a manual
	CONFIRMED_ALIASES override. Deliberately NOT automatic beyond that - see
	suggest_slug_candidates() for why.
	"""
	direct = slugify(clean_name)
	if direct in implemented:
		return direct
	return CONFIRMED_ALIASES.get(clean_name)


def suggest_slug_candidates(clean_name: str, tier_key: str, implemented: set, lang_display: dict) -> list[str]:
	"""Suggest (never apply) implemented slugs that might be this card, by
	comparing the Trello name against every implemented digimon's actual
	in-game display name (en_us.json) - close matches only, gated by the
	evo_stage being valid for the card's tier.

	This is suggestion-only and intentionally not wired into in_mod: the mod
	has real duplicate/mislabeled lang entries (e.g. conomon.json's lang key
	incorrectly says "Cocomon", collidng with the actual separate baby
	digimon "Cocomon"), so even an exact name match here is not proof - it
	must be checked by hand and added to CONFIRMED_ALIASES once confirmed
	(see that dict's docstring for the two-signal check to run first).
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


def fetch_digimon_stats(slug: str, evolves_from_map: dict) -> dict:
	data = fetch_digimon_json(slug)

	evolutions = data.get("evolutions") or {}
	xp_drops = []
	for i in data.get("xps") or []:
		if isinstance(i, int) and 0 <= i < len(XP_ITEMS):
			item_slug, label = XP_ITEMS[i]
			xp_drops.append(
				{"label": label, "img": f"./src/assets/images/the_digimod/xp_items/{item_slug}.png"}
			)

	evo_stage = data.get("evo_stage")
	if isinstance(evo_stage, int) and 0 <= evo_stage < len(EVO_STAGE_LABELS):
		evo_stage = EVO_STAGE_LABELS[evo_stage]

	return {
		"entity_id": f"{MOD_ID}:{slug}",
		"profession": data.get("profession"),
		"diet": data.get("diet"),
		"evo_stage": evo_stage,
		"default_move": data.get("default_sp_move"),
		"xp_drops": xp_drops,
		"evolves_into": sorted(evolutions.keys()),
		"evolves_from": evolves_from_map.get(slug, []),
	}


def main() -> int:
	board = fetch_json(TRELLO_BOARD_URL)
	lists_by_name = {l["name"]: l["id"] for l in board["lists"]}

	implemented_entries = fetch_json(GITHUB_API_URL)
	implemented = {
		e["name"].removesuffix(".json")
		for e in implemented_entries
		if e["type"] == "file" and e["name"].endswith(".json")
	}
	implemented |= set(CONFIRMED_ALIASES.values())
	lang_display = fetch_lang_display_map()

	evolves_from_map = build_evolves_from_map(implemented)

	ROSTER_DIR.mkdir(parents=True, exist_ok=True)

	js_entries: list[dict] = []
	suggestion_notes: list[str] = []

	all_tier_titles = {key: title for key, title, _slug in TIER_LISTS}
	all_tier_titles[EXTRA_LIST_TIER_KEY] = EXTRA_LIST_TITLE
	group_order = [key for key, _t, _s in TIER_LISTS] + [EXTRA_LIST_TIER_KEY]

	def add_group(label_id: str, label: str, cards: list) -> list[str]:
		lines = [f'            <li id="{label_id}" class="mob-group-label">{html.escape(label)}</li>']
		for tier_key in group_order:
			tier_cards = [c for c in cards if c["tier_key"] == tier_key]
			if not tier_cards:
				continue
			lines.append(f'            <li class="mob-tier-label">{html.escape(all_tier_titles[tier_key])}</li>')
			for card in tier_cards:
				idx = len(js_entries)
				lines.append(f'            <li data-idx="{idx}">{html.escape(card["clean_name"])}</li>')
				js_entries.append(
					{"name": card["clean_name"], "img": card["img_rel_path"], "stats": card["stats"]}
				)
		return lines

	def process_card(card: dict, source_tier_key: str, source_tier_slug: str) -> dict | None:
		clean_name = clean_card_name(card["name"])
		resolved_slug = resolve_slug(clean_name, source_tier_key, implemented)
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
			"stats": fetch_digimon_stats(slug, evolves_from_map) if in_mod else None,
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

	list_lines = add_group("section-mobs-in-mod", "In The Mod", in_mod_cards)
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
