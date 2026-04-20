"""Minimal Markdown → HTML converter (stdlib only).

Supports the subset of Markdown we actually use in our bundled help
files:

    # / ## / ### … headings     (ATX-style, up to six levels)
    * or - bullet lists         (single level, indented continuation lines join)
    blank-line-separated paragraphs, with hard-wrapped lines joined
    **bold**, *italic*, `code`, [link text](https://url)

No code blocks, no tables, no images, no raw HTML pass-through, no
nested lists. If you need more, add it here and add a test — the
goal is deliberately small, readable, and predictable. Everything
is stdlib (``re`` and ``html``).

Output is semantic HTML (``<h1>``, ``<ul>``, ``<li>``, ``<p>``,
``<strong>``, ``<em>``, ``<code>``, ``<a>``) so NVDA's browse-mode
navigation works naturally inside the bundled help.
"""

from __future__ import annotations

import html as _html
import re


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_RE = re.compile(r"^[*-]\s+(.*)$")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_CODE_RE = re.compile(r"`([^`]+)`")


def _inline(escaped: str) -> str:
	"""Apply inline transforms to text that has ALREADY been HTML-escaped.

	Order matters: links first (they carry URLs the other patterns must
	not touch), then bold (``**``) before italic (``*``), then code.
	"""
	def _link(match: re.Match) -> str:
		return f'<a href="{match.group(2)}">{match.group(1)}</a>'

	escaped = _LINK_RE.sub(_link, escaped)
	escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
	escaped = _ITALIC_RE.sub(r"<em>\1</em>", escaped)
	escaped = _CODE_RE.sub(r"<code>\1</code>", escaped)
	return escaped


def _body(markdown: str) -> str:
	"""Convert a Markdown string to the inner HTML body (no <html> wrapper)."""
	out: list[str] = []

	paragraph: list[str] = []
	list_items: list[str] = []          # finished items, awaiting <ul> emission
	current_item: list[str] | None = None  # the item we are still accumulating

	def flush_paragraph() -> None:
		if paragraph:
			out.append(f"<p>{_inline(_html.escape(' '.join(paragraph)))}</p>")
			paragraph.clear()

	def finish_current_item() -> None:
		nonlocal current_item
		if current_item is not None:
			list_items.append(" ".join(current_item))
			current_item = None

	def flush_list() -> None:
		finish_current_item()
		if list_items:
			out.append("<ul>")
			for text in list_items:
				out.append(f"<li>{_inline(_html.escape(text))}</li>")
			out.append("</ul>")
			list_items.clear()

	for raw in markdown.splitlines():
		line = raw.rstrip()
		stripped = line.lstrip()

		if not stripped:
			flush_paragraph()
			flush_list()
			continue

		# Indented non-bullet line while we have a list item open →
		# it is a soft continuation of that item.
		if current_item is not None and raw.startswith((" ", "\t")) and not _LIST_RE.match(stripped):
			current_item.append(stripped)
			continue

		heading = _HEADING_RE.match(line)
		if heading:
			flush_paragraph()
			flush_list()
			level = len(heading.group(1))
			text = _inline(_html.escape(heading.group(2).strip()))
			out.append(f"<h{level}>{text}</h{level}>")
			continue

		item = _LIST_RE.match(line)
		if item:
			flush_paragraph()
			finish_current_item()
			current_item = [item.group(1).strip()]
			continue

		# Plain text line. If a list is open, this closes it (a new
		# unindented paragraph breaks the list).
		flush_list()
		paragraph.append(stripped)

	flush_paragraph()
	flush_list()
	return "\n".join(out)


def convert(markdown: str, title: str = "Help") -> str:
	"""Return a full, standalone HTML5 document for ``markdown``.

	If the markdown starts with an ``# H1`` line, its text becomes the
	document's <title>; otherwise we fall back to ``title``.
	"""
	first_heading = _HEADING_RE.match(markdown.lstrip().splitlines()[0]) if markdown.strip() else None
	if first_heading and len(first_heading.group(1)) == 1:
		title = first_heading.group(2).strip() or title

	inner = _body(markdown)
	escaped_title = _html.escape(title)
	return (
		"<!DOCTYPE html>\n"
		"<html lang=\"en\">\n"
		"<head>\n"
		"<meta charset=\"utf-8\">\n"
		f"<title>{escaped_title}</title>\n"
		"</head>\n"
		"<body>\n"
		f"{inner}\n"
		"</body>\n"
		"</html>\n"
	)
