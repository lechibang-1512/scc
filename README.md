# C++ Editor & Compiler (Python Tkinter)

Lightweight single-file README placeholder.
# C++ Editor & Compiler (Python Tkinter)

Lightweight C++ editor and compiler written in Python using Tkinter.

Features
- New/Open/Save/Save As
- Line numbers
- C++ syntax highlighting (Pygments if installed, otherwise a simple fallback)
- Compile with g++ and show compiler errors
- Run the compiled executable and capture stdout/stderr
- Inline suggestions (C++ only): C++ keywords, file symbols, and limited std names
- Quick diagnostics (unmatched braces/quotes, naive missing semicolon suggestions)
- Stop a running compile or executable process
- Unsaved-changes protection (prompt on close/new/open)

Requirements
- Python 3.8+
- g++ (GNU C++ compiler)
- Tkinter (for the GUI; on Linux, install python3-tk or equivalent)
- Pygments (optional, for robust syntax highlighting). Install via `pip install -r requirements.txt`.

Tip: Use a virtual environment. Always activate `.venv` before installing requirements or running the editor:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Usage
1. Run the editor:
```bash
python3 cpp_editor.py
```
2. Open or edit `.cpp` files (e.g., `hello.cpp`).
3. Save, then Build -> Compile, or Build -> Compile & Run.

Notes
- This editor focuses on C++; suggestion and highlighting are targeted for C++ only.
- For deep semantic analysis and smart completions, integrate a full language server like `clangd`.

License
MIT
# C++ Editor & Compiler (Python Tkinter)

Lightweight C++ editor and compiler written in Python using Tkinter.

Features
- New/Open/Save/Save As
- Line numbers
- C++ syntax highlighting (Pygments if installed, otherwise a simple fallback)
- Compile with g++ and show compiler errors
- Run the compiled executable and capture stdout/stderr
- Inline suggestions (C++ only): C++ keywords, file symbols, and limited std names
- Quick diagnostics (unmatched braces/quotes, naive missing semicolon suggestions)
- Stop a running compile or executable process
- Unsaved-changes protection (prompt on close/new/open)

Requirements
- Python 3.8+
- g++ (GNU C++ compiler)
- Tkinter (for the GUI; on Linux, install python3-tk or equivalent)
- Pygments (optional, for robust syntax highlighting). Install via `pip install -r requirements.txt`.

Tip: Use a virtual environment. Always activate `.venv` before installing requirements or running the editor:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Usage
1. Run the editor:
```bash
python3 cpp_editor.py
```
2. Open or edit `.cpp` files (e.g., `hello.cpp`).
3. Save, then Build -> Compile, or Build -> Compile & Run.

Notes
- This editor focuses on C++; suggestion and highlighting are targeted for C++ only.
- For deep semantic analysis and smart completions, integrate a full language server like `clangd`.

License
MIT
# C++ Editor & Compiler (Python Tkinter)

Lightweight C++ editor and compiler written in Python using Tkinter.

Features
- New/Open/Save/Save As
- Line numbers
- C++ syntax highlighting (Pygments if installed, otherwise a simple fallback)
- Compile with g++ and show compiler errors
- Run the compiled executable and capture stdout/stderr
- Inline suggestions (C++ only): C++ keywords, file symbols, and limited std names
- Quick diagnostics (unmatched braces/quotes, naive missing semicolon suggestions)
- Stop a running compile or executable process
- Unsaved-changes protection (prompt on close/new/open)

Requirements
- Python 3.8+
- g++ (GNU C++ compiler)
- Tkinter (for the GUI; on Linux, install python3-tk or equivalent)
- Pygments (optional, for robust syntax highlighting). Install via `pip install -r requirements.txt`.

Tip: Use a virtual environment. Always activate `.venv` before installing requirements or running the editor:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Usage
1. Run the editor:
```bash
python3 cpp_editor.py
```
2. Open or edit `.cpp` files (e.g., `hello.cpp`).
3. Save, then Build -> Compile, or Build -> Compile & Run.

