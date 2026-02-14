#!/usr/bin/env python3
"""
benchmark.py — Performance benchmark suite for SCC Editor

Measures CPU time, memory usage (RSS + tracemalloc), storage footprint,
and read/write I/O for every major subsystem.

Usage:
    python3 benchmark.py              # Run all benchmarks
    python3 benchmark.py --json       # Output raw JSON results
    python3 benchmark.py --help       # Show help
"""

import gc
import json
import os
import resource
import sys
import tempfile
import time
import tracemalloc

# ── Optional deps ────────────────────────────────────────────────────
try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

# ── Paths ────────────────────────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

# ── Helpers ──────────────────────────────────────────────────────────

def _fmt_bytes(n):
    """Human-readable byte size."""
    for unit in ('B', 'KB', 'MB', 'GB'):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _fmt_time(s):
    if s < 0.001:
        return f"{s * 1_000_000:.0f} µs"
    if s < 1:
        return f"{s * 1_000:.2f} ms"
    return f"{s:.3f} s"


def _rss_bytes():
    """Current RSS via /proc or psutil."""
    if _PSUTIL:
        return psutil.Process().memory_info().rss
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except Exception:
        pass
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


def _io_counters():
    """Return (read_bytes, write_bytes) or None."""
    if _PSUTIL:
        try:
            io = psutil.Process().io_counters()
            return io.read_bytes, io.write_bytes
        except Exception:
            pass
    try:
        with open(f"/proc/{os.getpid()}/io") as f:
            data = {}
            for line in f:
                k, v = line.split(":")
                data[k.strip()] = int(v.strip())
            return data.get("read_bytes", 0), data.get("write_bytes", 0)
    except Exception:
        return None


def _cpu_percent_snapshot():
    """Return CPU percent (over a short interval) or None."""
    if _PSUTIL:
        p = psutil.Process()
        p.cpu_percent()  # prime
        time.sleep(0.1)
        return p.cpu_percent()
    return None


# ── Generate test data ───────────────────────────────────────────────

def _generate_cpp_code(lines=1000):
    """Generate a realistic C++ source file of the given line count."""
    chunks = []
    chunks.append('#include <iostream>\n#include <vector>\n#include <string>\nusing namespace std;\n\n')
    func_count = 0
    i = len(chunks[0].splitlines())
    while i < lines:
        func_count += 1
        body = [
            f'int function_{func_count}(int x, double y) {{',
            f'    // compute result for function {func_count}',
            f'    string msg = "hello from function_{func_count}";',
            f'    vector<int> data = {{1, 2, 3, 4, 5}};',
            f'    int result = 0;',
            f'    for (int j = 0; j < static_cast<int>(data.size()); j++) {{',
            f'        result += data[j] * x;',
            f'        if (result > 1000) {{',
            f'            cout << msg << " overflow at " << j << endl;',
            f'            return -1;',
            f'        }}',
            f'    }}',
            f'    /* multi-line',
            f'       comment block */',
            f'    return result;',
            f'}}',
            f'',
        ]
        chunks.append('\n'.join(body) + '\n')
        i += len(body)

    chunks.append('\nint main() {\n')
    for f in range(1, func_count + 1):
        chunks.append(f'    cout << function_{f}(1, 2.0) << endl;\n')
    chunks.append('    return 0;\n}\n')
    return ''.join(chunks)


# ── Benchmark functions ──────────────────────────────────────────────

