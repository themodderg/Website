#!/usr/bin/env python3

"""Build the Items section + one detail page per item for td_lore.html.

Sources: the mod's own item lang keys (item.thedigimod.* in en_us.json),
item/block model jsons (for icons - registry ids don't map 1:1 to texture
filenames), and the recipes/ folder (for Crafting sections). Everything
here comes straight from themodderg/The-Digimod on GitHub, cross-referenced
against the locally cached digimon jsons from sync_td_roster.py (default
move usage, implemented-species check for Digitama items).

Categorisation into the index groups (Digivices, Chips, Data, ...) is rule
based, not per-item guesswork: exact id sets for the few groups that don't
follow a naming prefix (Digivices, Drives, Food, Training Goods) were built
by hand-checking every one of the mod's 137 item lang entries against its
recipe file and display name once, then hardcoded below - not re-derived
every run, so future new items fall into "Misc" until someone checks and
files them the same way.
"""

from pathlib import Path
import html
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
TD_PAGES_DIR = REPO_ROOT / "pages" / "td"
TD_LORE_HTML = TD_PAGES_DIR / "td_lore.html"
ITEMS_DIR = REPO_ROOT / "src/assets/images/the_digimod/items"
XP_ITEMS_DIR = REPO_ROOT / "src/assets/images/the_digimod/xp_items"
VANILLA_DIR = REPO_ROOT / "src/assets/images/vanilla"
VANILLA_TEXTURES_SRC = Path.home() / "assets/assets/minecraft/textures"

MOD_ID = "thedigimod"
RAW_BASE = "https://raw.githubusercontent.com/themodderg/The-Digimod/main/src/main/resources"
LANG_URL = f"{RAW_BASE}/assets/thedigimod/lang/en_us.json"
RECIPES_API_URL = "https://api.github.com/repos/themodderg/The-Digimod/contents/src/main/resources/data/thedigimod/recipes"
RECIPE_URL_TMPL = f"{RAW_BASE}/data/thedigimod/recipes/{{name}}"
MODEL_URL_TMPL = f"{RAW_BASE}/assets/thedigimod/models/{{kind}}/{{name}}.json"
TEXTURE_URL_TMPL = f"{RAW_BASE}/assets/thedigimod/textures/{{path}}.png"

# Shared with sync_td_roster.py - reuse its lang cache and its 166 already
# fetched digimon jsons instead of re-downloading them.
DIGIMON_CACHE_DIR = Path(__file__).resolve().parent / ".td_digimon_cache"
LANG_CACHE_FILE = DIGIMON_CACHE_DIR / "_lang.json"

ITEMS_CACHE_DIR = Path(__file__).resolve().parent / ".td_items_cache"
MODEL_CACHE_DIR = ITEMS_CACHE_DIR / "models"
RECIPE_CACHE_DIR = ITEMS_CACHE_DIR / "recipes"

MAX_ICON_SIDE = 300

EVO_STAGE_LABELS = ["Baby I", "Baby II", "Rookie", "Champion", "Perfect", "Ultimate"]

# Same 9 attribute Data items as sync_td_roster.py's XP_ITEMS (labels only,
# needed here to name the attribute a Data/Data Pack/advanced Training Good
# is tied to - kept in sync by hand since it's a fixed, mod-defined list).
XP_ITEMS = [
	("dragon_data", "Dragon Data"), ("beast_data", "Beast Data"), ("plantinsect_data", "Plant/Insect Data"),
	("aquan_data", "Aquan Data"), ("wind_data", "Wind Data"), ("machine_data", "Machine Data"),
	("earth_data", "Earth Data"), ("nightmare_data", "Nightmare Data"), ("holy_data", "Holy Data"),
]

# ---------------------------------------------------------------------------
# Categorisation

DIGIVICE_IDS = {
	"digivice", "digivice01", "digivice2020", "digivice_burst", "digivice_ic",
	"d3", "darc", "dscanner", "dstorage", "vpet", "xross_loader", "vitalbracelet",
}
DRIVE_IDS = {"gbattack", "gbdefence", "gbspattack", "gbspdefence", "health_drives", "battles_chip"}
FOOD_IDS = {
	"digi_cake", "digi_meat", "digi_meat_big", "digi_meat_rotten", "digi_ribs",
	"digi_sushi", "poop", "gold_poop", "guilmon_bread",
}
# update_item IS a real TDItems.java training good (SpawnGoodItem -> InitGoods.UPDATE_GOOD,
# stat "health") - not to be confused with health_drives (TDItemsAdmin.java, MAX_MEGA debug
# item). goblimon_bat/tamer_leash/boss_cube are TDItemsAdmin.java debug tools, not training
# goods - they fall through to "misc" below and get flagged via CREATIVE_ONLY_IDS.
TRAINING_IDS = {
	"bag_item", "ball_good", "clown_box", "dragon_bone", "flytrap_good",
	"lira_good", "m2_disk_item", "old_pc", "red_freezer",
	"shield_item", "table_item", "target_item", "training_bag", "training_rock",
	"wind_vane", "update_item",
}

# Training-good items that are NOT SpawnGoodItems - they don't place a
# trainable entity when used. training_bag is a ContainerItem starter bundle
# (see TDItems.java line 73) that just hands the player one of each of the 5
# basic goods. All 16 items appear in the top Items TOC either way; this set
# is what the standalone Training Good Entities section under Blocks EXCLUDES,
# since a bundle has no entity form.
TRAINING_ITEM_ONLY_IDS = {"training_bag"}

# item_id -> registered entity id (from InitGoods.java's GOODS.register()
# calls, matched to TDItems.java's SpawnGoodItem constructor's first arg).
# Used to look up "entity.thedigimod.<id>" lang entries so the entity
# section can show the entity's own display name when it differs from the
# item's (e.g. target_item item = "Target", but its entity = "Training Target").
TRAINING_ITEM_TO_ENTITY = {
	"bag_item": "punching_bag",
	"target_item": "target",
	"table_item": "defence_table",
	"shield_item": "shield",
	"update_item": "update",
	"dragon_bone": "dragon_bone",
	"ball_good": "ball_good",
	"flytrap_good": "flytrap_good",
	"red_freezer": "red_freezer",
	"wind_vane": "wind_vane",
	"old_pc": "old_pc",
	"training_rock": "training_rock",
	"clown_box": "clown_box",
	"lira_good": "lira_good",
	"m2_disk_item": "m2_disk",
}

# Real per-good stat + tier, read straight from TDItems.java's SpawnGoodItem
# constructor calls (3rd arg) and InitGoods.java's .setStatMultiplier(1.5f)/
# .setXpId(n) calls - not guessed from the item name.
TRAINING_STAT_MAP = {
	"bag_item": "Attack", "table_item": "Sp. Defense", "target_item": "Sp. Attack",
	"shield_item": "Defense", "update_item": "Health",
	"dragon_bone": "Attack", "ball_good": "Attack", "clown_box": "Sp. Attack",
	"flytrap_good": "Sp. Defense", "old_pc": "Defense", "lira_good": "Sp. Defense",
	"red_freezer": "Sp. Attack", "wind_vane": "Sp. Attack", "training_rock": "Defense",
	"m2_disk_item": "Health",
}
TRAINING_ADVANCED_IDS = {
	"dragon_bone", "ball_good", "clown_box", "flytrap_good", "old_pc",
	"lira_good", "red_freezer", "wind_vane", "training_rock", "m2_disk_item",
}
# item id -> XP_ITEMS index it has a chance of granting while training (InitGoods.java .setXpId()).
TRAINING_XP_MAP = {
	"dragon_bone": 0, "ball_good": 1, "flytrap_good": 2, "red_freezer": 3,
	"wind_vane": 4, "old_pc": 5, "training_rock": 6, "clown_box": 7, "lira_good": 8,
}

