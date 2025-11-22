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
# C++ Editor & Compiler (SCC)

A lightweight C++ code editor and compiler implemented in Python using Tkinter with comprehensive syntax highlighting and configuration support.

## Features

- **File Operations**: New, Open, Save, Save As
- **Advanced Line Numbers**: Dynamic width adjustment, scroll synchronization
- **Comprehensive C++ Syntax Highlighting**:
  - All C++ keywords (C++17/20 compatible)
  - Built-in types and standard library types
  - Preprocessor directives
  - Numbers (integers, floats, hex, binary)
  - Strings and comments
  - Configurable colors via JSON
- **Build System**:
  - Compile with g++ (configurable compiler and flags)
  - Run compiled executables
  - Compile & Run in one step
  - Stop running processes
- **Smart Features**:
  - Inline code suggestions (C++ keywords, file symbols, std names)
  - Quick diagnostics (unmatched braces/parentheses, unclosed quotes)
  - Error highlighting in editor
  - Unsaved changes protection
- **Fully Configurable**: All settings stored in `config.json`

## Requirements

- Python 3.8+
- g++ (GNU C++ compiler)
- Tkinter (usually included with Python; on Linux: `python3-tk`)
- Pygments (optional, for enhanced syntax highlighting): `pip install -r requirements.txt`

## Installation

```bash
# Clone or download the repository
cd scc

# (Optional) Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python3 scc.py
```

### Quick Start

1. Open the editor with `python3 scc.py`
2. Use **File → New/Open** to create or open C++ files
3. Use the **Build** toolbar button to:
   - **Compile**: Build your code
   - **Run**: Execute the last compiled binary
   - **Compile && Run**: Build and execute in one step
4. Use **Stop** to terminate running processes

## Configuration

All settings are stored in `config.json`. You can customize:

### Editor Settings
```json
{
  "editor": {
    "font": "Consolas",
    "font_size": 12,
    "wrap": "none",
    "line_number_width": 5,
    "line_number_bg": "#f0f0f0",
    "line_number_fg": "gray"
  }
}
```

### Compiler Settings
```json
{
  "compiler": {
    "command": "g++",
    "flags": ["-std=c++17", "-Wall"],
    "timeout": 20
  }
}
```

### Syntax Highlighting
```json
{
  "syntax": {
    "keywords": ["if", "else", "for", "while", ...],
    "types": ["int", "float", "bool", ...],
    "std_types": ["string", "vector", "map", ...],
    "colors": {
      "keyword": "#0000ff",
      "type": "#1c9d00",
      "comment": "#888888",
      ...
    }
  }
}
```

See `config.json` for the complete configuration schema.

## Features in Detail

### Line Numbering
- Dynamic width adjustment based on file size
- Synchronized scrolling with editor
- Updates automatically on text changes

### Syntax Highlighting
- Over 80 C++ keywords supported
- Standard library types recognition
- Preprocessor directive highlighting
- Number literal detection (int, float, hex, binary)
- Proper string and comment parsing
- Uses Pygments when available, falls back to regex-based highlighting

### Build System
- Unified build execution system
- Configurable compiler and flags
- Temporary file management for unsaved code
- Error parsing and line highlighting
- Configurable execution timeout

### Code Suggestions
- Context-aware C++ keyword completion
- File symbol detection
- Standard library type suggestions
- Quick fixes for common errors

## Notes

- Executables are created next to the source file (or as temporary files)
- The editor supports C++ only
- For advanced features (LSP, debugging), consider integrating with `clangd`
- Temporary files are automatically cleaned up

## License

MIT License - adapt and reuse as you like.
