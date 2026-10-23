cjkspace — CJK inline spacing for Sphinx
=========================================

Remove the spaces that inline markup needs but Chinese, Japanese and Korean
typography does not.

Enable the extension once and inline markup embedded in CJK prose renders
without the artificial gaps around it. There is nothing to configure, and it
is safe to leave on for every language and every builder.

The problem
-----------

reStructuredText — like CommonMark, cf. `markdown-cjk-friendly
<https://github.com/tats-u/markdown-cjk-friendly>`_ — recognises inline
markup only when its delimiters sit next to whitespace or punctuation. CJK
characters count as neither, so this is **not** emphasis::

    中文*强调*中文          →  <p>中文*强调*中文</p>

The workaround is to pad the markup with spaces::

    中文 *强调* 中文        →  <p>中文 <em>强调</em> 中文</p>

That parses — but the spaces now show on the page, and CJK typography puts no
spaces between its characters. The gaps are artefacts of the markup
workaround, not part of the prose.

Translations hit the same problem in a less obvious way. Sphinx re-parses
every translated message (``msgstr``) with the reStructuredText parser, so a
translation that keeps the markup::

    #: ../../source/foundations.rst:12
    msgid "... the thinking and theorising behind Diátaxis – *why* it works ..."
    msgstr "……即它 *为什么* 有效，而不是如何运作。"

renders with the same unwanted gaps::

    即它 <em>为什么</em> 有效，而不是如何运作。

What this extension does
------------------------

After a document has been parsed and translated, the extension deletes the
artificial whitespace at the seam between text and inline markup — but only
when the characters on **both** sides of that whitespace are CJK::

    即它 *为什么* 有效，而不是如何运作。
    ↓
    即它<em>为什么</em>有效，而不是如何运作。

This is the approach of `sphinx-cjkspace
<https://github.com/seisman/sphinx-cjkspace>`_: work on the finished document
tree rather than on parsing, and leave sources and message catalogs alone.
Because it edits the document tree rather than the HTML, the same rule
applies to every builder (HTML, LaTeX, text, EPUB, …).

It fixes **all** inline elements, not only ``*emphasis*``: strong emphasis,
inline literals, references and links, roles such as ``:code:``, and any
other inline node. It also handles section titles — including the copies shown
in the page navigation.

Enabling it
-----------

The extension lives in this repository as ``extensions/cjkspace``. Add its
name to the extension list in ``source/conf.py`` (which already puts
``extensions/`` on ``sys.path``)::

    extensions = ["sphinx_design", "sphinx_reredirects",
                  "atomfeed", "diataxis_diagram", "cjkspace"]

To use it from another project, make the ``cjkspace`` package importable
(vendor it into your project, or add its parent directory to ``sys.path`` in
``conf.py``) and add ``"cjkspace"`` to ``extensions``.

Once enabled, every build benefits — this repository's language targets
(``make html-zh_CN``, ``make html-ja``, …) pick it up with no further change.

What gets fixed
---------------

The rule is always the same. At a seam between a text node and an adjacent
inline element, the whitespace is removed when:

* the text-side character next to the whitespace is CJK, **and**
* the first (or last) character rendered by the inline element is CJK.