# Registered under TDItemsAdmin.java's CREATIVE_ITEMS registry (confirmed by
# reading the mod's Java source) - real items, but with no recipe, loot table,
# or mob drop anywhere in the mod's data, so unobtainable in normal survival
# play. Unlike admin_logo (excluded entirely - it's not in any item group,
# just the creative tab's own icon), these do exist as real, usable items;
# they're kept and flagged rather than removed.
CREATIVE_ONLY_IDS = {
	"dragon_data", "beast_data", "plantinsect_data", "aquan_data", "wind_data",
	"machine_data", "earth_data", "nightmare_data", "holy_data", "poop_data",
	"dragon_pack", "beast_pack", "plantinsect_pack", "aquan_pack", "wind_pack",
	"machine_pack", "earth_pack", "nightmare_pack", "holy_pack", "poop_pack",
	"gbattack", "gbdefence", "gbspattack", "gbspdefence", "health_drives",
	"battles_chip", "goblimon_bat", "tamer_leash", "boss_cube",
}

CATEGORY_META = {
	"digivices": ("Digivices", "Digivice"),
	"chips": ("Special Attack Chips", "Special Attack Chip"),
	"data": ("Data (XP Items)", "Data"),
	"data_packs": ("Data Packs", "Data Pack"),
	"bytes": ("Stat Bytes", "Stat Byte"),
	"drives": ("Stat Drives", "Stat Drive"),
	"digitama": ("Digitama", "Digitama"),
	"training": ("Training Goods", "Training Good"),
	"food": ("Food & Care", "Food / Care Item"),
	"misc": ("Misc", "Misc"),
}
CATEGORY_ORDER = ["digivices", "chips", "data", "data_packs", "bytes", "drives", "digitama", "training", "food", "misc"]

# Lang entries that aren't a real, player-obtainable item - confirmed by
# ModderG (mod author): admin_logo is only the icon item for the
# "digiadmin_tab" creative-mode tab (itemGroup.digiadmin_tab), not something
# players can get in survival. Skip these entirely rather than list them.
EXCLUDED_ITEM_IDS = {
	"admin_logo",
	# Duplicate lang entry for "Bubbmon Digitama" (same display name as the
	# real `bubbmon` item). No matching baby digimon json / entity exists, so
	# the item has no working spawn behavior - skip it rather than render a
	# phantom second Bubbmon in the Digitama listing.
	"bubbmonk",
}


def categorize(item_id: str, lang_name: str) -> str:
	if item_id in DIGIVICE_IDS:
		return "digivices"
	if item_id.startswith("chip_"):
		return "chips"
	if item_id.endswith("_data"):
		return "data"
	if item_id.endswith("_pack"):
		return "data_packs"
	if item_id.startswith("byte"):
		return "bytes"
	if item_id in DRIVE_IDS:
		return "drives"
	if lang_name.endswith("Digitama"):
		return "digitama"
	if item_id in FOOD_IDS:
		return "food"
	if item_id in TRAINING_IDS:
		return "training"
	return "misc"


# ---------------------------------------------------------------------------
# Fetch / cache plumbing

def fetch_json(url: str) -> dict | None:
	req = urllib.request.Request(url, headers={"User-Agent": "codderg-wiki-sync"})
	try:
		with urllib.request.urlopen(req) as resp:
			return json.loads(resp.read())
	except urllib.error.HTTPError as e:
		if e.code == 404:
			return None
		raise


def download(url: str, dest: Path) -> bool:
	result = subprocess.run(["curl", "-sfL", "-o", str(dest), url])
	if result.returncode != 0:
		dest.unlink(missing_ok=True)
		return False
	return True


def fetch_lang_map() -> dict:
	LANG_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
	if LANG_CACHE_FILE.exists():
		lang = json.loads(LANG_CACHE_FILE.read_text(encoding="utf-8"))
	else:
		lang = fetch_json(LANG_URL)
		LANG_CACHE_FILE.write_text(json.dumps(lang), encoding="utf-8")
	# If a local mod checkout is available, overlay its lang on top of the
	# remote cache - new items that haven't been pushed to GitHub yet (e.g.
	# recently added Digitama species) get picked up without waiting for a
	# manual cache flush.
	local_lang = Path.home() / "raid/mods/digimods/digimod/src/main/resources/assets/thedigimod/lang/en_us.json"
	if local_lang.is_file():
		try:
			lang = {**lang, **json.loads(local_lang.read_text(encoding="utf-8"))}
		except json.JSONDecodeError:
			pass
	return lang


LOCAL_MOD_ROOT = Path.home() / "raid/mods/digimods/digimod"
LOCAL_MOD_ASSETS = LOCAL_MOD_ROOT / "src/main/resources/assets/thedigimod"


def fetch_model(kind: str, name: str) -> dict | None:
	MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
	cache_file = MODEL_CACHE_DIR / f"{kind}_{name}.json"
	if cache_file.exists():
		text = cache_file.read_text(encoding="utf-8")
		if text != "null":
			return json.loads(text)
		# Cached "null" from a prior remote miss - retry from local first
		# so items added after the last remote fetch still resolve.
	local_path = LOCAL_MOD_ASSETS / "models" / kind / f"{name}.json"
	if local_path.is_file():
		try:
			data = json.loads(local_path.read_text(encoding="utf-8"))
			cache_file.write_text(json.dumps(data), encoding="utf-8")
			return data
		except json.JSONDecodeError:
			pass
	if cache_file.exists():
		return None
	data = fetch_json(MODEL_URL_TMPL.format(kind=kind, name=name))
	cache_file.write_text(json.dumps(data), encoding="utf-8")
	return data


def resolve_texture(name: str) -> str | None:
	"""Find the texture id (e.g. 'item/ball_good') backing a thedigimod item
	or block id, without assuming the registry id matches the filename."""
	m = fetch_model("item", name)
	if m:
		tex = (m.get("textures") or {}).get("layer0")
		if tex:
			return tex.removeprefix(f"{MOD_ID}:")
		parent = m.get("parent", "")
		if parent.startswith(f"{MOD_ID}:block/"):
			name = parent.split("/", 1)[1]
	m2 = fetch_model("block", name)
	if m2:
		textures = m2.get("textures") or {}
		for key in ("all", "top", "side", "front", "texture"):
			if key in textures:
				return textures[key].removeprefix(f"{MOD_ID}:")
		if textures:
			return next(iter(textures.values())).removeprefix(f"{MOD_ID}:")
	return None


_icon_cache: dict[str, str | None] = {}


def get_thedigimod_icon(name: str) -> str | None:
	"""Download (once per run) the icon for a thedigimod item/block id into
	ITEMS_DIR, return its site-relative path or None if unresolvable."""
	if name in _icon_cache:
		return _icon_cache[name]
	dest = ITEMS_DIR / f"{name}.png"
	rel = f"./src/assets/images/the_digimod/items/{name}.png"
	if dest.exists():
		_icon_cache[name] = rel
		return rel
	texture = resolve_texture(name)
	if not texture:
		print(f"WARNING: no resolvable texture for thedigimod:{name}", file=sys.stderr)
		_icon_cache[name] = None
		return None
	ITEMS_DIR.mkdir(parents=True, exist_ok=True)
	raw = dest.with_suffix(".raw")
	local_texture = LOCAL_MOD_ASSETS / "textures" / f"{texture}.png"
	if local_texture.is_file():
		raw.write_bytes(local_texture.read_bytes())
	elif not download(TEXTURE_URL_TMPL.format(path=texture), raw):
		print(f"WARNING: texture download failed for thedigimod:{name} ({texture})", file=sys.stderr)
		_icon_cache[name] = None
		return None
	im = Image.open(raw).convert("RGBA")
	w, h = im.size
	if h > w and h % w == 0:
		# Animated item texture (Minecraft's stacked-frames convention, paired
		# with a .png.mcmeta) - use the first frame (top square) as the icon.
		im = im.crop((0, 0, w, w))
		w, h = im.size
	scale = MAX_ICON_SIDE / max(w, h)
	if scale < 1:
		im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
	im.save(dest, "PNG", optimize=True)
	raw.unlink()
	_icon_cache[name] = rel
	return rel


