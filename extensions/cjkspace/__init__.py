"""Sphinx extension: strip artificial spaces around inline markup in CJK text.

The problem (cf. https://github.com/tats-u/markdown-cjk-friendly)
----------------------------------------------------------------
reStructuredText — like CommonMark, cf. the ``markdown-cjk-friendly``
specification — only recognises inline markup delimiters (``*emphasis*``,
``**strong**``, literals, ...) when they are flanked by whitespace or
punctuation.  CJK characters qualify as neither, so emphasis embedded in
CJK prose has to be padded with spaces to parse at all::

    即它 *为什么* 有效

Translators add these spaces especially on translation platforms such as
Transifex, where the rendered output cannot be previewed and the markup
rules are not understood — the exact scenario ``markdown-cjk-friendly``
was written for.  The spaces then leak into the rendered page as unwanted
gaps between CJK text and the emphasised span::

    即它 <em>为什么</em> 有效

CJK typography puts no space between CJK characters, so the spaces are
artifacts of the markup workaround, not of the prose.

The fix (after https://github.com/seisman/sphinx-cjkspace)
----------------------------------------------------------
Like ``sphinx-cjkspace`` removes newline-induced spaces between CJK
characters after parsing, this extension post-processes the resolved
doctree — at ``doctree-read``, before the navigation snapshots section
titles, and again at ``doctree-resolved``, the last stage before writing
— and deletes the artificial whitespace there.  Parsing and the message
catalogs are never touched.

A whitespace run at the seam between a ``Text`` node and a neighbouring
inline element (emphasis, strong, literal, reference, ...) is dropped when
both characters flanking it are CJK:

* the last (or first) character of the ``Text`` node, and
* the first (or last) character rendered by the neighbouring element.

CJK here means a character of East Asian Width ``W`` or ``F`` that is a
letter, digit or punctuation mark — ideographs, kana, hangul, CJK
punctuation (。、「」) and fullwidth forms (！：) — plus punctuation of
Ambiguous East Asian Width that CJK typography uses as its own: the em
dash (——), the ellipsis (……), curly quotes (“”), the middle dot (·).
Wide symbols/emoji do not qualify (a space reads fine there), and neither
do ambiguous-width letters, so European prose — French é, Greek α — is
untouched.

Because removal only ever triggers between two CJK characters, prose in
other languages is untouched, and the (desirable) space between CJK and
Latin text is kept.  Newline-wrapped source counts as whitespace too, so
markup at the start of a continuation line is glued as well, mirroring
sphinx-cjkspace's line joining.

The ``gettext`` builder is skipped, so ``.pot`` msgids stay verbatim for
translators; ``literal_block`` (which includes parsed literals) and
``math_block`` are skipped because whitespace there is significant.
"""

from __future__ import annotations

import re
import unicodedata

from docutils import nodes

__version__ = "0.1.0"

# East Asian Width values of characters treated as CJK text: Wide and
# Fullwidth. Halfwidth forms do not qualify.
_CJK_WIDTHS = frozenset("WF")

# Category prefixes (first letter of unicodedata.category) of characters
# that count as CJK text: letters (ideographs, kana, hangul), numbers and
# punctuation (。、「」！). Excludes symbols/emoji (S*) — a wide emoji is
# regularly followed by a space that reads fine — and marks (M*).
_CJK_CATEGORIES = frozenset("LNP")

# Whitespace runs at a Text node's seams. \s matches the fullwidth space
# U+3000 as well as newlines, so a source line wrapped right before
# markup joins too. The optional \x00 is docutils' escape marker: an
# escaped space (``\ ``, common in translated msgstrs so tooling keeps
# it) is stored as NUL + space and is just as artificial a seam space.
_LEADING_WS = re.compile(r"^(?:\x00?\s)+")
_TRAILING_WS = re.compile(r"(?:\x00?\s)+$")

# Parents whose children are left alone: whitespace is significant in
# literal blocks (``.. parsed-literal::`` shares the literal_block class)
# and in math.
_PRESERVE_PARENTS = (nodes.literal_block, nodes.math_block)


def is_cjk_char(char: str) -> bool:
    """True if *char* is a CJK character that forbids an adjacent space.

    CJK ideographs, kana and hangul, CJK punctuation (。、) and fullwidth
    forms (！：) qualify. So does punctuation of Ambiguous East Asian Width
    that Chinese/Japanese typography uses as CJK punctuation — the em dash
    (——), the ellipsis (……), curly quotes (“”), the middle dot (·).
    ASCII/Latin, ambiguous-width *letters* (é, α — European prose keeps
    its spaces), and wide symbols/emoji do not.

    >>> is_cjk_char("中")
    True
    >>> is_cjk_char("。") or is_cjk_char("—") or is_cjk_char("…")
    True
    >>> is_cjk_char("A") or is_cjk_char("é") or is_cjk_char("😀")
    False
    """
    if not char:
        return False
    category = unicodedata.category(char)
    width = unicodedata.east_asian_width(char)
    if width in _CJK_WIDTHS:
        return category[0] in _CJK_CATEGORIES
    # Ambiguous-width punctuation: —— …… “” · are written without spaces
    # in CJK text (and a space next to them is often the markup workaround
    # too). Ambiguous-width letters stay non-CJK so European prose is safe.
    return width == "A" and category[0] == "P"


