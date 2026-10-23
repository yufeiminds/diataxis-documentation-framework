"""End-to-end: the real translation workflow this extension targets.

Sphinx re-parses every translated msgstr with the RST parser (the
``Locale`` transform), so translators write ``它 *有效* 得很`` — with the
spaces the markup needs to be recognised — directly in the catalog. The
rendered zh_CN page then carries those spaces, until the final-stage pass
removes them.

The pair of tests builds the *same* project with and without the
extension: the bug is reproduced without it, and gone with it.
"""

from __future__ import annotations

from pathlib import Path

from extensions.cjkspace.tests.conftest import _build, _write_mo

INDEX_RST = "Welcome\n=======\n\nIt works *well*.\n"

CATALOG = {
    "Welcome": "欢迎",
    "It works *well*.": "它 *有效* 得很。",
}

CONF_EXTRA = 'locale_dirs = ["locale"]\ngettext_compact = False'


def _translated_build(tmp_path: Path, *, extensions=("extensions.cjkspace",)):
    return _build(
        tmp_path,
        INDEX_RST,
        language="zh_CN",
        extra_conf=CONF_EXTRA,
        extra_files={"locale/zh_CN/LC_MESSAGES/index.mo": _write_mo(CATALOG)},
        extensions=extensions,
    )


def _page(outdir: Path) -> str:
    return (outdir / "index.html").read_text(encoding="utf-8")


def test_translated_msgstr_keeps_its_artificial_spaces_without_extension(tmp_path):
    _app, out = _translated_build(tmp_path, extensions=())
    html = _page(out)
    # The premise of the extension: the translated msgstr parses (its
    # spaces are what made the markup recognisable) and renders them.
    assert "它 <em>有效</em> 得很。" in html


def test_translated_msgstr_spaces_are_removed(tmp_path):
    _app, out = _translated_build(tmp_path)
    html = _page(out)
    assert "它<em>有效</em>得很。" in html
    assert "它 <em>" not in html
    assert "</em> 得很" not in html


def test_translated_title_is_glued(tmp_path):
    # Titles go through the same pass: the re-parsed translated title is
    # fixed before the page is written.
    catalog = {"Welcome": "欢迎 *到来* 吧", "It works *well*.": "它 *有效*。"}
    _app, out = _build(
        tmp_path,
        INDEX_RST,
        language="zh_CN",
        extra_conf=CONF_EXTRA,
        extra_files={"locale/zh_CN/LC_MESSAGES/index.mo": _write_mo(catalog)},
    )
    html = _page(out)
    assert "欢迎<em>到来</em>吧" in html