VANILLA_LABEL_OVERRIDES = {
	"milk_bucket": "Milk Bucket", "slime_ball": "Slime Ball", "iron_ingot": "Iron Ingot",
	"iron_nugget": "Iron Nugget", "copper_ingot": "Copper Ingot", "dried_kelp": "Dried Kelp",
	"flower_pot": "Flower Pot", "name_tag": "Name Tag",
}


def ensure_vanilla_icon(name: str) -> str | None:
	dest = VANILLA_DIR / f"{name}.png"
	rel = f"./src/assets/images/vanilla/{name}.png"
	if dest.exists():
		return rel
	for sub in ("item", "block"):
		src = VANILLA_TEXTURES_SRC / sub / f"{name}.png"
		if src.exists():
			VANILLA_DIR.mkdir(parents=True, exist_ok=True)
			dest.write_bytes(src.read_bytes())
			return rel
	print(f"WARNING: no local vanilla texture found for minecraft:{name}", file=sys.stderr)
	return None


# Tag ingredients don't resolve to a single item - give each a representative
# icon/label by hand instead of guessing which concrete item was meant.
TAG_OVERRIDES = {
	"minecraft:planks": ("Any Planks", lambda: ensure_vanilla_icon("oak_planks")),
	"minecraft:logs": ("Any Log", lambda: ensure_vanilla_icon("oak_log")),
	f"{MOD_ID}:babies/babies": ("Any Baby I Digimon Digitama", lambda: get_thedigimod_icon("botamon")),
}


def ingredient_icon(ref: dict, item_lang: dict, block_lang: dict) -> tuple[str, str | None, str | None]:
	"""Return (label, icon relpath or None, link href or None)."""
	if "tag" in ref:
		tag = ref["tag"]
		if tag in TAG_OVERRIDES:
			label, icon_fn = TAG_OVERRIDES[tag]
			return label, icon_fn(), None
		return tag.split(":")[-1].split("/")[-1].replace("_", " ").title(), None, None
	item_id_full = ref["item"]
	if item_id_full.startswith("minecraft:"):
		name = item_id_full.split(":", 1)[1]
		label = VANILLA_LABEL_OVERRIDES.get(name, name.replace("_", " ").title())
		return label, ensure_vanilla_icon(name), None
	name = item_id_full.split(":", 1)[1]
	label = item_lang.get(name) or block_lang.get(name) or name.replace("_", " ").title()
	# Only link to ids that actually get their own td_item_<id>.html page -
	# real player-obtainable items, minus the excluded creative-only ones.
	href = f"./td_item_{name}.html" if name in item_lang and name not in EXCLUDED_ITEM_IDS else None
	return label, get_thedigimod_icon(name), href


def recipe_td_ingredients(recipe: dict) -> set[str]:
	"""Return the set of thedigimod item ids referenced as ingredients in a recipe."""
	refs: list[dict] = []
	rtype = recipe.get("type", "")
	if rtype == "minecraft:crafting_shaped":
		refs.extend(recipe.get("key", {}).values())
	elif rtype == "minecraft:crafting_shapeless":
		refs.extend(recipe.get("ingredients", []))
	elif rtype in ("minecraft:smelting", "minecraft:blasting"):
		ing = recipe.get("ingredient")
		if isinstance(ing, list):
			refs.extend(ing)
		elif isinstance(ing, dict):
			refs.append(ing)
	out: set[str] = set()
	for ref in refs:
		if not isinstance(ref, dict):
			continue
		item_id_full = ref.get("item", "")
		if item_id_full.startswith(f"{MOD_ID}:"):
			out.add(item_id_full.split(":", 1)[1])
	return out


def fetch_recipes() -> dict[str, dict]:
	"""result item id (no namespace) -> recipe dict, thedigimod items only."""
	listing = fetch_json(RECIPES_API_URL) or []
	by_result: dict[str, dict] = {}
	seen_names: set[str] = set()
	for entry in listing:
		if entry["type"] != "file" or not entry["name"].endswith(".json"):
			continue
		seen_names.add(entry["name"])
		cache_file = RECIPE_CACHE_DIR / entry["name"]
		RECIPE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
		if cache_file.exists():
			data = json.loads(cache_file.read_text(encoding="utf-8"))
		else:
			data = fetch_json(RECIPE_URL_TMPL.format(name=entry["name"]))
			cache_file.write_text(json.dumps(data), encoding="utf-8")
		result = data.get("result")
		result_item = result if isinstance(result, str) else (result or {}).get("item", "")
		if result_item.startswith(f"{MOD_ID}:"):
			by_result[result_item.split(":", 1)[1]] = data
	# Overlay recipes from the local mod source - new/updated recipes not yet
	# on GitHub main still land in the wiki. Locals win over remote.
	local_recipes_dir = LOCAL_MOD_ROOT / "src/main/resources/data/thedigimod/recipes"
	if local_recipes_dir.is_dir():
		for f in local_recipes_dir.glob("*.json"):
			try:
				data = json.loads(f.read_text(encoding="utf-8"))
			except json.JSONDecodeError:
				continue
			result = data.get("result")
			result_item = result if isinstance(result, str) else (result or {}).get("item", "")
			if result_item.startswith(f"{MOD_ID}:"):
				by_result[result_item.split(":", 1)[1]] = data
	return by_result


# ---------------------------------------------------------------------------
# Cross-references against the locally cached digimon jsons (from
# sync_td_roster.py) - default move usage and implemented-species check.

def load_digimon_cache() -> dict[str, dict]:
	out = {}
	if not DIGIMON_CACHE_DIR.exists():
		return out
	for f in DIGIMON_CACHE_DIR.glob("*.json"):
		if f.name == "_lang.json":
			continue
		try:
			out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
		except json.JSONDecodeError:
			continue
	# The remote-fetched cache drops "egg_type" (the field the mod uses to
	# group babies by shared egg icon in the creative tab). If a local mod
	# source is available, merge it in so we can sort Digitama items by egg
	# type to mirror the in-game grouping.
	local_dir = Path.home() / "raid/mods/digimods/digimod/src/main/resources/data/thedigimod/digimon"
	if local_dir.is_dir():
		for f in local_dir.glob("*.json"):
			try:
				local = json.loads(f.read_text(encoding="utf-8"))
			except json.JSONDecodeError:
				continue
			entry = out.setdefault(f.stem, {})
			for k in ("egg_type", "xps", "evo_stage"):
				if k in local and k not in entry:
					entry[k] = local[k]
	return out


def mob_link(slug: str, name: str) -> str:
	"""Link to a Digimon's entry in the td_lore.html roster (see the
	showFromHash() deep-link handler in that page's inline script)."""
	return f'<a href="./td_lore.html#mob-{slug}" class="wiki-link">{html.escape(name)}</a>'


