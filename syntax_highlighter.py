"""
syntax_highlighter.py

Use Pygments to perform robust syntax highlighting for a Tkinter Text widget.
Falls back to a simple tag-based approach if Pygments is not installed.
"""
from typing import Dict, Any

try:
    from pygments import lex
    from pygments.lexers import CppLexer, get_lexer_by_name
    from pygments.token import Token
    PYGMENTS_AVAILABLE = True
except Exception:
    PYGMENTS_AVAILABLE = False
    Token = None  # type: ignore


class SyntaxHighlighter:
    # ── Lexer cache (shared across instances) ────────────────────────
    _lexer_cache: Dict[str, Any] = {}

    def __init__(self, text_widget):
        self.text = text_widget
        # Build a direct Token-type → tag-name lookup for O(1) resolution.
        # Uses the actual Pygments Token hierarchy instead of string matching.
        self._token_map: Dict[Any, str] = {}
        if PYGMENTS_AVAILABLE:
            self._token_map = {
                Token.Keyword:          'keyword',
                Token.Keyword.Type:     'type',
                Token.Name.Builtin:     'builtin',
                Token.Name:             'name',
                Token.Name.Function:    'function',
                Token.Name.Class:       'class',
                Token.Literal.String:   'string',
                Token.Literal.Number:   'number',
                Token.Comment:          'comment',
                Token.Comment.Single:   'comment',
                Token.Comment.Multiline:'comment',
                Token.Comment.Preproc:  'comment',
                Token.Operator:         'operator',
                Token.Punctuation:      'punctuation',
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
        # Direct lookup first (O(1) for known types)
        tag = self._token_map.get(ttype)
        if tag:
            return tag
        # Walk up the token type hierarchy (e.g. Token.Keyword.Reserved → Token.Keyword)
        parent = ttype
        while parent:
            tag = self._token_map.get(parent)
            if tag:
                # Cache for future hits
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
        """Highlight characters from start_char to end_char in the Text widget using tokens.

        start_char and end_char are character offsets relative to the start of widget content.
        """
        if not PYGMENTS_AVAILABLE:
            return
        text = self.text.get('1.0', 'end-1c')
        selection_text = text[start_char:end_char]
        # remove tags in the region for tags we use
        start_idx = f'1.0+{start_char}c'
        end_idx = f'1.0+{end_char}c'
        for tag in self._all_tags:
            self.text.tag_remove(tag, start_idx, end_idx)

        lexer = self._get_lexer(language)

        # Lex selection and apply tags with offsets
        pos_in_full = start_char
        for ttype, value in lex(selection_text, lexer):
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
        """Highlight only the visible region of the text widget, for efficiency.

        Reads only the visible text instead of the full document.
        """
        if not PYGMENTS_AVAILABLE:
            return
        try:
            # Get first and last visible line indices
            first = self.text.index('@0,0')
            last = self.text.index(f'@0,{self.text.winfo_height()}')

            # Extend range slightly for context (tokenizer accuracy)
            first_line = max(1, int(first.split('.')[0]) - 2)
            last_line = int(last.split('.')[0]) + 2

            start_idx = f'{first_line}.0'
            end_idx = f'{last_line}.end'

            # Read only the visible portion of text
            visible_text = self.text.get(start_idx, end_idx)
            if not visible_text:
                return

            # Remove old tags in the visible region
            for tag in self._all_tags:
                self.text.tag_remove(tag, start_idx, end_idx)

            lexer = self._get_lexer(language)

            # Lex and apply tags using line.col indices directly
            line = first_line
            col = 0
            for ttype, value in lex(visible_text, lexer):
                if not value:
                    continue
                tag = self._tag_name_for_token(ttype)

                # Calculate start index
                s_line, s_col = line, col

                # Advance position through the value
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
            # On any exception, fallback to highlight_all
            self.highlight_all(language=language)

    def highlight_all(self, language: str = 'cpp'):
        """Highlight the entire content of the widget using Pygments (if available).

        This computes token spans and applies text widget tags accordingly.
        """
        # Remove existing tags (just the ones we use)
        for tag in self._all_tags:
            self.text.tag_remove(tag, '1.0', 'end')
        # If no Pygments, bail
        if not PYGMENTS_AVAILABLE:
            return

        text = self.text.get('1.0', 'end-1c')
        lexer = self._get_lexer(language)

        pos = 0
        for ttype, value in lex(text, lexer):
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