class BenchmarkResult:
    __slots__ = ('name', 'cpu_time', 'wall_time', 'mem_before', 'mem_after',
                 'mem_peak', 'tracemalloc_peak', 'io_read', 'io_write',
                 'extra', 'cpu_percent')

    def __init__(self, name):
        self.name = name
        self.cpu_time = 0.0
        self.wall_time = 0.0
        self.mem_before = 0
        self.mem_after = 0
        self.mem_peak = 0
        self.tracemalloc_peak = 0
        self.io_read = 0
        self.io_write = 0
        self.cpu_percent = None
        self.extra = {}

    def to_dict(self):
        d = {
            'name': self.name,
            'cpu_time_s': round(self.cpu_time, 6),
            'wall_time_s': round(self.wall_time, 6),
            'mem_before_bytes': self.mem_before,
            'mem_after_bytes': self.mem_after,
            'mem_delta_bytes': self.mem_after - self.mem_before,
            'tracemalloc_peak_bytes': self.tracemalloc_peak,
            'io_read_bytes': self.io_read,
            'io_write_bytes': self.io_write,
        }
        if self.cpu_percent is not None:
            d['cpu_percent'] = self.cpu_percent
        if self.extra:
            d['extra'] = self.extra
        return d


def _run_bench(name, func, *args, **kwargs):
    """Run a benchmark function with full instrumentation."""
    gc.collect()
    gc.collect()

    r = BenchmarkResult(name)
    r.mem_before = _rss_bytes()
    io_before = _io_counters()

    tracemalloc.start()
    t0_cpu = time.process_time()
    t0_wall = time.perf_counter()

    result = func(*args, **kwargs)

    t1_cpu = time.process_time()
    t1_wall = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    r.cpu_time = t1_cpu - t0_cpu
    r.wall_time = t1_wall - t0_wall
    r.mem_after = _rss_bytes()
    r.tracemalloc_peak = peak

    io_after = _io_counters()
    if io_before and io_after:
        r.io_read = io_after[0] - io_before[0]
        r.io_write = io_after[1] - io_before[1]

    if isinstance(result, dict):
        r.extra = result

    return r


# ── Individual benchmarks ────────────────────────────────────────────

def bench_import_startup():
    """Measure importing core modules (no Tkinter, no GUI)."""
    # Remove cached modules so import is fresh
    for mod in list(sys.modules):
        if mod in ('syntax_highlighter', 'extension_api', 'extension_manager'):
            del sys.modules[mod]

    def _do():
        import syntax_highlighter  # noqa: F401
        import extension_api  # noqa: F401
        import extension_manager  # noqa: F401
        return {
            'pygments_available': syntax_highlighter.PYGMENTS_AVAILABLE,
            'note': 'Pygments is lazy-loaded — should be False at import time',
        }

    return _run_bench("1. Module Import (no GUI)", _do)


def bench_pygments_lazy_load():
    """Measure the cost of first Pygments load."""
    for mod in list(sys.modules):
        if 'pygments' in mod:
            del sys.modules[mod]
    import syntax_highlighter
    # Reset the lazy flags
    syntax_highlighter.PYGMENTS_AVAILABLE = False
    syntax_highlighter.Token = None
    syntax_highlighter._lex = None

    def _do():
        syntax_highlighter._ensure_pygments()
        return {'pygments_loaded': syntax_highlighter.PYGMENTS_AVAILABLE}

    return _run_bench("2. Pygments Lazy Load", _do)


def bench_lexer_creation():
    """Measure cached vs uncached lexer creation."""
    import syntax_highlighter
    syntax_highlighter._ensure_pygments()
    syntax_highlighter.SyntaxHighlighter._lexer_cache.clear()

    def _do():
        times = {}
        # First call — cold cache
        t0 = time.perf_counter()
        syntax_highlighter.SyntaxHighlighter._get_lexer('cpp')
        times['cold_cache_ms'] = round((time.perf_counter() - t0) * 1000, 3)

        # Second call — warm cache
        t0 = time.perf_counter()
        for _ in range(1000):
            syntax_highlighter.SyntaxHighlighter._get_lexer('cpp')
        times['warm_cache_1000x_ms'] = round((time.perf_counter() - t0) * 1000, 3)
        return times

    return _run_bench("3. Lexer Cache (cold vs warm)", _do)