Notes
- This editor focuses on C++; suggestion and highlighting are targeted for C++ only.
- For deep semantic analysis and smart completions, integrate a full language server like `clangd`.

License
MIT
# C++ Editor & Compiler (Python Tkinter)

Lightweight C++ editor and compiler written in Python using Tkinter.

Features
- New/Open/Save/Save As
- Line numbers
- C++ syntax highlighting (Pygments if installed, otherwise a simple fallback)
- Compile with g++ and show compiler errors
- Run the compiled executable and capture stdout/stderr
- Inline suggestions (C++ only): C++ keywords, file symbols, and limited std names
- Quick diagnostics (unmatched braces/quotes, naive missing semicolon suggestions)
- Stop a running compile or executable process
- Unsaved-changes protection (prompt on close/new/open)

Requirements
- Python 3.8+
- g++ (GNU C++ compiler)
- Tkinter (for the GUI; on Linux, install python3-tk or equivalent)
- Pygments (optional, for robust syntax highlighting). Install via `pip install -r requirements.txt`.

Tip: Use a virtual environment. Always activate `.venv` before installing requirements or running the editor:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Usage
1. Run the editor:
```bash
python3 cpp_editor.py
```
2. Open or edit `.cpp` files (e.g., `hello.cpp`).
3. Save, then Build -> Compile, or Build -> Compile & Run.

Notes
- This editor focuses on C++; suggestion and highlighting are targeted for C++ only.
- For deep semantic analysis and smart completions, integrate a full language server like `clangd`.

License
MIT
# C++ Editor & Compiler (Python Tkinter)

This small tool is a C++ code editor and compiler implemented in Python using Tkinter.

Features
- New/Open/Save/Save As
- Basic syntax highlighting for C++ (keywords, types, strings, comments)
- Line numbers
- Compile with g++ and show compiler errors
- Run the compiled executable and capture stdout/stderr

- Python 3.8+
- g++ (GNU C++ compiler)
- Tkinter (for the GUI; on Linux, install python3-tk or equivalent)
- Pygments (for robust syntax highlighting). Install via `pip install -r requirements.txt`.
Requirements
- Python 3.8+
- g++ (GNU C++ compiler)
- Tkinter (for the GUI; on Linux, install python3-tk or equivalent)
- Pygments (optional, for robust syntax highlighting). Install via `pip install -r requirements.txt`.

Tip: Use a virtual environment. Always activate `.venv` before installing requirements or running the editor:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- Python 3.8+
- g++ (GNU C++ compiler)
- Tkinter (for the GUI; on Linux, install python3-tk or equivalent)
- Pygments (for robust syntax highlighting). Install via `pip install -r requirements.txt`.

Usage
1. Run the editor:
```bash
python3 cpp_editor.py
```
2. Use File -> Open to open `hello.cpp` or create a new file.
3. Save your file (`.cpp`) then use Build -> Compile to compile it.
4. On successful compilation use Build -> Run to run or Build -> Compile & Run to do both.

- On Linux, executables will be created next to the source file with the same base name.
- The app performs minimal syntax highlighting and error parsing; it aims to be simple and educational.
Notes
- On Linux, executables will be created next to the source file with the same base name.
- The app can use Pygments for improved syntax highlighting if `Pygments` is installed; otherwise it falls back to a simple regex-based highlighter.
- Features added: C++ highlighting, Stop button (to kill compile/run processes), partial visible-region highlighting for performance, and unsaved-changes detection with prompt on close/new/open.

- In-line suggestions: type an identifier prefix to see possible completions; accept with Tab or Enter, navigate with Up/Down. Suggestions include C++ keywords, identifiers found in the current file, and a limited set of common std names.
 - Quick diagnostics and quick fixes: as-you-type diagnosis detects unmatched braces/parentheses and unclosed quotes, highlights the problematic lines, and suggests simple quick fixes (e.g., Add ';') which can be accepted in-place via the suggestion box.
- On Linux, executables will be created next to the source file with the same base name.
- The app performs minimal syntax highlighting and error parsing; it aims to be simple and educational.

License
MIT; adapt & reuse as you like.
