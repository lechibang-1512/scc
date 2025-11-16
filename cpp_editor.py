#!/usr/bin/env python3
"""
A lightweight C++ editor/compile-run app in Python (Tkinter)

Features:
- New/Open/Save/Save As
- Basic syntax highlighting for C++
- Line numbers
- Compile (g++) with captured compiler errors
- Run compiled executable (capture stdout/stderr)
- Compile & Run flow
"""
import os
import re
from typing import Optional
import shlex
import subprocess
import tempfile
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


class CppEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('C++ Editor & Compiler')
        self.current_file = None
        self._build_ui()
        self._bind_events()
        # Start with an example C++ snippet
        # Initialize highlight_timer before calling update_highlight in set_text
        self.highlight_timer = None
        # process management
        self.current_process: Optional[subprocess.Popen] = None
        # track if editor buffer is modified (unsaved changes)
        self.dirty = False
        self.set_text(self.default_cpp())
        self.update_highlight()

    def _build_ui(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=False)
        filemenu.add_command(label='New', command=self.new_file)
        filemenu.add_command(label='Open', command=self.open_file)
        filemenu.add_command(label='Save', command=self.save_file)
        filemenu.add_command(label='Save As', command=self.save_file_as)
        filemenu.add_separator()
        filemenu.add_command(label='Exit', command=self.root.quit)
        menubar.add_cascade(label='File', menu=filemenu)

        buildmenu = tk.Menu(menubar, tearoff=False)
        buildmenu.add_command(label='Compile', command=self.compile_code)
        buildmenu.add_command(label='Run', command=self.run_program)
        buildmenu.add_command(label='Compile & Run', command=self.compile_and_run)
        menubar.add_cascade(label='Build', menu=buildmenu)

        self.root.config(menu=menubar)

        # Top frame: code editor with line numbers
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill='both', expand=True)

        self.line_numbers = tk.Text(top_frame, width=5, padx=3, takefocus=0, bd=0, bg='#f0f0f0', fg='gray', state='disabled')
        self.line_numbers.pack(side='left', fill='y')

        self.text = tk.Text(top_frame, wrap='none', undo=True, font=('Consolas', 12))
        self.text.pack(side='left', fill='both', expand=True)

        xscroll = tk.Scrollbar(self.root, orient='horizontal', command=self.text.xview)
        xscroll.pack(fill='x')
        self.text.configure(xscrollcommand=xscroll.set)

        side_frame = tk.Frame(self.root)
        side_frame.pack(fill='x')
        btn_compile = tk.Button(side_frame, text='Compile', command=self.compile_code)
        btn_compile.pack(side='left', padx=6, pady=6)
        btn_run = tk.Button(side_frame, text='Run', command=self.run_program)
        btn_run.pack(side='left', padx=6, pady=6)
        btn_crun = tk.Button(side_frame, text='Compile && Run', command=self.compile_and_run)
        btn_crun.pack(side='left', padx=6, pady=6)
        btn_stop = tk.Button(side_frame, text='Stop', command=self.stop_current_process)
        btn_stop.pack(side='left', padx=6, pady=6)

        # language selector for highlighting
        lang_label = tk.Label(side_frame, text='Highlight:')
        lang_label.pack(side='left', padx=(12, 4))
        self.lang_var = tk.StringVar(value='cpp')
        self.lang_combo = ttk.Combobox(side_frame, values=['cpp', 'c', 'python', 'java', 'javascript'], width=10, textvariable=self.lang_var)
        self.lang_combo.pack(side='left')

        self.status_var = tk.StringVar()
        self.status_var.set('Ready')
        status = tk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w')
        status.pack(side='bottom', fill='x')

        # Output console
        self.output = tk.Text(self.root, height=12, bg='#111111', fg='#ffffff', font=('Consolas', 11))
        self.output.pack(fill='both')
        self.output.insert('end', 'Output console available.\n')
        self.output.configure(state='disabled')

        # Syntax highlight tags (base config)
        self.text.tag_configure('error_line', background='#420000')

        # Try to use external SyntaxHighlighter (Pygments) if available
        try:
            import syntax_highlighter as sh
            if getattr(sh, 'PYGMENTS_AVAILABLE', False):
                from syntax_highlighter import SyntaxHighlighter
                self.highlighter = SyntaxHighlighter(self.text)
                self.highlighter.create_tags()
            else:
                self.highlighter = None
        except Exception:
            self.highlighter = None
        # Basic tags fallback if no Pygments-based highlighter
        if not self.highlighter:
            self.text.tag_configure('keyword', foreground='blue')
            self.text.tag_configure('type', foreground='#1c9d00')
            self.text.tag_configure('string', foreground='#d14')
            self.text.tag_configure('comment', foreground='#888')

    def _bind_events(self):
        self.text.bind('<KeyRelease>', lambda e: (self.set_dirty(True), self.update_highlight()))
        self.text.bind('<Button-1>', lambda e: self.update_line_numbers())
        self.text.bind('<MouseWheel>', lambda e: self.update_line_numbers())
        self.text.bind('<Return>', lambda e: self.update_line_numbers())
        self.lang_combo.bind('<<ComboboxSelected>>', lambda e: self.update_highlight())

        # Bind close event to check for unsaved changes
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

    def default_cpp(self):
        return r"""#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}
"""

    def new_file(self):
        if not self.confirm_discard():
            return
        self.current_file = None
        self.set_text('')
        self.status_var.set('New file')

    def confirm_discard(self):
        # Ask user to confirm if there are unsaved changes
        if not self.dirty:
            return True
        resp = messagebox.askyesnocancel('Unsaved changes', 'You have unsaved changes. Save before continuing?')
        if resp is None:
            # cancel
            return False
        if resp is True:
            return self.save_file()
        # resp is False -> discard
        return True

    def set_dirty(self, v: bool):
        self.dirty = v
        # also set Tk edit modified flag for compatibility
        try:
            self.text.edit_modified(bool(v))
        except Exception:
            pass

    def open_file(self):
        path = filedialog.askopenfilename(title='Open C++ file', filetypes=[('C++ Files', '*.cpp *.hpp *.h *.cc *.c'), ('All Files', '*.*')])
        if path:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                self.set_text(f.read())
            self.current_file = path
            self.status_var.set(f'Opened {os.path.basename(path)}')

    def save_file(self):
        if self.current_file is None:
            return self.save_file_as()
        text = self.get_text()
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(text)
        self.status_var.set(f'Saved {os.path.basename(self.current_file)}')
        self.set_dirty(False)
        return True

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension='.cpp', filetypes=[('C++ Files', '*.cpp *.hpp *.h *.cc *.c'), ('All Files', '*.*')])
        if not path:
            return False
        self.current_file = path
        return self.save_file()

    def set_text(self, txt):
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', txt)
        self.update_line_numbers()
        self.update_highlight()
        # Reset dirty flag when setting text programmatically
        self.set_dirty(False)

    def get_text(self):
        return self.text.get('1.0', 'end-1c')

    def update_line_numbers(self):
        content = self.get_text().splitlines()
        width = len(str(max(1, len(content))))
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        for i in range(1, len(content) + 1):
            self.line_numbers.insert('end', f'{i}'.rjust(width) + '\n')
        self.line_numbers.config(state='disabled')

    def update_highlight(self):
        if self.highlight_timer:
            self.root.after_cancel(self.highlight_timer)
        self.highlight_timer = self.root.after(150, self._highlight)

    def _highlight(self):
        # Use external Pygments-based SyntaxHighlighter if available
        if self.highlighter:
            # make sure prior tags are cleared by highlighter
            lang = getattr(self, 'lang_var', None) and self.lang_var.get() or 'cpp'
            try:
                # Prefer highlighting visible region for performance
                self.highlighter.highlight_visible_region(language=lang)
            except Exception:
                self.highlighter.highlight_all(language=lang)
            return

        # Fallback: basic regex highlight
        text = self.get_text()
        self.text.tag_remove('keyword', '1.0', 'end')
        self.text.tag_remove('type', '1.0', 'end')
        self.text.tag_remove('string', '1.0', 'end')
        self.text.tag_remove('comment', '1.0', 'end')
        # Basic highlights
        keywords = r'\b(if|else|for|while|return|break|continue|goto|switch|case|default|namespace|using|class|struct|template|typename|public|private|protected|virtual|override|constexpr)\b'
        types = r'\b(int|long|short|float|double|char|void|bool|unsigned|signed|size_t|auto)\b'
        for m in re.finditer(keywords, text):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            self.text.tag_add('keyword', start, end)
        for m in re.finditer(types, text):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            self.text.tag_add('type', start, end)
        # strings
        for m in re.finditer(r'(".*?"|\'.*?\')', text):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            self.text.tag_add('string', start, end)
        # comments // and /* */
        for m in re.finditer(r'//.*', text):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            self.text.tag_add('comment', start, end)
        for m in re.finditer(r'/\*.*?\*/', text, flags=re.DOTALL):
            start = f'1.0+{m.start()}c'
            end = f'1.0+{m.end()}c'
            self.text.tag_add('comment', start, end)

    def compile_code(self):
        if not self.save_file():
            return
        # Save the file if needed
        path = self.current_file
        if not path:
            messagebox.showerror('Error', 'Please save your source code first')
            return
        self.output_clear()
        self.status_var.set('Compiling...')
        threading.Thread(target=self._compile_thread, args=(path,), daemon=True).start()

    def _compile_thread(self, path):
        base, ext = os.path.splitext(path)
        out_exe = base  # without extension; on Linux, no .exe
        cmd = ['g++', '-std=c++17', path, '-o', out_exe]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.current_process = proc
            try:
                stdout, stderr = proc.communicate()
            finally:
                self.current_process = None
        except Exception as e:
            self.output_write(f'Error running g++: {e}\n')
            self.status_var.set('Compilation failed')
            return
        if proc.returncode != 0:
            self.output_write('Compiler returned errors:\n', clear=False)
            self.output_write(stderr)
            self.status_var.set('Compilation failed')
            self._parse_and_highlight_errors(stderr)
        else:
            self.output_write('Compilation succeeded.\n')
            self.status_var.set('Compiled')

    def _parse_and_highlight_errors(self, stderr_text):
        # Parse messages like: file.cpp:line:col: error: message
        # Simplify: highlight line numbers in the current editor
        for tag in ('error_line',):
            self.text.tag_remove(tag, '1.0', 'end')
        pattern = re.compile(r'(?P<file>[^:\s]+):(\s?)(?P<line>\d+):(\d+):\s(?P<kind>error|warning):\s(?P<msg>.*)')
        for m in pattern.finditer(stderr_text):
            file = m.group('file')
            line = int(m.group('line'))
            if self.current_file and os.path.basename(self.current_file) == os.path.basename(file):
                # highlight this line
                start = f'{line}.0'
                end = f'{line}.0 + 1 line'
                self.text.tag_add('error_line', start, end)


    def run_program(self):
        if self.current_file is None:
            messagebox.showerror('Error', 'Please save and compile your source file first.')
            return
        base, ext = os.path.splitext(self.current_file)
        exe = base
        if not os.path.exists(exe):
            messagebox.showerror('Error', 'Executable not found. Compile first.')
            return
        self.output_clear()
        self.status_var.set('Running...')
        threading.Thread(target=self._run_thread, args=(exe,), daemon=True).start()

    def _run_thread(self, exe):
        try:
            proc = subprocess.Popen([exe], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.current_process = proc
            try:
                stdout, stderr = proc.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                self.current_process = None
                self.output_write('\nProgram timed out (20s).\n')
                self.status_var.set('Program timed out')
                return
            self.current_process = None
        except subprocess.TimeoutExpired:
            self.output_write('\nProgram timed out (20s).\n')
            self.status_var.set('Program timed out')
            return
        except Exception as e:
            self.output_write(f'Error running program: {e}\n')
            self.status_var.set('Run failed')
            return
        if stdout:
            self.output_write(stdout)
        if stderr:
            self.output_write(stderr)
        try:
            retcode = proc.returncode
        except Exception:
            retcode = 0
        self.status_var.set(f'Execution finished (code {retcode})')

    def compile_and_run(self):
        if not self.save_file():
            return
        path = self.current_file
        self.output_clear()
        self.status_var.set('Compiling and running...')
        threading.Thread(target=self._compile_and_run_thread, args=(path,), daemon=True).start()

    def _compile_and_run_thread(self, path):
        base, ext = os.path.splitext(path)
        exe = base
        cmd = ['g++', '-std=c++17', path, '-o', exe]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.current_process = proc
            try:
                stdout, stderr = proc.communicate()
            finally:
                self.current_process = None
        except Exception as e:
            self.output_write(f'Error running g++: {e}\n')
            self.status_var.set('Compilation failed')
            return
        if proc.returncode != 0:
            self.output_write('Compilation failed:\n')
            self.output_write(stderr)
            self.status_var.set('Compilation failed')
            self._parse_and_highlight_errors(stderr)
            return
        self.output_write('Compilation succeeded. Running...\n')
        try:
            runproc = subprocess.Popen([exe], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.current_process = runproc
            try:
                out, err = runproc.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                runproc.kill()
                out, err = runproc.communicate()
                self.current_process = None
                self.output_write('\nProgram timed out (20s).\n')
                self.status_var.set('Program timed out')
                return
            self.current_process = None
        except subprocess.TimeoutExpired:
            self.output_write('\nProgram timed out (20s).\n')
            self.status_var.set('Program timed out')
            return
        except Exception as e:
            self.output_write(f'Error running program: {e}\n')
            self.status_var.set('Run failed')
            return
        if out:
            self.output_write(out)
        if err:
            self.output_write(err)
        try:
            ret = runproc.returncode
        except Exception:
            ret = 0
        self.status_var.set(f'Execution finished (code {ret})')

    def stop_current_process(self):
        proc = getattr(self, 'current_process', None)
        if proc is not None:
            try:
                proc.kill()
                self.output_write('\nProcess killed by user.\n')
                self.status_var.set('Stopped')
                self.current_process = None
            except Exception:
                pass

    def on_close(self):
        if self.confirm_discard():
            # Good to close
            try:
                self.root.destroy()
            except Exception:
                self.root.quit()

    def output_write(self, text, clear=False):
        def _write():
            if clear:
                self.output.config(state='normal')
                self.output.delete('1.0', 'end')
                self.output.config(state='disabled')
            self.output.config(state='normal')
            self.output.insert('end', text)
            self.output.see('end')
            self.output.config(state='disabled')
        self.root.after(0, _write)

    def output_clear(self):
        self.root.after(0, lambda: (self.output.config(state='normal'), self.output.delete('1.0', 'end'), self.output.config(state='disabled')))


def main():
    root = tk.Tk()
    app = CppEditorApp(root)
    root.minsize(640, 480)
    root.mainloop()


if __name__ == '__main__':
    main()