def build_move_usage(digimon_cache: dict, entity_lang: dict) -> dict[str, list[tuple[str, str]]]:
	"""default move -> sorted list of (slug, display name) tuples."""
	by_move: dict[str, list[tuple[str, str]]] = {}
	for slug, data in digimon_cache.items():
		move = data.get("default_sp_move")
		if move:
			by_move.setdefault(move, []).append((slug, entity_lang.get(slug, slug)))
	return {k: sorted(v, key=lambda t: t[1]) for k, v in by_move.items()}


# ---------------------------------------------------------------------------
# Usage prose - category-general templates, with per-item overrides only
# where the mod's own FAQ prose / evolution / recipe data pins down a more
# specific mechanic. Anything not traceable to real data says so plainly.

SPECIAL_USAGE: dict[str, list[str]] = {
	"black_digitron": [
		'Interact with a Digimon that has a dark counterpart while holding this item to trigger '
		'<a href="./td_lore.html#evo-digitron" class="wiki-link">slide evolution</a> into that dark form.'
	],
	"dark_tower_shard": [
		'Exposing a Digimon to this item <a href="./td_lore.html#evo-digitron" class="wiki-link">de-evolves</a> '
		"it to a previous evolution stage."
	],
	"digi_core": [
		"Restores one of the Digimon's 3 lives when used - see "
		'<a href="./td_lore.html#faq-mistakes" class="wiki-link">Lifes &amp; Care Mistakes</a>.'
	],
	"digi_memory": [
		"Used from the Digivice command menu to convert a partner Digimon into a storable item form - see "
		'<a href="./td_lore.html#faq-commands" class="wiki-link">Commands</a>.'
	],
	"blue_card": ["A common crafting reagent used across most of the Training Goods' recipes."],
	"training_bag": [
		'A starter bundle containing one each of the 5 basic Training Goods - '
		'<a href="./td_item_table_item.html" class="wiki-link">Learning Table</a>, '
		'<a href="./td_item_bag_item.html" class="wiki-link">Punching Bag</a>, '
		'<a href="./td_item_shield_item.html" class="wiki-link">Training Shield</a>, '
		'<a href="./td_item_target_item.html" class="wiki-link">Target</a> and '
		'<a href="./td_item_update_item.html" class="wiki-link">Health Upgrade</a>. Given to newly joined players '
		'by default (configurable).'
	],
	"digimon_card": ["A crafting reagent used in most Digivice recipes."],
	"chrondigizoit": [
		'Smelted from <a href="./td_item_huanglong_ore.html" class="wiki-link">Huanglong Ore</a>; further smelted '
		'into <a href="./td_item_chrome_digizoid.html" class="wiki-link">Chrome Digizoid</a>. Also a crafting '
		"reagent for several Digivice recipes."
	],
	"chrome_digizoid": [
		"The final product of the Huanglong Ore &rarr; Chrondigizoit &rarr; Chrome Digizoid smelting chain. "
		"Required in stacks of 10 by several evolution conditions (e.g. Tyrannomon &rarr; MetalTyrannomon, "
		"Greymon &rarr; MetalGreymon, Gabumon &rarr; Garurumon(Black), Growlmon &rarr; MegaloGrowmon)."
	],
	"huanglong_ore": [
		'The raw ore form, smelted into <a href="./td_item_chrondigizoit.html" class="wiki-link">Chrondigizoit</a>.'
	],
	"tamer_leash": ["Right-clicking an untamed Digimon with this item tames it to the player (like a vanilla Lead)."],
	"boss_cube": [
		"Right-clicking a Digimon with this item turns it into a Boss variant, playing the level-up/XP sound cues."
	],
	"goblimon_bat": [
		"Right-clicking a Digimon with this item adds one care mistake to it - see "
		'<a href="./td_lore.html#faq-mistakes" class="wiki-link">Lifes &amp; Care Mistakes</a>.'
	],
	"poop": [
		"Produced automatically when a fed Digimon defecates - see "
		'<a href="./td_lore.html#faq-poop" class="wiki-link">Why Is My Digimon Purple?</a>.'
	],
	"gold_poop": [
		'A rarer variant of <a href="./td_item_poop.html" class="wiki-link">Digi Poop</a> - see '
		'<a href="./td_lore.html#faq-poop" class="wiki-link">Why Is My Digimon Purple?</a>.'
	],
	"poop_data": [
		"The 10th Data (XP Item), tied to the Poop attribute. Right-clicking a Digimon with it grants one unit of "
		"Poop-attribute experience - the same XP type shown on Poop-attribute Digimon's stats as an \"XP Drop\". "
		"Only Poop-attribute Digimon benefit from it."
	],
	"battles_chip": [
		"Right-clicking a Digimon with this item adds 5 to its battle-win count. Several evolution routes require "
		'a minimum number of wins - see <a href="./td_lore.html#evo-conds" class="wiki-link">'
		"Evolving Into The Correct Digimon</a>."
	],
}

# Debug variants of the 5 Byte stats (TDItemsAdmin.java, StatUpItem with
# DigimonEntity.MAX_MEGA = 999) - instantly maxes the stat instead of the
# Bytes' small fixed amount.
DRIVE_GENERIC_STATS = {
	"gbattack": "Attack", "gbdefence": "Defense", "gbspattack": "Sp. Attack",
	"gbspdefence": "Sp. Defense", "health_drives": "Health",
}


def usage_paragraphs(item_id: str, category: str, lang_name: str, move_usage: dict, digimon_cache: dict, entity_lang: dict) -> list[str]:
	if item_id in SPECIAL_USAGE:
		return list(SPECIAL_USAGE[item_id])

	if category == "digivices":
		return [
			"One of the mod's Digivice items - interact with a partner Digimon to open its GUI and check stats, "
			'evolution routes, and issue commands. See <a href="./td_lore.html#faq-digivices" class="wiki-link">'
			"Digivices</a>. The different Digivice models share the same functionality."
		]

	if category == "chips":
		# Usage stays intentionally short - the "who uses it / how do I get one"
		# info lives in the infobox ("Used By") and the Obtaining section, so we
		# don't repeat the mob list here.
		return [
			"A Special Attack Chip - feeding it to a Digimon teaches it as a move. See "
			'<a href="./td_lore.html#faq-moves" class="wiki-link">Speciall Attack Chips</a>.'
		]

	if category == "data":
		attr = lang_name.removesuffix(" Data")
		return [
			f"One of the 9 attribute-tagged Data items ({attr} attribute). Right-clicking a Digimon with it "
			f"directly grants that Digimon {attr} experience (the same XP type shown on its stats as an "
			"\"XP Drop\"). Wild Digimon grant this XP directly on defeat rather than dropping the physical item."
		]

	if category == "data_packs":
		attr = lang_name.removesuffix(" Pack")
		return [
			f"A bulk, 9-charge version of the {attr} Data item. Each right-click on a Digimon consumes one charge "
			f"and grants a unit of {attr} experience, for 9 total uses before the item is consumed."
		]

	if category == "bytes":
		stat = lang_name.removesuffix(" Byte")
		# Drop info belongs in Obtaining, not Usage.
		return [f"Directly raises a Digimon's {stat} stat when used."]

	if category == "drives" and item_id in DRIVE_GENERIC_STATS:
		stat = DRIVE_GENERIC_STATS[item_id]
		return [f"A debug variant of the {stat} Byte: right-clicking a Digimon with it instantly sets the stat to 999, instead of adding the Byte's small fixed amount."]

	if category == "digitama":
		species = lang_name.removesuffix(" Digitama")
		implemented = item_id in digimon_cache
		mob = mob_link(item_id, entity_lang.get(item_id, species)) if implemented else html.escape(species)
		return [
			f"Right-click on a block to spawn a tamed {mob} at that location, similar to a vanilla spawn egg "
			"but with the resulting Digimon already tamed by the user. The item is consumed on use, and plays "
			"the turtle-egg hatch sound."
		]

	if category == "training":
		stat = TRAINING_STAT_MAP.get(item_id)
		if not stat:
			# training_bag has its own SPECIAL_USAGE entry (bundle item) and never
			# reaches this branch; this is just a safety net for anything else.
			return [
				"One of the mod's Training Goods - place it and have a partner Digimon target/hit it during "
				'training. See <a href="./td_lore.html#faq-goods" class="wiki-link">Trainning Goods</a>.'
			]
		if item_id in TRAINING_ADVANCED_IDS:
			bonus = ""
			xp_idx = TRAINING_XP_MAP.get(item_id)
			if xp_idx is not None:
				attr = XP_ITEMS[xp_idx][1].removesuffix(" Data")
				bonus = f", with a small chance of also granting {attr} Data while training"
			return [
				f"An advanced Training Good - place it and have a partner Digimon target/hit it to raise its "
				f"{stat} stat by a larger amount than a basic Training Good{bonus}. See "
				'<a href="./td_lore.html#faq-advanced-goods" class="wiki-link">Advanced Goods</a>.'
			]
		return [
			f"A basic Training Good - place it and have a partner Digimon target/hit it to raise its {stat} stat. "
			'See <a href="./td_lore.html#faq-goods" class="wiki-link">Trainning Goods</a>.'
		]

	if category == "food":
		return [
			"A food/care item. Digimon have individual diet preferences ranked in the Digivice GUI - see "
			'<a href="./td_lore.html#faq-diet" class="wiki-link">What Do I Feed My Digimon?</a>.'
		]

	return ["Its exact function isn't specified beyond its name and model in the mod's data."]