.. list-table::
   :header-rows: 1
   :widths: 24 27 25 24

   * - Situation
     - Source (or ``msgstr``)
     - Renders before
     - Renders after
   * - Emphasis with CJK on both sides
     - ``即它 *为什么* 有效。``
     - ``即它 <em>为什么</em> 有效。``
     - ``即它<em>为什么</em>有效。``
   * - Strong emphasis with CJK on both sides
     - ``都兼具 **实践表达** 与 **概念把握**。``
     - ``都兼具 <strong>实践表达</strong> 与 <strong>概念把握</strong>。``
     - ``都兼具<strong>实践表达</strong>与<strong>概念把握</strong>。``
   * - Markup opening after a CJK letter
     - ``即它 *为什么*``
     - ``即它 <em>为什么</em>``
     - ``即它<em>为什么</em>``
   * - Markup closing before a CJK letter
     - ``句子 **粗体** 中文。``
     - ``句子 <strong>粗体</strong> 中文。``
     - ``句子<strong>粗体</strong>中文。``
   * - Space after a CJK full stop, before the opener
     - ``英文。 **粗体** 结尾。``
     - ``英文。 <strong>粗体</strong> 结尾。``
     - ``英文。<strong>粗体</strong>结尾。``
   * - Emphasis ending on CJK punctuation
       (the example from ``markdown-cjk-friendly``)
     - ``**这些星号。** 都是因为这个句子。``
     - ``<strong>这些星号。</strong> 都是因为这个句子。``
     - ``<strong>这些星号。</strong>都是因为这个句子。``
   * - Fullwidth parenthesis after the closing delimiter
     - ``句子 **粗体** （注）结尾。``
     - ``句子 <strong>粗体</strong> （注）结尾。``
     - ``句子<strong>粗体</strong>（注）结尾。``
   * - Space-only text between two spans
     - ``**甲** **乙** 并列。``
     - ``<strong>甲</strong> <strong>乙</strong> 并列。``
     - ``<strong>甲</strong><strong>乙</strong>并列。``
   * - Text between two spans
     - ``**甲** 和 **乙** 并列。``
     - ``<strong>甲</strong> 和 <strong>乙</strong> 并列。``
     - ``<strong>甲</strong>和<strong>乙</strong>并列。``
   * - Emphasis followed by the CJK em dash
     - ``它 *行之有效* —— 无论用户。``
     - ``它 <em>行之有效</em> —— 无论用户。``
     - ``它<em>行之有效</em>—— 无论用户。``
   * - Emphasis followed by the CJK ellipsis
     - ``它 *行之有效* …… 无论用户。``
     - ``它 <em>行之有效</em> …… 无论用户。``
     - ``它<em>行之有效</em>…… 无论用户。``
   * - Any other inline element (references, links, …)
     - ``即它 `链接`_ 有效。``
     - ``即它 <a href="…">链接</a> 有效。``
     - ``即它<a href="…">链接</a>有效。``
   * - Section titles (heading and page navigation)
     - ``小节 *强调* 标题``
     - heading and navigation keep the gaps
     - both render glued

More forms that are handled
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Inline literals.** The same rule applies to inline literals (the
double-backtick markup) and to roles that produce inline markup, such as
``:code:`` or ``:kbd:``.

.. code-block:: text

    这是 ``内嵌代码`` 示例。
    ↓
    这是<code>内嵌代码</code>示例。

**Markup at the start of a wrapped source line.** A newline before the markup
counts as whitespace and is removed between CJK characters (the same joining
that ``sphinx-cjkspace`` does).

.. code-block:: text

    这是一个很长的句子，在行末换行
    *紧接着强调* 然后继续。
    ↓
    这是一个很长的句子，在行末换行<em>紧接着强调</em>然后继续。

**Fullwidth space (U+3000).** It is whitespace like the ASCII space.

.. code-block:: text

    即它　*为什么*　有效。      （　 = U+3000）
    ↓
    即它<em>为什么</em>有效。

**Several spaces.** The whole run is removed, not just one space.

.. code-block:: text

    即它  *为什么*  有效。
    ↓
    即它<em>为什么</em>有效。

**Escaped spaces.** Translation tooling often writes a backslash in front of
a space (a backslash-space) so the space cannot be trimmed; docutils stores
it escaped. It is still an artificial seam space and is removed as well.

.. code-block:: text

    这是 *内嵌强调* \ （注释）结尾。
    ↓
    这是<em>内嵌强调</em>（注释）结尾。

Translations
------------

For translators, nothing about the workflow changes:

* Keep the ``*`` markers in the ``msgstr`` — Sphinx re-parses them, so they
  become real emphasis.