def bench_syntax_highlighting():
    """Measure syntax highlighting on a 1000-line C++ file (headless lex only)."""
    import syntax_highlighter
    syntax_highlighter._ensure_pygments()
    if not syntax_highlighter.PYGMENTS_AVAILABLE:
        r = BenchmarkResult("4. Syntax Highlighting (1000 lines)")
        r.extra = {'skipped': 'Pygments not available'}
        return r

    from pygments.lexers import CppLexer
    code = _generate_cpp_code(1000)
    lexer = CppLexer()

    def _do():
        tokens = list(syntax_highlighter._lex(code, lexer))
        return {
            'lines': code.count('\n'),
            'chars': len(code),
            'tokens': len(tokens),
        }

    return _run_bench("4. Syntax Highlighting (1000 lines)", _do)


def bench_syntax_highlighting_large():
    """Measure on 10,000-line file."""
    import syntax_highlighter
    syntax_highlighter._ensure_pygments()
    if not syntax_highlighter.PYGMENTS_AVAILABLE:
        r = BenchmarkResult("5. Syntax Highlighting (10,000 lines)")
        r.extra = {'skipped': 'Pygments not available'}
        return r

    from pygments.lexers import CppLexer
    code = _generate_cpp_code(10000)
    lexer = CppLexer()

    def _do():
        tokens = list(syntax_highlighter._lex(code, lexer))
        return {
            'lines': code.count('\n'),
            'chars': len(code),
            'tokens': len(tokens),
        }

    return _run_bench("5. Syntax Highlighting (10,000 lines)", _do)


def bench_extension_loading():
    """Measure extension discovery and metadata parsing."""

    def _do():
        import extension_manager
        # Re-instantiate to test fresh load
        em = extension_manager.ExtensionManager.__new__(extension_manager.ExtensionManager)
        em.editor = None
        em.extensions = {}
        em._active = []
        em._marketplace_cache = None
        em._marketplace_mtime = 0

        # Benchmark marketplace listing (metadata parse)
        t0 = time.perf_counter()
        listings = em.list_marketplace()
        t_list = time.perf_counter() - t0

        # Benchmark second call (cached)
        t0 = time.perf_counter()
        listings2 = em.list_marketplace()
        t_cached = time.perf_counter() - t0

        return {
            'extensions_found': len(listings),
            'first_list_ms': round(t_list * 1000, 3),
            'cached_list_ms': round(t_cached * 1000, 3),
            'speedup': f"{t_list / max(t_cached, 1e-9):.1f}x",
        }

    return _run_bench("6. Extension Discovery & Caching", _do)


def bench_file_io():
    """Measure file read/write performance with various sizes."""

    def _do():
        results = {}
        for size_label, lines in [('100 lines', 100), ('1K lines', 1000), ('10K lines', 10000)]:
            code = _generate_cpp_code(lines)
            code_bytes = len(code.encode('utf-8'))

            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False,
                                              dir=PROJECT_DIR) as f:
                tmppath = f.name

            # Write benchmark
            t0 = time.perf_counter()
            with open(tmppath, 'w', encoding='utf-8') as f:
                f.write(code)
            write_time = time.perf_counter() - t0

            # Read benchmark
            t0 = time.perf_counter()
            with open(tmppath, 'r', encoding='utf-8') as f:
                _ = f.read()
            read_time = time.perf_counter() - t0

            file_size = os.path.getsize(tmppath)
            os.unlink(tmppath)

            results[size_label] = {
                'file_size': _fmt_bytes(file_size),
                'file_size_bytes': file_size,
                'write_ms': round(write_time * 1000, 3),
                'read_ms': round(read_time * 1000, 3),
                'write_throughput': _fmt_bytes(code_bytes / max(write_time, 1e-9)) + '/s',
                'read_throughput': _fmt_bytes(code_bytes / max(read_time, 1e-9)) + '/s',
            }
        return results

    return _run_bench("7. File I/O (Read & Write)", _do)


