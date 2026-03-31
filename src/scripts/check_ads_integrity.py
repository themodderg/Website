#!/usr/bin/env python3

from pathlib import Path
import re
import sys


OPEN_INS_RE = re.compile(r"<ins\b", re.IGNORECASE)
CLOSE_INS_RE = re.compile(r"</ins>", re.IGNORECASE)
PUSH_CALL_RE = re.compile(r"\(adsbygoogle\s*=\s*window\.adsbygoogle\s*\|\|\s*\[\]\)\.push\(\{\}\)")
AD_CLIENT_RE = re.compile(r"data-ad-client\s*=\s*[\"'][^\"']+[\"']", re.IGNORECASE)
AD_SLOT_RE = re.compile(r"data-ad-slot\s*=\s*[\"'][^\"']+[\"']", re.IGNORECASE)


def main() -> int:
	repo_root = Path(__file__).resolve().parents[2]
	html_files = sorted(repo_root.glob("*.html"))

	failures: list[str] = []
	checked_pages = 0

	for file_path in html_files:
		content = file_path.read_text(encoding="utf-8")
		if "adsbygoogle" not in content:
			continue

		checked_pages += 1
		open_ins = len(OPEN_INS_RE.findall(content))
		close_ins = len(CLOSE_INS_RE.findall(content))
		push_calls = len(PUSH_CALL_RE.findall(content))

		if open_ins != close_ins:
			failures.append(
				f"{file_path.name}: mismatched <ins> tags (open={open_ins}, close={close_ins})"
			)

		if push_calls != open_ins:
			failures.append(
				f"{file_path.name}: push calls do not match ad blocks (push_calls={push_calls}, ad_blocks={open_ins})"
			)

		ad_blocks = re.findall(r"<ins[^>]*class=[\"'][^\"']*adsbygoogle[^\"']*[\"'][^>]*>", content, re.IGNORECASE)
		for index, ad_block in enumerate(ad_blocks, start=1):
			if not AD_CLIENT_RE.search(ad_block):
				failures.append(f"{file_path.name}: ad block #{index} missing data-ad-client")
			if not AD_SLOT_RE.search(ad_block):
				failures.append(f"{file_path.name}: ad block #{index} missing data-ad-slot")

	if checked_pages == 0:
		print("No pages with adsbygoogle markers found. Failing to prevent silent ad removal.")
		return 1

	if failures:
		print("Ad integrity check failed:\n")
		for failure in failures:
			print(f"- {failure}")
		return 1

	print(f"Ad integrity check passed for {checked_pages} pages.")
	return 0


if __name__ == "__main__":
	sys.exit(main())