* Keep the spaces that make the markup parse (before an opening delimiter
  that follows a CJK letter, after a closing delimiter followed by a CJK
  letter or an opening fullwidth parenthesis). They are needed while reading
  the catalog, and this extension removes them from the rendered page.
* ``.pot`` files are never modified: msgids keep their markup and spacing
  verbatim, so translation memory and existing ``msgstr`` entries keep
  matching.

A complete ``.po`` entry for a paragraph::

    #: ../../source/foundations.rst:12
    msgid ""
    "the thinking and theorising behind Diátaxis – *why* it works, not how it "
    "works."
    msgstr "阅读本页的唯一理由，是为了更好地领会 Diátaxis 背后的某些思考与理论 —— 即它 *为什么* 有效，而不是如何运作。"

What is left untouched
----------------------

Some spaces are intentional. The extension only acts when **both** sides of
the whitespace are CJK, so all of the following keep their spacing.

* **English and other Latin-script prose** — ``It works *well* today.``
* **The space between CJK and Latin text** — this spacing is desirable, e.g.
  ``中文 *English* 中文`` and ``配置 :code:`Python` 的环境``.
* **Wide emoji** — emoji are symbols rather than text: ``句子 😀 *强调* 😀
  结尾`` keeps its spaces.
* **European accented letters** — ``é``, ``α`` and other ambiguous-width
  letters are not CJK: ``Déjà *强调* déjà`` keeps its spaces.
* **Literal content** — ``.. code-block::``, ``.. parsed-literal::``, doctest
  blocks and other literal blocks, where whitespace is significant.
* **Plain text without adjacent markup** — the extension edits seams around
  inline elements only. A space in ordinary prose, such as ``这是 （注） 说明``,
  is left alone.
* **The plain-text part of a dash** — in ``它<em>行之有效</em>—— 无论用户。``
  only the space before the dash (the markup seam) is removed; the space
  after ``——`` belongs to the prose and stays.

What counts as CJK
------------------

A character counts as CJK when it is written wide in CJK text:

* letters, digits and punctuation of East Asian Width *Wide* or *Fullwidth* —
  ideographs, kana, hangul, ``。``, ``、``, ``「」``, ``（）``, ``！``, ``：``,
  fullwidth digits and so on;
* punctuation of *Ambiguous* width that CJK typography uses as its own —
  the em dash ``——``, the ellipsis ``……``, curly quotes ``“”``, the middle
  dot ``·``.

It does **not** count as CJK:

* wide symbols and emoji (``😀``), where a space reads fine;
* ambiguous-width *letters* (``é``, ``α``, ``Ж``), so European prose is never
  affected;
* halfwidth forms.

Scope and limitations
---------------------

* **Only markup seams are cleaned.** Spaces that come from wrapping plain
  source lines between CJK characters, with no inline markup involved, are
  not touched — that is what `sphinx-cjkspace
  <https://github.com/seisman/sphinx-cjkspace>`__ does. The two extensions can
  be used together.
* **Unparseable markup is out of scope.** If the source has no spaces at all
  (``中文*强调*中文``), the markup never becomes emphasis — no post-processing
  can recover it. Keep the spaces (or a backslash-space), and this extension
  removes them from the output.
* **Very late contributions.** The pass runs at ``doctree-resolved``; content
  injected by another extension after that point is not processed.

How it works
------------

The extension never touches parsing, sources or catalogs. It post-processes
the document tree twice: at ``doctree-read`` (before the toctree collector
snapshots section titles for the navigation) and at ``doctree-resolved`` (the
last stage before writing). At each seam between a text node and an inline
element it removes the whitespace run when both flanking characters are CJK.
Both passes are idempotent, and the ``gettext`` builder is skipped.

Running the tests
-----------------

The test suite lives in ``extensions/cjkspace/tests`` and builds small Sphinx
projects, including a compiled translation catalog::

    pytest extensions/cjkspace/

Compatibility
-------------

Developed and tested against this repository's pins: Sphinx 9.1 and
docutils 0.22. No configuration values, no third-party dependencies, and no
changes to your sources or translations are required.
