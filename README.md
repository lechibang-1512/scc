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
 - Features added: per-language highlighting select (C++, C, Python, Java, Javascript), Stop button (to kill compile/run processes), partial visible-region highlighting for performance, and unsaved-changes detection with prompt on close/new/open.
- On Linux, executables will be created next to the source file with the same base name.
- The app performs minimal syntax highlighting and error parsing; it aims to be simple and educational.

License
MIT; adapt & reuse as you like.
