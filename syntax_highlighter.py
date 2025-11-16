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
    # Keep imports local in fallback if needed


class SyntaxHighlighter:
    def __init__(self, text_widget):
        self.text = text_widget
        # Map pygments token types to tag names
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

    def _tag_name_for_token(self, ttype) -> str:
        # ttype is a pygments token object; convert to human form
        name = str(ttype)
        # map based on known forms
        for k, tag in self.token_to_tag.items():
            # match token suffix if present
            if name.endswith(k):
                return tag
        return 'name'

    def highlight_region(self, start_char: int, end_char: int, language: str = 'cpp'):
        """Highlight characters from start_char to end_char in the Text widget using tokens.

        start_char and end_char are character offsets relative to the start of widget content.
        """
        if not PYGMENTS_AVAILABLE:
            return
        text = self.text.get('1.0', 'end-1c')
        selection_text = text[start_char:end_char]
        # remove tags in the region for tags we use
        for tag in set(self.token_to_tag.values()):
            self.text.tag_remove(tag, f'1.0+{start_char}c', f'1.0+{end_char}c')

        try:
            if language and language != 'cpp':
                lexer = get_lexer_by_name(language)
            else:
                lexer = CppLexer()
        except Exception:
            lexer = CppLexer()

        # Lex selection and apply tags with offsets
        pos_in_full = start_char
        for ttype, value in lex(selection_text, lexer):
            tag = self._tag_name_for_token(ttype)
            if not value:
                continue
            start = pos_in_full
            end = pos_in_full + len(value)
            pos_in_full = end
            start_index = f'1.0+{start}c'
            end_index = f'1.0+{end}c'
            try:
                self.text.tag_add(tag, start_index, end_index)
            except Exception:
                pass

    def highlight_visible_region(self, language: str = 'cpp'):
        """Highlight only the visible region of the text widget, for efficiency.

        Uses Text widget coordinates to compute a visible range.
        """
        try:
            # get first and last visible indices
            first = self.text.index('@0,0')
            last = self.text.index(f'@0,{self.text.winfo_height()}')
            # convert to char offsets
            # index 'line.char' convert to absolute char index by computing content before that index
            full_text = self.text.get('1.0', 'end-1c')
            def idx_to_charpos(idx):
                line, col = map(int, idx.split('.'))
                # compute char offset
                lines = full_text.splitlines(True)
                # clamp
                if line-1 >= len(lines):
                    return len(full_text)
                offset = sum(len(l) for l in lines[:line-1]) + col
                return offset
            start_char = idx_to_charpos(first)
            end_char = idx_to_charpos(last)
            if end_char < start_char:
                end_char = start_char + 1
            self.highlight_region(start_char, end_char, language=language)
        except Exception:
            # On any exception, fallback to highlight_all
            self.highlight_all(language=language)

    def highlight_all(self, language: str = 'cpp'):
        """Highlight the entire content of the widget using Pygments (if available).

        This computes token spans and applies text widget tags accordingly.
        """
        text = self.text.get('1.0', 'end-1c')
        # remove existing tags (just the ones we use)
        for tag in set(self.token_to_tag.values()):
            self.text.tag_remove(tag, '1.0', 'end')
        # If no Pygments, bail
        if not PYGMENTS_AVAILABLE:
            return
        try:
            if language and language != 'cpp':
                lexer = get_lexer_by_name(language)
            else:
                lexer = CppLexer()
        except Exception:
            lexer = CppLexer()

        pos = 0
        for ttype, value in lex(text, lexer):
            tag = self._tag_name_for_token(ttype)
            if not value:
                continue
            # Calculate start/end index in chars
            start = pos
            end = pos + len(value)
            pos = end
            if tag:
                start_index = f'1.0+{start}c'
                end_index = f'1.0+{end}c'
                try:
                    self.text.tag_add(tag, start_index, end_index)
                except Exception:
                    # In case of widget/position issues, ignore
                    pass


if __name__ == '__main__':
    print('Pygments available:', PYGMENTS_AVAILABLE)
