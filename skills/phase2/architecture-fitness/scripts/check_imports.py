#!/usr/bin/env python3
"""
check_imports.py — Architecture fitness: import boundary and circular import checker.

Reads .fitness.yml for layer boundary configuration, scans Python source files,
detects circular imports, and enforces layer boundary rules.

Usage:
    python check_imports.py [--root PATH] [--config PATH]
    python check_imports.py --help

Exit codes:
    0 — all checks pass
    1 — one or more violations found
"""

import ast
import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        print(f"[check_imports] No .fitness.yml found at {config_path} — skipping checks")
        sys.exit(0)
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def load_exceptions(root: Path) -> set:
    """Return a set of (file_rel_path, imported_module) pairs that are excepted."""
    exc_path = root / ".fitness-exceptions.yml"
    if not exc_path.exists():
        return set()
    with open(exc_path) as f:
        data = yaml.safe_load(f) or {}
    from datetime import date
    today = date.today()
    excepted = set()
    for exc in data.get("exceptions", []):
        if exc.get("rule") != "layer_boundary":
            continue
        expires = exc.get("expires")
        if expires and str(expires) < str(today):
            print(f"WARN  exception expired: {exc.get('location')} (expired {expires})")
            continue
        excepted.add(exc.get("location", ""))
    return excepted


def collect_python_files(root: Path) -> List[Path]:
    files = []
    for p in root.rglob("*.py"):
        # Skip test files and virtual environments
        parts = p.parts
        if any(part in ("test", "tests", "venv", ".venv", "__pycache__", "site-packages") for part in parts):
            continue
        files.append(p)
    return files


def extract_imports(filepath: Path, root: Path) -> List[str]:
    """Return list of absolute module paths imported by this file."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                if node.level == 0:
                    imports.append(node.module)
                else:
                    # Relative import — resolve against current package
                    pkg_parts = filepath.relative_to(root).parent.parts
                    if node.level <= len(pkg_parts):
                        base = ".".join(pkg_parts[: len(pkg_parts) - node.level + 1])
                        imports.append(f"{base}.{node.module}" if base else node.module)
    return imports


def module_to_layer(module: str, layers: dict) -> Optional[str]:
    """Return the layer name for a module, or None if not in any defined layer."""
    top = module.split(".")[0]
    for layer in layers:
        if top == layer:
            return layer
    return None


def file_to_layer(filepath: Path, root: Path, layers: dict) -> Optional[str]:
    try:
        rel = filepath.relative_to(root)
    except ValueError:
        return None
    top = rel.parts[0] if rel.parts else ""
    return top if top in layers else None


def detect_circular_imports(import_graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Return list of cycles found using DFS."""
    visited = set()
    rec_stack = set()
    cycles = []

    def dfs(node, path):
        visited.add(node)
        rec_stack.add(node)
        for neighbour in import_graph.get(node, set()):
            if neighbour not in visited:
                dfs(neighbour, path + [neighbour])
            elif neighbour in rec_stack:
                cycle_start = path.index(neighbour)
                cycles.append(path[cycle_start:] + [neighbour])
        rec_stack.discard(node)

    for node in list(import_graph.keys()):
        if node not in visited:
            dfs(node, [node])
    return cycles