# ---------------------------------------------------------------------------
# Recipe rendering

def render_recipe_section(item_id: str, display_name: str, icon_rel: str, recipe: dict, item_lang: dict, block_lang: dict) -> str:
	rtype = recipe["type"]
	cells: list[tuple[str, str | None, str | None] | None] = [None] * 9
	note = None

	if rtype == "minecraft:crafting_shaped":
		pattern = recipe["pattern"]
		key = recipe.get("key", {})
		for r, row in enumerate(pattern):
			for c, ch in enumerate(row):
				if ch == " " or ch not in key:
					continue
				cells[r * 3 + c] = ingredient_icon(key[ch], item_lang, block_lang)
	elif rtype == "minecraft:crafting_shapeless":
		for i, ref in enumerate(recipe.get("ingredients", [])[:9]):
			cells[i] = ingredient_icon(ref, item_lang, block_lang)
		note = "Shapeless recipe: the ingredients can go in any slots."
	elif rtype in ("minecraft:smelting", "minecraft:blasting"):
		ref = recipe["ingredient"]
		ref = ref[0] if isinstance(ref, list) else ref
		cells[0] = ingredient_icon(ref, item_lang, block_lang)
		furnace = "blast furnace" if rtype == "minecraft:blasting" else "furnace"
		note = f"Smelted in a {furnace}."
	else:
		return ""

	cell_html = []
	for cell in cells:
		if cell is None:
			cell_html.append('            <div class="recipe-cell"></div>')
		else:
			label, img, href = cell
			inner = f'<img src="{img}" alt="{html.escape(label)}">' if img else html.escape(label[:1])
			if href:
				inner = f'<a href="{href}">{inner}</a>'
			cell_html.append(
				f'            <div class="recipe-cell recipe-cell-filled" title="{html.escape(label)}">{inner}</div>'
			)

	result = recipe.get("result")
	count = result.get("count", 1) if isinstance(result, dict) else 1
	count_html = f'<span class="recipe-count">{count}</span>' if count and count > 1 else ""

	legend_items = {}
	for cell in cells:
		if cell:
			label, img, href = cell
			legend_items[label] = (img, href)
	legend_lines = []
	for label, (img, href) in sorted(legend_items.items()):
		icon_tag = f'<img src="{img}" alt="" class="recipe-legend-icon">' if img else ""
		text = f'<a href="{href}" class="wiki-link">{html.escape(label)}</a>' if href else html.escape(label)
		legend_lines.append(f"          <li>{icon_tag} {text}</li>")
	legend_html = "\n".join(legend_lines)

	note_html = f'\n        <p class="recipe-note">{note}</p>' if note else ""

	return f"""      <section id="crafting" class="lore-box lore-section">
        <h2 class="lore-section-title">Crafting</h2>
        <div class="lore-section-body recipe-body">
          <div class="recipe-grid">
{chr(10).join(cell_html)}
          </div>

          <div class="recipe-arrow"><i class="fa-solid fa-arrow-right"></i></div>

          <div class="recipe-result">
            <div class="recipe-cell recipe-cell-filled recipe-cell-result">
              <img src="{icon_rel}" alt="{html.escape(display_name)}">
              {count_html}
            </div>
          </div>
        </div>{note_html}

        <ul class="recipe-legend">
{legend_html}
        </ul>
      </section>
"""


USED_IN_SECTION_RE = re.compile(
	r'[ \t]*<section id="crafting-material-for"[^>]*>.*?</section>\n?',
	re.DOTALL,
)
USED_IN_TOC_RE = re.compile(
	r'[ \t]*<li><a href="#crafting-material-for"[^>]*>.*?</li>\n?',
	re.DOTALL,
)


def patch_used_in_section(page_html: str, entries: list[tuple[str, str, str | None]]) -> str:
	"""Replace (or insert / remove) the 'Material for' section + TOC
	entry on an existing item page without touching any other section."""
	# Strip previous version wherever it landed.
	page_html = USED_IN_SECTION_RE.sub("", page_html)
	page_html = USED_IN_TOC_RE.sub("", page_html)
	if not entries:
		return page_html

	section = render_used_in_section(entries)
	# Insert before the closing </div> of the wiki-detail column - the same
	# anchor generate_item_page uses.
	detail_marker = 'class="w-full xl:w-[70vw] wiki-detail"'
	d_idx = page_html.find(detail_marker)
	ad_marker = '    <div class="hidden xl:block ad-sidebar">'
	a_idx = page_html.find(ad_marker, d_idx) if d_idx != -1 else -1
	if d_idx != -1 and a_idx != -1:
		before = page_html[:a_idx]
		close_idx = before.rfind("    </div>")
		if close_idx != -1 and close_idx > d_idx:
			page_html = before[:close_idx] + section + before[close_idx:] + page_html[a_idx:]

	# TOC entry: append after the last <li>...</li> inside the item-toc <ul>.
	toc_start = page_html.find('<ul class="mod-content-list"')
	if toc_start != -1:
		toc_end = page_html.find("</ul>", toc_start)
		if toc_end != -1:
			last_li = page_html.rfind("</li>", toc_start, toc_end)
			if last_li != -1:
				toc_li = (
					'\n            <li><a href="#crafting-material-for" class="mod-content-link">'
					'<span class="mod-content-bullet"></span>'
					'<span>Material for</span></a></li>'
				)
				after = last_li + len("</li>")
				page_html = page_html[:after] + toc_li + page_html[after:]
	return page_html


def render_used_in_section(entries: list[tuple[str, str, str | None]]) -> str:
	"""entries: sorted list of (item_id, display_name, icon_rel)."""
	if not entries:
		return ""
	lines = []
	for iid, name, icon in entries:
		icon_tag = f'<img src="{icon}" alt="" class="recipe-legend-icon"> ' if icon else ""
		lines.append(
			f'            <li>{icon_tag}<a href="./td_item_{iid}.html" class="wiki-link">{html.escape(name)}</a></li>'
		)
	return (
		'      <section id="crafting-material-for" class="lore-box lore-section">\n'
		'        <h2 class="lore-section-title">Material for</h2>\n'
		'        <div class="lore-section-body">\n'
		'          <ul class="recipe-legend">\n'
		+ "\n".join(lines) + "\n"
		'          </ul>\n'
		'        </div>\n'
		'      </section>\n'
	)