def bench_undo_stack_memory():
    """Simulate undo stack growth with maxundo=50 vs unlimited."""

    def _do():
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()

        results = {}

        # Test with maxundo=50 (our optimization)
        t_capped = tk.Text(root, undo=True, maxundo=50, autoseparators=False)
        t_capped.pack()
        gc.collect()
        mem_before = _rss_bytes()
        for i in range(500):
            t_capped.insert('end', f'Line {i}: some text content here\n')
            t_capped.edit_separator()
        gc.collect()
        mem_after = _rss_bytes()
        # Test undo works
        undo_count = 0
        try:
            while True:
                t_capped.edit_undo()
                undo_count += 1
        except tk.TclError:
            pass
        results['capped_50'] = {
            'mem_delta': _fmt_bytes(mem_after - mem_before),
            'mem_delta_bytes': mem_after - mem_before,
            'undo_steps_available': undo_count,
            'insertions': 500,
        }
        t_capped.destroy()

        # Test with unlimited undo
        t_unlimited = tk.Text(root, undo=True, autoseparators=True)
        t_unlimited.pack()
        gc.collect()
        mem_before = _rss_bytes()
        for i in range(500):
            t_unlimited.insert('end', f'Line {i}: some text content here\n')
        gc.collect()
        mem_after = _rss_bytes()
        undo_count = 0
        try:
            while True:
                t_unlimited.edit_undo()
                undo_count += 1
        except tk.TclError:
            pass
        results['unlimited'] = {
            'mem_delta': _fmt_bytes(mem_after - mem_before),
            'mem_delta_bytes': mem_after - mem_before,
            'undo_steps_available': undo_count,
            'insertions': 500,
        }
        t_unlimited.destroy()
        root.destroy()
        return results

    return _run_bench("8. Undo Stack (capped vs unlimited)", _do)


def bench_output_buffer_cap():
    """Simulate output buffer growth and verify cap at 2000 lines."""

    def _do():
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        output = tk.Text(root, state='disabled')
        output.pack()

        gc.collect()
        mem_before = _rss_bytes()

        # Simulate output_write with capping logic
        for i in range(5000):
            output.config(state='normal')
            if int(float(output.index('end'))) > 2000:
                output.delete('1.0', '500.0')
            output.insert('end', f'[output] Line {i}: Compilation result message\n')
            output.config(state='disabled')

        gc.collect()
        mem_after = _rss_bytes()
        final_lines = int(float(output.index('end'))) - 1

        output.destroy()
        root.destroy()
        return {
            'lines_written': 5000,
            'final_lines_in_buffer': final_lines,
            'buffer_capped': final_lines <= 2000,
            'mem_delta': _fmt_bytes(mem_after - mem_before),
            'mem_delta_bytes': mem_after - mem_before,
        }

    return _run_bench("9. Output Buffer Cap (5000→2000 lines)", _do)


