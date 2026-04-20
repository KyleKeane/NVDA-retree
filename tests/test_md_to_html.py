"""Tests for tools/md_to_html.py.

Regression coverage is the point — the bundled NVDA help file is
generated through this converter at build time, so any behavioural
drift here would silently change what the user reads inside NVDA.
"""

from md_to_html import _body, convert


def test_h1_and_h2():
	assert _body("# Title\n\n## Subtitle\n") == "<h1>Title</h1>\n<h2>Subtitle</h2>"


def test_heading_up_to_h6():
	assert _body("###### Deep\n") == "<h6>Deep</h6>"


def test_bullet_list_wraps_with_ul():
	md = "* one\n* two\n* three\n"
	assert _body(md) == "<ul>\n<li>one</li>\n<li>two</li>\n<li>three</li>\n</ul>"


def test_dash_bullets_also_work():
	assert _body("- a\n- b\n") == "<ul>\n<li>a</li>\n<li>b</li>\n</ul>"


def test_blank_line_closes_list_and_starts_paragraph():
	md = "* one\n\nA new paragraph.\n"
	assert _body(md) == "<ul>\n<li>one</li>\n</ul>\n<p>A new paragraph.</p>"


def test_heading_after_list_closes_list():
	md = "* one\n\n## Next\n"
	assert _body(md) == "<ul>\n<li>one</li>\n</ul>\n<h2>Next</h2>"


def test_hard_wrap_joins_with_space():
	md = "This is\na paragraph\nwith three wrapped lines.\n"
	assert _body(md) == "<p>This is a paragraph with three wrapped lines.</p>"


def test_list_item_continuation_joins_into_same_li():
	"""Indented lines under a bullet are part of that bullet, not a
	new paragraph. This is the real pattern we use in readme.md:

	    * **Shortcut** — description
	      that wraps to a second line.
	"""
	md = (
		"* **Shortcut** — description\n"
		"  that wraps to a second line.\n"
	)
	assert _body(md) == (
		"<ul>\n"
		"<li><strong>Shortcut</strong> — description that wraps to a second line.</li>\n"
		"</ul>"
	)


def test_unindented_text_after_list_closes_list():
	md = (
		"* one\n"
		"* two\n"
		"A paragraph.\n"
	)
	assert _body(md) == (
		"<ul>\n<li>one</li>\n<li>two</li>\n</ul>\n<p>A paragraph.</p>"
	)


def test_multiple_list_items_each_with_continuations():
	md = (
		"* first\n"
		"  continued.\n"
		"* second\n"
		"  also continued.\n"
	)
	assert _body(md) == (
		"<ul>\n<li>first continued.</li>\n<li>second also continued.</li>\n</ul>"
	)


def test_bold_inline():
	assert _body("**loud**\n") == "<p><strong>loud</strong></p>"


def test_italic_inline():
	assert _body("*emphasised*\n") == "<p><em>emphasised</em></p>"


def test_code_inline():
	assert _body("`code`\n") == "<p><code>code</code></p>"


def test_bold_is_not_confused_for_italic():
	"""Double asterisks must not be split into two `*italic*` pairs."""
	assert _body("**bold**\n") == "<p><strong>bold</strong></p>"


def test_link_inline():
	md = "See [the page](https://example.com/x) for details.\n"
	assert _body(md) == '<p>See <a href="https://example.com/x">the page</a> for details.</p>'


def test_html_chars_are_escaped():
	md = "a < b & c > d\n"
	assert _body(md) == "<p>a &lt; b &amp; c &gt; d</p>"


def test_angle_brackets_inside_code_are_escaped():
	assert _body("use `<Enter>` to submit\n") == (
		"<p>use <code>&lt;Enter&gt;</code> to submit</p>"
	)


def test_full_document_has_doctype():
	html = convert("# Hello\n")
	assert html.startswith("<!DOCTYPE html>")
	assert "<h1>Hello</h1>" in html
	assert html.endswith("</html>\n")


def test_first_h1_becomes_document_title():
	"""NVDA (and browsers) use <title> as the window/tab label. The
	markdown's first H1 is the most descriptive thing we have, so use
	it in preference to the fallback."""
	html = convert("# Semantic Tree\n\nBody.\n", title="Fallback")
	assert "<title>Semantic Tree</title>" in html


def test_title_fallback_used_when_no_h1():
	html = convert("No heading here.\n", title="Fallback")
	assert "<title>Fallback</title>" in html


def test_round_trip_bundled_readme_shape():
	"""The real bundled help file converts without error and produces
	the structural tags NVDA's browse mode relies on."""
	import os
	repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
	path = os.path.join(repo_root, "addon", "doc", "en", "readme.md")
	with open(path, encoding="utf-8") as f:
		html = convert(f.read(), title="Semantic Tree")
	assert "<h1>Semantic Tree</h1>" in html
	assert "<h2>Shortcuts</h2>" in html
	assert "<ul>" in html and "</ul>" in html
	assert "<strong>NVDA + Ctrl + Shift + Up / Down / Left / Right</strong>" in html
	# And nothing leaked through as raw angle brackets from HTML escapes.
	assert "&lt;timestamp&gt;" in html
