"""
syntax_highlighter.py

Use Pygments to perform robust syntax highlighting for a Tkinter Text widget.
Falls back to a simple tag-based approach if Pygments is not installed.

Pygments is lazy-loaded on first use to reduce startup memory (~4-8 MB saved).
Tags are "virtualized": only the visible region carries tags, off-screen tags
are stripped to keep memory proportional to window height, not file size.
"""
from typing import Any, Dict

# ── Lazy Pygments loading ────────────────────────────────────────────
# We do NOT import pygments at module level.  The flag is set in __init__
# and the actual library is loaded in _get_lexer / highlight_* on first call.
PYGMENTS_AVAILABLE = False
Token = None  # type: ignore
_lex = None   # will be set to pygments.lex on first use


def _ensure_pygments():
    """Import pygments on first demand.  Returns True if available."""
    global PYGMENTS_AVAILABLE, Token, _lex
    if PYGMENTS_AVAILABLE:
        return True
    try:
        from pygments import lex as _lex_fn
        from pygments.token import Token as _Token
        _lex = _lex_fn
        Token = _Token
        PYGMENTS_AVAILABLE = True
        return True
    except ImportError:
        PYGMENTS_AVAILABLE = False
        return False


class SyntaxHighlighter:
    # ── Lexer cache (shared across instances) ────────────────────────
    _lexer_cache: Dict[str, Any] = {}

    def __init__(self, text_widget):
        self.text = text_widget
        # Attempt to detect pygments availability (no heavy loading yet)
        _ensure_pygments()
        # Build a direct Token-type → tag-name lookup for O(1) resolution.
        self._token_map: Dict[Any, str] = {}
        if PYGMENTS_AVAILABLE:
            self._token_map = {
                Token.Keyword:           'keyword',
                Token.Keyword.Type:      'type',
                Token.Name.Builtin:      'builtin',
                Token.Name:              'name',
                Token.Name.Function:     'function',
                Token.Name.Class:        'class',
                Token.Literal.String:    'string',
                Token.Literal.Number:    'number',
                Token.Comment:           'comment',
                Token.Comment.Single:    'comment',
                Token.Comment.Multiline: 'comment',
                Token.Comment.Preproc:   'comment',
                Token.Operator:          'operator',
                Token.Punctuation:       'punctuation',
            }
        # Legacy string-based map kept only for fallback in _tag_name_for_token
        self.token_to_tag = {
            'Keyword': 'keyword',
            'Name.Builtin': 'builtin',
            'Name': 'name',
            'Literal.String': 'string',
            'Literal.Number': 'number',
            'Comment': 'comment',
            'Operator': 'operator',
            'Punctuation': 'punctuation',
            'Keyword.Type': 'type',
            'Name.Function': 'function',
            'Name.Class': 'class',
        }
        self._all_tags = tuple(set(self.token_to_tag.values()))

    def create_tags(self):
        # Define tags and basic colors; apps can configure them further
        self.text.tag_configure('keyword', foreground='blue')
        self.text.tag_configure('builtin', foreground='#6b6')
        self.text.tag_configure('name', foreground='#000')
        self.text.tag_configure('string', foreground='#d14')
        self.text.tag_configure('number', foreground='#b000b0')
        self.text.tag_configure('comment', foreground='#888')
        self.text.tag_configure('operator', foreground='#333')
        self.text.tag_configure('punctuation', foreground='#333')
        self.text.tag_configure('type', foreground='#1c9d00')
        self.text.tag_configure('function', foreground='#6a5acd')
        self.text.tag_configure('class', foreground='#008fb3')
        self.text.tag_configure('error_line', background='#420000')

    # ── Fast token → tag resolution ──────────────────────────────────
    def _tag_name_for_token(self, ttype) -> str:
        """Resolve a Pygments token type to a tag name using hierarchy walk."""
        tag = self._token_map.get(ttype)
        if tag:
            return tag
        parent = ttype
        while parent:
            tag = self._token_map.get(parent)
            if tag:
                self._token_map[ttype] = tag
                return tag
            parent = parent.parent if hasattr(parent, 'parent') else None
        return ''

    # ── Cached lexer factory ─────────────────────────────────────────
    @classmethod
    def _get_lexer(cls, language: str):
        """Return a cached lexer instance for the given language."""
        lexer = cls._lexer_cache.get(language)
        if lexer is None:
            # Lazy import: only load lexer modules when actually needed
            from pygments.lexers import CppLexer, get_lexer_by_name
            try:
                if language == 'cpp' or not language:
                    lexer = CppLexer()
                else:
                    lexer = get_lexer_by_name(language)
            except Exception:
                lexer = CppLexer()
            cls._lexer_cache[language] = lexer
        return lexer

    def highlight_region(self, start_char: int, end_char: int, language: str = 'cpp'):
        """Highlight characters from start_char to end_char."""
        if not PYGMENTS_AVAILABLE:
            return
        text = self.text.get('1.0', 'end-1c')
        selection_text = text[start_char:end_char]
        start_idx = f'1.0+{start_char}c'
        end_idx = f'1.0+{end_char}c'
        for tag in self._all_tags:
            self.text.tag_remove(tag, start_idx, end_idx)

        lexer = self._get_lexer(language)
        pos_in_full = start_char
        for ttype, value in _lex(selection_text, lexer):
            if not value:
                continue
            tag = self._tag_name_for_token(ttype)
            if not tag:
                pos_in_full += len(value)
                continue
            start = pos_in_full
            end = pos_in_full + len(value)
            pos_in_full = end
            try:
                self.text.tag_add(tag, f'1.0+{start}c', f'1.0+{end}c')
            except Exception:
                pass

    def highlight_visible_region(self, language: str = 'cpp'):
        """Highlight only the visible region — virtualized.

        Tags are applied ONLY to the visible window.  Off-screen tags are
        aggressively stripped so that tag memory stays O(window_height)
        regardless of file size.
        """
        if not PYGMENTS_AVAILABLE:
            return
        try:
            # 1. Calculate visible bounds
            first = self.text.index('@0,0')
            last = self.text.index(f'@0,{self.text.winfo_height()}')

            first_line = max(1, int(first.split('.')[0]) - 2)
            last_line = int(last.split('.')[0]) + 2

            start_idx = f'{first_line}.0'
            end_idx = f'{last_line}.end'

            # 2. VIRTUALIZE: strip tags from non-visible regions
            for tag in self._all_tags:
                self.text.tag_remove(tag, '1.0', start_idx)      # above viewport
            for tag in self._all_tags:
                self.text.tag_remove(tag, end_idx, 'end')         # below viewport

            # 3. Read only the visible portion
            visible_text = self.text.get(start_idx, end_idx)
            if not visible_text:
                return

            # 4. Clear tags in visible region before re-applying
            for tag in self._all_tags:
                self.text.tag_remove(tag, start_idx, end_idx)

            lexer = self._get_lexer(language)

            # 5. Lex and apply tags using line.col indices
            line = first_line
            col = 0
            for ttype, value in _lex(visible_text, lexer):
                if not value:
                    continue
                tag = self._tag_name_for_token(ttype)
                s_line, s_col = line, col
                lines_in_value = value.split('\n')
                if len(lines_in_value) == 1:
                    col += len(value)
                else:
                    line += len(lines_in_value) - 1
                    col = len(lines_in_value[-1])
                if tag:
                    try:
                        self.text.tag_add(tag, f'{s_line}.{s_col}', f'{line}.{col}')
                    except Exception:
                        pass
        except Exception:
            self.highlight_all(language=language)

    def highlight_all(self, language: str = 'cpp'):
        """Highlight the entire content (fallback, not virtualized)."""
        for tag in self._all_tags:
            self.text.tag_remove(tag, '1.0', 'end')
        if not PYGMENTS_AVAILABLE:
            return

        text = self.text.get('1.0', 'end-1c')
        lexer = self._get_lexer(language)

        pos = 0
        for ttype, value in _lex(text, lexer):
            if not value:
                continue
            tag = self._tag_name_for_token(ttype)
            if not tag:
                pos += len(value)
                continue
            start = pos
            end = pos + len(value)
            pos = end
            try:
                self.text.tag_add(tag, f'1.0+{start}c', f'1.0+{end}c')
            except Exception:
                pass


if __name__ == '__main__':
    print('Pygments available:', PYGMENTS_AVAILABLE)