def bench_tag_virtualization():
    """Measure tag memory: full-file tags vs virtualized (visible-only) tags."""

    def _do():
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()

        code = _generate_cpp_code(2000)
        results = {}

        # Scenario A: Tags on ALL lines (old behavior)
        t_full = tk.Text(root)
        t_full.pack()
        t_full.insert('1.0', code)
        gc.collect()
        mem_before = _rss_bytes()
        line_count = int(t_full.index('end').split('.')[0])
        for i in range(1, line_count):
            t_full.tag_add('keyword', f'{i}.0', f'{i}.3')
            t_full.tag_add('string', f'{i}.5', f'{i}.10')
            t_full.tag_add('comment', f'{i}.12', f'{i}.end')
        gc.collect()
        mem_after = _rss_bytes()
        tag_ranges_full = len(t_full.tag_ranges('keyword'))
        results['full_file_tags'] = {
            'mem_delta': _fmt_bytes(mem_after - mem_before),
            'mem_delta_bytes': mem_after - mem_before,
            'tag_ranges': tag_ranges_full,
        }
        t_full.destroy()

        # Scenario B: Tags on only 60 visible lines (virtualized)
        t_virt = tk.Text(root)
        t_virt.pack()
        t_virt.insert('1.0', code)
        gc.collect()
        mem_before = _rss_bytes()
        visible_start, visible_end = 500, 560
        for i in range(visible_start, visible_end):
            t_virt.tag_add('keyword', f'{i}.0', f'{i}.3')
            t_virt.tag_add('string', f'{i}.5', f'{i}.10')
            t_virt.tag_add('comment', f'{i}.12', f'{i}.end')
        gc.collect()
        mem_after = _rss_bytes()
        tag_ranges_virt = len(t_virt.tag_ranges('keyword'))
        results['virtualized_tags'] = {
            'mem_delta': _fmt_bytes(mem_after - mem_before),
            'mem_delta_bytes': mem_after - mem_before,
            'tag_ranges': tag_ranges_virt,
            'visible_lines': visible_end - visible_start,
        }
        t_virt.destroy()
        root.destroy()

        # Summary
        results['improvement'] = {
            'tag_ranges_ratio': f"{tag_ranges_full}/{tag_ranges_virt}",
            'note': 'Virtualized tags cover only visible lines (O(window) not O(file))',
        }
        return results

    return _run_bench("10. Tag Virtualization (full vs visible)", _do)


def bench_storage_footprint():
    """Measure on-disk footprint of the project."""

    def _do():
        results = {}
        total_size = 0
        file_count = 0
        by_category = {
            'core': {'pattern': ['cpp_editor.py', 'extension_api.py', 'extension_manager.py',
                                  'extension_marketplace.py', 'syntax_highlighter.py'], 'size': 0, 'count': 0},
            'extensions': {'pattern': 'extensions/', 'size': 0, 'count': 0},
            'marketplace': {'pattern': 'marketplace/', 'size': 0, 'count': 0},
            'other_py': {'pattern': '.py', 'size': 0, 'count': 0},
        }

        for root_dir, dirs, files in os.walk(PROJECT_DIR):
            # Skip hidden dirs and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root_dir, fname)
                fsize = os.path.getsize(fpath)
                total_size += fsize
                file_count += 1
                relpath = os.path.relpath(fpath, PROJECT_DIR)

                if fname in by_category['core']['pattern']:
                    by_category['core']['size'] += fsize
                    by_category['core']['count'] += 1
                elif relpath.startswith('extensions/'):
                    by_category['extensions']['size'] += fsize
                    by_category['extensions']['count'] += 1
                elif relpath.startswith('marketplace/'):
                    by_category['marketplace']['size'] += fsize
                    by_category['marketplace']['count'] += 1
                else:
                    by_category['other_py']['size'] += fsize
                    by_category['other_py']['count'] += 1

        results['total'] = {'files': file_count, 'size': _fmt_bytes(total_size), 'size_bytes': total_size}
        for cat, info in by_category.items():
            results[cat] = {'files': info['count'], 'size': _fmt_bytes(info['size']), 'size_bytes': info['size']}

        return results

    return _run_bench("11. Storage Footprint", _do)


def bench_process_overview():
    """Snapshot of current process metrics."""
    r = BenchmarkResult("0. Process Overview")
    r.mem_after = _rss_bytes()
    r.cpu_percent = _cpu_percent_snapshot()
    r.extra = {
        'pid': os.getpid(),
        'rss': _fmt_bytes(r.mem_after),
        'python_version': sys.version.split()[0],
        'psutil_available': _PSUTIL,
    }
    if _PSUTIL:
        p = psutil.Process()
        r.extra['threads'] = p.num_threads()
        r.extra['open_files'] = len(p.open_files())
        try:
            io = p.io_counters()
            r.extra['total_read'] = _fmt_bytes(io.read_bytes)
            r.extra['total_write'] = _fmt_bytes(io.write_bytes)
        except Exception:
            pass
    return r