def main():
    parser = argparse.ArgumentParser(
        description="Architecture fitness: check import boundaries and circular imports."
    )
    parser.add_argument("--root", default=".", help="Repo root directory (default: current directory)")
    parser.add_argument("--config", default=".fitness.yml", help="Path to .fitness.yml (default: .fitness.yml)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config_path = root / args.config if not Path(args.config).is_absolute() else Path(args.config)
    config = load_config(config_path)
    import_rules = config.get("import_rules", {})

    check_circular = import_rules.get("no_circular_imports", False)
    layer_boundaries = import_rules.get("layer_boundaries", {})

    if not check_circular and not layer_boundaries:
        print("[check_imports] No import rules enabled in .fitness.yml — nothing to check")
        sys.exit(0)

    files = collect_python_files(root)
    print(f"[check_imports] Scanning {len(files)} Python files...")

    exceptions = load_exceptions(root)

    # Derive module names for every project file so we can filter intra-project imports.
    def _file_to_module(fp: Path) -> str:
        rel_parts = list(fp.relative_to(root).parts)
        if rel_parts[-1] == "__init__.py":
            rel_parts = rel_parts[:-1]
        elif rel_parts[-1].endswith(".py"):
            rel_parts[-1] = rel_parts[-1][:-3]
        return ".".join(rel_parts)

    project_modules: Set[str] = set()
    for fp in files:
        try:
            project_modules.add(_file_to_module(fp))
        except ValueError:
            pass

    # Build two graphs:
    # import_graph  — top-level dir → set of top-level dirs (for boundary checks)
    # module_graph  — module.path → set of module.paths (for circular detection,
    #                 includes same-package imports that import_graph drops)
    import_graph: Dict[str, Set[str]] = defaultdict(set)
    module_graph: Dict[str, Set[str]] = defaultdict(set)
    file_imports: Dict[Path, List[str]] = {}

    for filepath in files:
        imports = extract_imports(filepath, root)
        file_imports[filepath] = imports
        try:
            rel = str(filepath.relative_to(root))
            top = rel.split(os.sep)[0]
            src_module = _file_to_module(filepath)
        except ValueError:
            continue
        for imp in imports:
            imp_top = imp.split(".")[0]
            if imp_top and imp_top != top:
                import_graph[top].add(imp_top)
            # Module graph: only track imports that resolve to a project file.
            if imp in project_modules:
                module_graph[src_module].add(imp)

    violations = []

    # Check circular imports using the fine-grained module graph so that
    # same-package cycles (app.a ↔ app.b) are detected, not just cross-package ones.
    if check_circular:
        cycles = detect_circular_imports(module_graph)
        if cycles:
            for cycle in cycles[:5]:  # Report first 5 cycles
                violations.append(f"circular_import: {' → '.join(cycle)}")
        pass_circular = len(cycles) == 0
        cycle_count = len(cycles)
    else:
        pass_circular = None
        cycle_count = 0

    # Check layer boundaries
    boundary_violations = []
    if layer_boundaries:
        for filepath, imports in file_imports.items():
            try:
                rel = filepath.relative_to(root)
            except ValueError:
                continue
            rel_str = str(rel)
            src_layer = rel.parts[0] if rel.parts else ""
            if src_layer not in layer_boundaries:
                continue
            allowed = set(layer_boundaries.get(src_layer, []))
            for imp in imports:
                imp_top = imp.split(".")[0]
                if imp_top in layer_boundaries and imp_top not in allowed and imp_top != src_layer:
                    if rel_str in exceptions:
                        continue
                    msg = f"layer_boundary — {rel_str} imports {imp_top}/ ({src_layer} → {imp_top} not allowed)"
                    boundary_violations.append(msg)
                    violations.append(msg)

    # Report results
    exit_code = 0

    if check_circular:
        if pass_circular:
            print(f"PASS  no_circular_imports   {cycle_count} cycles detected")
        else:
            print(f"FAIL  no_circular_imports   {cycle_count} cycle(s) detected")
            for v in violations:
                if v.startswith("circular_import"):
                    print(f"  VIOLATION: {v}")
            exit_code = 1

    if layer_boundaries:
        if not boundary_violations:
            print("PASS  layer_boundaries      all boundaries respected")
        else:
            print(f"FAIL  layer_boundaries      {len(boundary_violations)} violation(s)")
            for v in boundary_violations:
                print(f"  VIOLATION: {v}")
            exit_code = 1

    if exit_code == 0:
        print("Exit: 0")
    else:
        print(f"Exit: {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
