#!/usr/bin/env python3

"""Rebuild the digimon roster in td_lore.html from the Trello board + repo file list.

Sources: trello.com/b/Z5gjWmkN board JSON, and the digimon/ data folder in
themodderg/The-Digimod. Matching is exact-slug only; see CONFIRMED_ALIASES
below for known Trello/repo spelling mismatches.
"""

from pathlib import Path
import html
import json
import re
import subprocess
import sys
import urllib.request

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
TD_LORE_HTML = REPO_ROOT / "td_lore.html"
ROSTER_DIR = REPO_ROOT / "src/assets/images/the_digimod/roster"

TRELLO_BOARD_URL = "https://trello.com/b/Z5gjWmkN/the-digimod-needed-models.json"
GITHUB_API_URL = (
	"https://api.github.com/repos/themodderg/The-Digimod/contents/"
	"src/main/resources/data/thedigimod/digimon"
)

TIER_LISTS = [
	("Babies I in The Mod", "Babies I", "baby1"),
	("Babies II In The Mod", "Babies II", "baby2"),
	("Rookies In The Mod", "Rookies", "rookie"),
	("Champions In The Mod", "Champions", "champion"),
	("Ultimates In The Mod", "Ultimates", "ultimate"),
]

MAX_ICON_SIDE = 800

# Known Trello-vs-repo spelling mismatches confirmed as the same digimon.
# Add an entry here once you've confirmed it with the mod author instead of
# loosening the slug matcher to fuzzy-match everything.
CONFIRMED_ALIASES: dict[str, str] = {}


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

	ROSTER_DIR.mkdir(parents=True, exist_ok=True)

	js_entries: list[dict] = []

	def add_group(label_id: str, label: str, cards: list) -> list[str]:
		lines = [f'            <li id="{label_id}" class="mob-group-label">{html.escape(label)}</li>']
		for tier_key, tier_title, tier_slug in TIER_LISTS:
			tier_cards = [c for c in cards if c["tier_key"] == tier_key]
			if not tier_cards:
				continue
			lines.append(f'            <li class="mob-tier-label">{html.escape(tier_title)}</li>')
			for card in tier_cards:
				idx = len(js_entries)
				lines.append(f'            <li data-idx="{idx}">{html.escape(card["clean_name"])}</li>')
				js_entries.append({"name": card["clean_name"], "img": card["img_rel_path"]})
		return lines

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
			clean_name = clean_card_name(card["name"])
			slug = CONFIRMED_ALIASES.get(clean_name, slugify(clean_name))
			in_mod = slug in implemented

			cover_id = card.get("cover", {}).get("idAttachment")
			attachments = card.get("attachments", [])
			att = next((a for a in attachments if a["id"] == cover_id), None) or (
				attachments[0] if attachments else None
			)
			if not att:
				print(f"WARNING: no cover image for {card['name']!r}, skipping", file=sys.stderr)
				continue

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

			all_cards.append(
				{
					"tier_key": tier_key,
					"clean_name": clean_name,
					"img_rel_path": f"./src/assets/images/the_digimod/roster/{fname}",
					"in_mod": in_mod,
				}
			)

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
		"        { name: %r, img: %r }%s" % (e["name"], e["img"], "," if i < len(js_entries) - 1 else "")
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

	print(f"in_mod={len(in_mod_cards)} modeled={len(modeled_cards)} total={len(all_cards)}")
	unmatched_implemented = implemented - {slugify(c["clean_name"]) for c in in_mod_cards}
	if unmatched_implemented:
		print(
			f"NOTE: {len(unmatched_implemented)} implemented digimon have no matching Trello card "
			f"in the tier lists: {sorted(unmatched_implemented)}",
			file=sys.stderr,
		)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