# ── Report formatting ────────────────────────────────────────────────

_DIVIDER = "═" * 78
_THIN_DIV = "─" * 78


def print_report(results):
    print()
    print(_DIVIDER)
    print("  SCC Editor — Performance Benchmark Report")
    print(_DIVIDER)
    print()

    for r in results:
        d = r.to_dict()
        print(f"  ▸ {r.name}")
        print(f"    {'CPU time:':<22} {_fmt_time(r.cpu_time):<16} {'Wall time:':<14} {_fmt_time(r.wall_time)}")

        mem_delta = r.mem_after - r.mem_before
        line = f"    {'Memory (RSS):':<22} {_fmt_bytes(r.mem_after):<16}"
        if mem_delta != 0:
            sign = '+' if mem_delta > 0 else ''
            line += f" {'Δ RSS:':<14} {sign}{_fmt_bytes(mem_delta)}"
        print(line)

        if r.tracemalloc_peak > 0:
            print(f"    {'tracemalloc peak:':<22} {_fmt_bytes(r.tracemalloc_peak)}")

        if r.io_read > 0 or r.io_write > 0:
            print(f"    {'I/O read:':<22} {_fmt_bytes(r.io_read):<16} {'I/O write:':<14} {_fmt_bytes(r.io_write)}")

        if r.cpu_percent is not None:
            print(f"    {'CPU %:':<22} {r.cpu_percent:.1f}%")

        if r.extra:
            print(f"    {'Details:':<22}")
            _print_extra(r.extra, indent=6)

        print(f"  {_THIN_DIV}")

    print()
    print(_DIVIDER)
    print("  Benchmark complete")
    print(_DIVIDER)
    print()


def _print_extra(data, indent=6):
    prefix = ' ' * indent
    for k, v in data.items():
        if isinstance(v, dict):
            print(f"{prefix}{k}:")
            _print_extra(v, indent + 4)
        else:
            print(f"{prefix}{k}: {v}")


# ── Main ─────────────────────────────────────────────────────────────

def main():
    json_mode = '--json' in sys.argv
    if '--help' in sys.argv:
        print(__doc__)
        return

    print("\n  ⏳ Running SCC Editor benchmarks...\n")

    # Determine which benchmarks need Tkinter (GUI tests)
    has_display = bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))

    benchmarks_no_gui = [
        bench_process_overview,
        bench_import_startup,
        bench_pygments_lazy_load,
        bench_lexer_creation,
        bench_syntax_highlighting,
        bench_syntax_highlighting_large,
        bench_extension_loading,
        bench_file_io,
        bench_storage_footprint,
    ]

    benchmarks_gui = [
        bench_undo_stack_memory,
        bench_output_buffer_cap,
        bench_tag_virtualization,
    ]

    results = []
    for fn in benchmarks_no_gui:
        try:
            r = fn()
            results.append(r)
            print(f"  ✓ {r.name}")
        except Exception as e:
            print(f"  ✗ {fn.__name__}: {e}")

    if has_display:
        for fn in benchmarks_gui:
            try:
                r = fn()
                results.append(r)
                print(f"  ✓ {r.name}")
            except Exception as e:
                print(f"  ✗ {fn.__name__}: {e}")
    else:
        print("\n  ⚠  No DISPLAY — skipping GUI benchmarks (undo, output, tags)")

    print()

    # Sort by name
    results.sort(key=lambda r: r.name)

    if json_mode:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        print_report(results)

    # Save JSON to file
    report_path = os.path.join(PROJECT_DIR, 'benchmark_results.json')
    with open(report_path, 'w') as f:
        json.dump([r.to_dict() for r in results], f, indent=2)
    print(f"  📄 JSON results saved to: {report_path}\n")


if __name__ == '__main__':
    main()