# ---------------------------------------------------------------------------
# Page generation

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">

<head>
  <script data-cfasync="false" src="https://cmp.gatekeeperconsent.com/min.js"></script>
  <script data-cfasync="false" src="https://the.gatekeeperconsent.com/cmp.min.js"></script>
  <script async src="//www.ezojs.com/ezoic/sa.min.js"></script>
  <script>
    window.ezstandalone = window.ezstandalone || {{}};
    ezstandalone.cmd = ezstandalone.cmd || [];
  </script>
  <script src="//ezoicanalytics.com/analytics.js"></script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} | The Digimod Wiki</title>

  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-2592338544514821"
    crossorigin="anonymous"></script>

  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

  <link rel="stylesheet" href="./src/css/sections.css">
  <link rel="icon" type="image/png" href="src/assets/images/logo.png">
</head>

<body>
  <section class="hero">
    <div class="hero-row">
      <a href="./td_lore.html" class="hero-logo-link" title="Back to The Digimod">
        <img class="hero-logo" src="./src/assets/images/the_digimod/Logo.png" alt="The Digimod">
      </a>
      <div class="hero-badges hero-badges-right">
        <div class="hero-badge-card hero-badge-card-java">
          <span class="hero-badge-icon"><i class="fa-brands fa-java"></i></span>
          <span class="hero-badge-copy">
            <span class="hero-badge-title">Java</span>
            <span class="hero-badge-subtitle">Edition</span>
          </span>
        </div>
        <a class="hero-badge-card hero-badge-card-curseforge" href="https://www.curseforge.com/minecraft/mc-mods/the-digimod-beta" target="_blank"
          data-count-url="https://img.shields.io/curseforge/dt/910169?logo=curseforge&amp;logoColor=eb622b&amp;labelColor=101013&amp;color=eb622b" rel="nofollow noopener">
          <span class="hero-badge-icon"><i class="fa-solid fa-fire-flame-curved"></i></span>
          <span class="hero-badge-copy">
            <span class="hero-badge-title">CurseForge</span>
            <span class="hero-badge-subtitle">Downloads</span>
          </span>
        </a>
        <a class="hero-badge-card hero-badge-card-modrinth" href="https://modrinth.com/mod/the-digimod" target="_blank"
          data-count-url="https://img.shields.io/modrinth/dt/the-digimod?logo=modrinth&amp;labelColor=101013&amp;color=1bd96a" rel="nofollow noopener">
          <span class="hero-badge-icon"><i class="fa-solid fa-mountain"></i></span>
          <span class="hero-badge-copy">
            <span class="hero-badge-title">Modrinth</span>
            <span class="hero-badge-subtitle">Downloads</span>
          </span>
        </a>
      </div>
    </div>
  </section>


  <div class="xl:hidden block mobile-ad-slot">
    <div class="p-4">
      <ins class="adsbygoogle" style="display:inline-block; width:728px; height:90px;" data-ad-client="ca-pub-2592338544514821" data-ad-slot="1515942434"></ins>
      <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
    </div>
  </div>

  <div class="flex justify-center" style="width: 100%;">

    <div class="hidden xl:block ad-sidebar">
      <div class="ad-sticky">
        <div class="ad-inner">
          <ins class="adsbygoogle" style="display:inline-block; width:300px; height:600px;"
            data-ad-client="ca-pub-2592338544514821" data-ad-slot="3061012292"></ins>
          <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
        </div>
      </div>
    </div>

    <div class="w-full xl:w-[70vw] wiki-detail">
      <div class="item-overview">
        <section class="lore-box lore-section item-toc">
          <h2 class="lore-section-title">Contents</h2>
          <ul class="mod-content-list">
{toc_links}
          </ul>
        </section>

        <aside class="lore-box lore-section item-infobox">
          <h2 class="lore-section-title">{name}</h2>
          <div class="item-infobox-image">
            <img src="{icon}" alt="{name}">
          </div>
          <dl class="item-stats">
            <dt>Type</dt>
            <dd>{type_label}</dd>
{extra_stats}            <dt>ID</dt>
            <dd><code>thedigimod:{item_id}</code></dd>
          </dl>
        </aside>
      </div>

      <section id="usage" class="lore-box lore-section">
        <h2 class="lore-section-title">Usage</h2>
        <div class="lore-section-body">
{usage_paragraphs}
        </div>
      </section>

{crafting_section}{used_in_section}
    </div>

    <div class="hidden xl:block ad-sidebar">
      <div class="ad-sticky">
        <div class="ad-inner">
          <ins class="adsbygoogle" style="display:inline-block; width:300px; height:600px;"
            data-ad-client="ca-pub-2592338544514821" data-ad-slot="3061012292"></ins>
          <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
        </div>
      </div>
    </div>

  </div>

  <div class="xl:hidden block mobile-ad-slot">
    <div class="p-4">
      <ins class="adsbygoogle" style="display:inline-block; width:728px; height:90px;" data-ad-client="ca-pub-2592338544514821" data-ad-slot="1515942434"></ins>
      <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
    </div>
  </div>

  <script src="./src/scripts/js/common.js"></script>
</body>

