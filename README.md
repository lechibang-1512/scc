# C++ Editor & Compiler (Python Tkinter)

Lightweight C++ editor and compiler written in Python using Tkinter.

## Features
- New/Open/Save/Save As
- Line numbers
- C++ syntax highlighting (Pygments if installed, otherwise a simple fallback)
- Compile with g++ and show compiler errors
- Run the compiled executable and capture stdout/stderr
- Inline suggestions (C++ only): C++ keywords, file symbols, and limited std names
- Quick diagnostics (unmatched braces/quotes, naive missing semicolon suggestions)
- Stop a running compile or executable process
- Unsaved-changes protection (prompt on close/new/open)

## Requirements
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

## Usage
1. Run the editor:
```bash
python3 cpp_editor.py
```
2. Open or edit `.cpp` files.
3. Save, then Build -> Compile, or Build -> Compile & Run.

## Notes
- On Linux, executables will be created next to the source file with the same base name.
- The app focuses on C++; suggestion and highlighting are targeted for C++ only.
- For deep semantic analysis and smart completions, integrate a full language server like `clangd`.

## License
MIT