def _edge_char(node: nodes.Element, *, last: bool) -> str:
    """First (or last) character that *node* renders.

    ``""`` when the node renders nothing visible (an image without alt
    text, an inline target), which keeps the neighbouring space.
    """
    text = node.astext()
    return text[-1:] if last else text[:1]


def _replace_text(parent: nodes.Element, index: int, raw: str) -> bool:
    """Swap the Text node at ``parent.children[index]`` for one holding *raw*.

    docutils Text nodes are ``str`` subclasses with no mutable data slot,
    so the node has to be replaced rather than edited. ``setup_child``
    keeps the parent/document pointers intact, and assignment is by index
    so identical-content siblings elsewhere in the same parent cannot be
    confused (``index()`` would match them via str equality).
    """
    fresh = nodes.Text(raw)
    parent.setup_child(fresh)
    parent.children[index] = fresh
    return True


def _strip_trailing(parent: nodes.Element, index: int) -> bool:
    """Drop Text node *index*'s trailing whitespace run.

    Fires when the character before the run in the Text node and the
    first character of the element following it are both CJK.
    """
    raw = str(parent.children[index])
    match = _TRAILING_WS.search(raw)
    if match is None or match.start() == 0:
        # no run, or the node is all whitespace (a middle case handled
        # by _strip_inner_space)
        return False
    if not (
        is_cjk_char(raw[match.start() - 1])
        and is_cjk_char(_edge_char(parent.children[index + 1], last=False))
    ):
        return False
    return _replace_text(parent, index, raw[: match.start()])


def _strip_leading(parent: nodes.Element, index: int) -> bool:
    """Drop Text node *index*'s leading whitespace run.

    Fires when the character after the run in the Text node and the last
    character of the element preceding it are both CJK.
    """
    raw = str(parent.children[index])
    match = _LEADING_WS.match(raw)
    if match is None or match.end() == len(raw):
        return False
    rest = raw[match.end() :]
    if not (
        is_cjk_char(rest[0])
        and is_cjk_char(_edge_char(parent.children[index - 1], last=True))
    ):
        return False
    return _replace_text(parent, index, rest)


def _strip_inner_space(parent: nodes.Element) -> None:
    """Blank a whitespace-only Text node caught between two elements.

    ``*甲* *乙*`` needs the middle space to parse, yet renders as
    ``甲乙``: the space is artificial too. Only fires when both elements
    render CJK at the seam.
    """
    children = parent.children
    for i in range(1, len(children) - 1):
        node = children[i]
        if not isinstance(node, nodes.Text) or str(node).replace("\x00", "").strip():
            continue
        left, right = children[i - 1], children[i + 1]
        if isinstance(left, nodes.Text) or isinstance(right, nodes.Text):
            continue
        left_cjk = is_cjk_char(_edge_char(left, last=True))
        right_cjk = is_cjk_char(_edge_char(right, last=False))
        if left_cjk and right_cjk:
            _replace_text(parent, i, "")


def fix_inline_boundaries(parent: nodes.Element) -> None:
    """Strip artificial CJK-boundary spaces among one element's children.

    Only seams between a Text node and a neighbouring element are
    considered; Text↔Text siblings (which do not occur in parsed
    docutils trees) are left alone. Parents where whitespace is
    significant are skipped.
    """
    if isinstance(parent, _PRESERVE_PARENTS):
        return
    children = parent.children
    for i in range(len(children) - 1):
        left, right = children[i], children[i + 1]
        if isinstance(left, nodes.Text):
            if not isinstance(right, nodes.Text):
                _strip_trailing(parent, i)
        elif isinstance(right, nodes.Text):
            _strip_leading(parent, i + 1)
    _strip_inner_space(parent)


def process_cjk_boundaries(app, doctree, docname=None):
    """Strip artificial CJK-boundary spaces from one document tree.

    Connected to two events:

    ``doctree-read`` (priority 490, before the toctree collector's 500)
    so the section titles snapshotted for the navigation are already
    stripped, and ``doctree-resolved`` — the last stage before writing —
    so the page itself is final too. Translations are in place by then:
    the ``Locale`` transform re-parses every msgstr during reading, and
    both passes are idempotent.

    The ``gettext`` builder is skipped: message extraction reads
    ``rawsource`` (which this pass never touches), so there is nothing to
    gain there.
    """
    if app.builder.name == "gettext":
        return
    for parent in list(doctree.findall(nodes.Element)):
        fix_inline_boundaries(parent)


def setup(app):
    # Before the toctree collector snapshots section titles for the
    # navigation (it connects to doctree-read at the default priority).
    app.connect("doctree-read", process_cjk_boundaries, priority=490)
    app.connect("doctree-resolved", process_cjk_boundaries)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