</html>
"""


def generate_item_page(item_id: str, display_name: str, category: str, icon_rel: str, recipe: dict | None,
	item_lang: dict, block_lang: dict, move_usage: dict, digimon_cache: dict, entity_lang: dict,
	used_in_entries: list[tuple[str, str, str | None]] | None = None) -> str:
	# Registered under TDItemsAdmin.java's CREATIVE_ITEMS - real, usable items,
	# but with no recipe/loot/mob-drop source anywhere in the mod's data, so
	# they're unobtainable in normal survival play (per ModderG, mod author).
	is_creative_only = item_id in CREATIVE_ONLY_IDS
	type_label = "Creative Item" if is_creative_only else CATEGORY_META[category][1]

	# Usage first - it's what a player looks a page up for; Crafting (when it
	# exists) comes after.
	toc_entries = ['            <li><a href="#usage" class="mod-content-link"><span class="mod-content-bullet"></span><span>Usage</span></a></li>']
	crafting_html = ""
	if recipe:
		toc_entries.append('            <li><a href="#crafting" class="mod-content-link"><span class="mod-content-bullet"></span><span>Crafting</span></a></li>')
		crafting_html = render_recipe_section(item_id, display_name, icon_rel, recipe, item_lang, block_lang)

	used_in_html = render_used_in_section(used_in_entries or [])
	if used_in_entries:
		toc_entries.append('            <li><a href="#crafting-material-for" class="mod-content-link"><span class="mod-content-bullet"></span><span>Material for</span></a></li>')

	extra_stats = ""
	if category == "chips":
		move = item_id.removeprefix("chip_")
		users = move_usage.get(move, [])
		if users:
			shown = ", ".join(mob_link(slug, name) for slug, name in users[:6])
			more = f" +{len(users) - 6} more" if len(users) > 6 else ""
			extra_stats = f"            <dt>Used By</dt>\n            <dd>{shown}{more}</dd>\n"
	elif category == "digitama" and item_id in digimon_cache:
		link = mob_link(item_id, entity_lang.get(item_id, display_name))
		extra_stats = f"            <dt>Spawns</dt>\n            <dd>{link}</dd>\n"

	paras = usage_paragraphs(item_id, category, display_name, move_usage, digimon_cache, entity_lang)
	# For creative-only items we don't repeat the "not obtainable in survival"
	# note in Usage - Obtaining already says "Creative Mode only in the current
	# version of the mod." and that's the single source of truth for that fact.
	usage_html = "\n".join(f"          <p>{p}</p>" for p in paras)

	return PAGE_TEMPLATE.format(
		name=html.escape(display_name),
		toc_links="\n".join(toc_entries),
		icon=icon_rel,
		type_label=html.escape(type_label),
		extra_stats=extra_stats,
		item_id=item_id,
		crafting_section=crafting_html,
		used_in_section=used_in_html,
		usage_paragraphs=usage_html,
	)


# ---------------------------------------------------------------------------
# Index section + nav

def build_index_section(items_by_category: dict[str, list[tuple[str, str, str]]], digimon_cache: dict | None = None) -> tuple[str, str, str]:
	digimon_cache = digimon_cache or {}
	# Group Digitamas by the item texture their model actually uses (e.g.
	# "item/nightmare_baby") rather than the digimon json's egg_type field.
	# The two usually match, but some babies (Kuramon) leave egg_type unset
	# while their item still points at a shared egg texture - and grouping
	# by texture is what matches the icons the user sees in the listing.
	xp_by_baby = {slug: (data.get("xps") or [0])[0] for slug, data in digimon_cache.items()}
	texture_by_baby: dict[str, str] = {}
	for entries in items_by_category.values():
		for item_id, _display, _icon in entries:
			tex = resolve_texture(item_id) or ""
			if tex:
				texture_by_baby[item_id] = tex
	texture_order: dict[str, int] = {}
	for slug, tex in texture_by_baby.items():
		if not tex:
			continue
		texture_order[tex] = min(texture_order.get(tex, xp_by_baby.get(slug, 0)), xp_by_baby.get(slug, 0))

	def sort_key(cat: str, entry):
		item_id, display_name, _ = entry
		if cat == "digitama":
			tex = texture_by_baby.get(item_id, "")
			# Unknown textures sort last so unresolved stragglers don't
			# wedge themselves into a random group.
			return (texture_order.get(tex, 10**9), xp_by_baby.get(item_id, 0), display_name)
		return (display_name,)

	lines = []
	first_href = first_icon = None
	for cat in CATEGORY_ORDER:
		entries = items_by_category.get(cat)
		if not entries:
			continue
		title = CATEGORY_META[cat][0]
		lines.append(f'            <li class="category-label">{html.escape(title)}</li>')
		for item_id, display_name, icon_rel in sorted(entries, key=lambda e: sort_key(cat, e)):
			href = f"./td_item_{item_id}.html"
			if first_href is None:
				first_href, first_icon = href, icon_rel
			lines.append(
				f'            <li>\n'
				f'              <a href="{href}" class="mod-content-link">\n'
				f'                <img src="{icon_rel}" alt="" class="mod-content-icon">\n'
				f'                <span>{html.escape(display_name)}</span>\n'
				f'              </a>\n'
				f'            </li>'
			)
	return "\n".join(lines), first_href or "#", first_icon or ""


def build_training_goods_section(
	items_by_category: dict[str, list[tuple[str, str, str]]],
	entity_lang: dict[str, str],
) -> tuple[str, str]:
	"""Emit the standalone "Training Good Entities" gallery.

	Returns (list_html, entries_json_html). The list is a Mobs-style
	`<li data-tg-idx>` roster with tier group-labels; the entries block is
	a JSON array the client-side rotator uses to render name/image/stats
	when a list entry is clicked. Every SpawnGoodItem in the mod has a
	matching AbstractTrainingGood entity - documented here as an entity
	(no separate page). Items with no entity form (training_bag bundle)
	are skipped.
	"""
	pool = [
		e for e in (items_by_category.get("training") or [])
		if e[0] in TRAINING_ITEM_TO_ENTITY
	]
	basic, advanced = [], []
	for item_id, item_name, icon_rel in pool:
		entity_id = TRAINING_ITEM_TO_ENTITY[item_id]
		entity_name = entity_lang.get(entity_id) or item_name
		row = (item_id, entity_id, entity_name, item_name, icon_rel)
		(advanced if item_id in TRAINING_ADVANCED_IDS else basic).append(row)
	basic.sort(key=lambda r: r[2])
	advanced.sort(key=lambda r: r[2])

	list_lines: list[str] = []
	entries: list[dict] = []

	def push_group(title: str, group: list, tier_label: str) -> None:
		if not group:
			return
		list_lines.append(
			f'            <li class="mob-tier-label">{html.escape(title)}</li>'
		)
		for item_id, entity_id, entity_name, item_name, icon_rel in group:
			idx = len(entries)
			list_lines.append(
				f'            <li data-tg-idx="{idx}">{html.escape(entity_name)}</li>'
			)
			entry: dict = {
				"name": entity_name,
				"img": f"./src/assets/images/the_digimod/training_goods/{entity_id}.png",
				"entity_id": entity_id,
				"item_id": item_id,
				"item_name": item_name,
				"item_href": f"./td_item_{item_id}.html",
				"stat": TRAINING_STAT_MAP.get(item_id, "-"),
				"tier": tier_label,
			}
			xp_idx = TRAINING_XP_MAP.get(item_id)
			if xp_idx is not None and 0 <= xp_idx < len(XP_ITEMS):
				xp_id, xp_label = XP_ITEMS[xp_idx]
				entry["xp"] = {
					"label": xp_label,
					"img": f"./src/assets/images/the_digimod/xp_items/{xp_id}.png",
					"href": f"./td_item_{xp_id}.html",
				}
			entries.append(entry)

	push_group("Basic Training Good Entities", basic, "Basic")
	push_group("High Tier Training Good Entities", advanced, "High Tier")

	entries_lines = [
		"        " + json.dumps(e) + ("," if i < len(entries) - 1 else "")
		for i, e in enumerate(entries)
	]
	return "\n".join(list_lines), "\n".join(entries_lines)


def main() -> int:
	lang = fetch_lang_map()
	item_lang = {k.removeprefix("item.thedigimod."): v for k, v in lang.items() if k.startswith("item.thedigimod.")}
	block_lang = {k.removeprefix("block.thedigimod."): v for k, v in lang.items() if k.startswith("block.thedigimod.")}
	entity_lang = {k.removeprefix("entity.thedigimod."): v for k, v in lang.items() if k.startswith("entity.thedigimod.")}

	digimon_cache = load_digimon_cache()
	move_usage = build_move_usage(digimon_cache, entity_lang)
	recipes_by_result = fetch_recipes()

	# Reverse recipe index: TD ingredient item_id -> sorted list of result item_ids
	# that consume it. Used to build the "Material for" section on each
	# ingredient's page.
	used_in: dict[str, set[str]] = {}
	for result_id, recipe in recipes_by_result.items():
		for ing_id in recipe_td_ingredients(recipe):
			if ing_id == result_id:
				continue
			used_in.setdefault(ing_id, set()).add(result_id)

	ITEMS_DIR.mkdir(parents=True, exist_ok=True)

	items_by_category: dict[str, list[tuple[str, str, str]]] = {}
	generated_files = set()
	# id -> (display_name, icon_rel) for every emitted page. Needed to render
	# "Material for" entries with correct icons/labels.
	item_meta: dict[str, tuple[str, str]] = {}

	# First pass: collect metadata for every item that will get a page.
	pending: list[tuple[str, str, str, str]] = []  # (item_id, display_name, category, icon_rel)
	for item_id, display_name in sorted(item_lang.items()):
		if item_id in EXCLUDED_ITEM_IDS:
			continue
		category = categorize(item_id, display_name)

		if category == "data":
			icon_rel = f"./src/assets/images/the_digimod/xp_items/{item_id}.png"
			if not (XP_ITEMS_DIR / f"{item_id}.png").exists():
				icon_rel = get_thedigimod_icon(item_id) or icon_rel
		else:
			icon_rel = get_thedigimod_icon(item_id)
		if not icon_rel:
			print(f"WARNING: skipping {item_id!r} (Digitama-check: {item_id in digimon_cache}), no icon resolved", file=sys.stderr)
			continue

		items_by_category.setdefault(category, []).append((item_id, display_name, icon_rel))
		item_meta[item_id] = (display_name, icon_rel)
		pending.append((item_id, display_name, category, icon_rel))

	# Second pass. Item pages are NOT auto-regenerated any more - they are
	# hand-authored (Usage / Obtaining / Crafting prose is written by a human).
	# For pages that already exist we only patch the "Material for"
	# section and its TOC entry in place, so recipe changes stay in sync while
	# manual prose is preserved. Pages for brand-new items still get a full
	# template so authoring can start from a scaffold.
	for item_id, display_name, category, icon_rel in pending:
		recipe = recipes_by_result.get(item_id)
		used_in_entries: list[tuple[str, str, str | None]] = []
		for result_id in sorted(used_in.get(item_id, ())):
			meta = item_meta.get(result_id)
			if not meta:
				continue
			r_name, r_icon = meta
			used_in_entries.append((result_id, r_name, r_icon))
		used_in_entries.sort(key=lambda t: t[1].lower())
		out_file = TD_PAGES_DIR / f"td_item_{item_id}.html"
		if out_file.exists():
			patched = patch_used_in_section(out_file.read_text(encoding="utf-8"), used_in_entries)
			out_file.write_text(patched, encoding="utf-8")
		else:
			page_html = generate_item_page(
				item_id, display_name, category, icon_rel, recipe,
				item_lang, block_lang, move_usage, digimon_cache, entity_lang,
				used_in_entries=used_in_entries,
			)
			out_file.write_text(page_html, encoding="utf-8")
		generated_files.add(out_file.name)

	# Orphan detection: an item removed/renamed leaves its old page behind. We
	# only warn - never auto-delete - because these pages now hold hand-written
	# prose that we don't want silently trashed.
	for existing in REPO_ROOT.glob("td_item_*.html"):
		if existing.name not in generated_files:
			print(f"NOTE: orphan item page (no matching lang entry): {existing.name}", file=sys.stderr)

	list_html, first_href, first_icon = build_index_section(items_by_category, digimon_cache)

	content = TD_LORE_HTML.read_text(encoding="utf-8")

	items_section = f"""      <div class="item-overview items-overview">
        <section id="section-items" class="lore-box lore-section item-toc">
          <h2 class="lore-section-title">Items</h2>
          <p class="mod-content-intro">
            Digivices, training gear, consumables and crafting materials added by the mod, grouped by type.
          </p>
          <ul class="mod-content-list">
<!-- TD-ITEMS:LIST:START (generated by src/scripts/sync_td_items.py, do not hand-edit) -->
{list_html}
            <!-- TD-ITEMS:LIST:END -->
          </ul>
        </section>

        <aside class="lore-box lore-section item-infobox items-rotator">
          <a id="items-rotator-link" href="{first_href}" class="item-infobox-image items-rotator-image">
            <img id="items-rotator-img" src="{first_icon}" alt="">
          </a>
        </aside>
      </div>"""

	if "TD-ITEMS:LIST:START" not in content:
		# First run: insert the whole items-overview block right after the
		# mobs-overview block closes, inside the shared .content-lists div.
		anchor = '</aside>\n        </div>\n      </div>\n'
		if anchor not in content:
			print("ERROR: could not find the mobs-overview closing anchor in td_lore.html - "
				"has its structure changed? Not inserting the Items section.", file=sys.stderr)
			return 1
		content = content.replace(anchor, "</aside>\n        </div>\n\n" + items_section + "\n      </div>\n", 1)
	else:
		content = re.sub(
			r'<!-- TD-ITEMS:LIST:START.*?<!-- TD-ITEMS:LIST:END -->',
			lambda _: f"<!-- TD-ITEMS:LIST:START (generated by src/scripts/sync_td_items.py, do not hand-edit) -->\n{list_html}\n            <!-- TD-ITEMS:LIST:END -->",
			content,
			count=1,
			flags=re.DOTALL,
		)
		content = re.sub(
			r'(id="items-rotator-link" href=")[^"]*(")',
			lambda m: m.group(1) + first_href + m.group(2),
			content,
			count=1,
		)
		content = re.sub(
			r'(id="items-rotator-img" src=")[^"]*(")',
			lambda m: m.group(1) + first_icon + m.group(2),
			content,
			count=1,
		)

	if '<span>Items</span>' not in content:
		content = content.replace(
			'            <li>\n              <a href="#section-mobs-modeled" class="mod-content-link">\n'
			'                <img src="./src/assets/images/the_digimod/roster/rookie_palmon.png" alt="" class="mod-content-icon">\n'
			'                <span>Modeled Mobs</span>\n              </a>\n            </li>\n          </ul>',
			'            <li>\n              <a href="#section-mobs-modeled" class="mod-content-link">\n'
			'                <img src="./src/assets/images/the_digimod/roster/rookie_palmon.png" alt="" class="mod-content-icon">\n'
			'                <span>Modeled Mobs</span>\n              </a>\n            </li>\n'
			'            <li>\n              <a href="#section-items" class="mod-content-link">\n'
			f'                <img src="{first_icon}" alt="" class="mod-content-icon">\n'
			'                <span>Items</span>\n              </a>\n            </li>\n          </ul>',
		)

	# Standalone Training Good Entities gallery (Mobs-style: click-to-select
	# list on the left, rotator with per-entity stats on the right). Its HTML
	# skeleton and rotator JS are hand-authored in td_lore.html; we only
	# refresh the two markers here - the `<li>` list and the JS entries JSON.
	training_list_html, training_entries_html = build_training_goods_section(
		items_by_category, entity_lang
	)
	if "TD-TRAINING-GOODS:LIST:START" in content:
		content = re.sub(
			r'<!-- TD-TRAINING-GOODS:LIST:START.*?<!-- TD-TRAINING-GOODS:LIST:END -->',
			lambda _: (
				"<!-- TD-TRAINING-GOODS:LIST:START (generated by src/scripts/sync_td_items.py, do not hand-edit) -->\n"
				f"{training_list_html}\n"
				"          <!-- TD-TRAINING-GOODS:LIST:END -->"
			),
			content,
			count=1,
			flags=re.DOTALL,
		)
	if "TD-TRAINING-GOODS:ENTRIES:START" in content:
		content = re.sub(
			r'// TD-TRAINING-GOODS:ENTRIES:START.*?// TD-TRAINING-GOODS:ENTRIES:END',
			lambda _: (
				"// TD-TRAINING-GOODS:ENTRIES:START (generated by src/scripts/sync_td_items.py, do not hand-edit)\n"
				f"{training_entries_html}\n"
				"        // TD-TRAINING-GOODS:ENTRIES:END"
			),
			content,
			count=1,
			flags=re.DOTALL,
		)

	TD_LORE_HTML.write_text(content, encoding="utf-8")

	total = sum(len(v) for v in items_by_category.values())
	print(f"items={total} pages_written={len(generated_files)}")
	for cat in CATEGORY_ORDER:
		if cat in items_by_category:
			print(f"  {CATEGORY_META[cat][0]}: {len(items_by_category[cat])}", file=sys.stderr)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
