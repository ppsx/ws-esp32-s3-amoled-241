#!/usr/bin/env python3
"""Compare consolidated benchmark JSON outputs from rm690b0/displayio suites."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

CORE_METRICS = (
    "full_fill",
    "full_fill_bw",
    "partial_rect",
    "partial_rect_bw",
    "scene_mixed",
    "text_menu",
    "text_large",
    "blit_band",
    "blit_band_bw",
    "sprite_opaque",
    "sprite_transparent",
)

BACKEND_SPECIFIC_METRICS = (
    "retained_sprite",
    "retained_text",
    "retained_transparent",
)


class Dataset:
    def __init__(self, source: Path, label: str, payload: dict):
        self.source = source
        self.label = label
        self.payload = payload
        self.backend = payload.get("backend", "UNKNOWN")
        self.profile = payload.get("profile", "unknown")
        self.system = payload.get("system", "unknown")
        self.note = payload.get("note", "")
        self.values: Dict[Tuple[str, str], dict] = {}
        for row in payload.get("results", []):
            group = row.get("group", "DISPLAYIO")
            metric = row.get("label")
            if metric:
                self.values[(group, metric)] = row

    def groups(self) -> List[str]:
        groups = []
        for group, _metric in self.values.keys():
            if group not in groups:
                groups.append(group)
        return groups


def parse_dataset_arg(arg: str) -> Tuple[str | None, Path]:
    if "=" in arg:
        label, path_str = arg.split("=", 1)
        if label and path_str:
            return label, Path(path_str)
    return None, Path(arg)


def derive_label(path: Path, payload: dict) -> str:
    backend = payload.get("backend", "UNKNOWN")
    profile = payload.get("profile", "unknown")
    return "%s/%s" % (backend, profile)


def load_datasets(args: Iterable[str]) -> List[Dataset]:
    datasets = []
    for arg in args:
        forced_label, path = parse_dataset_arg(arg)
        payload = json.loads(path.read_text())
        label = forced_label or derive_label(path, payload)
        datasets.append(Dataset(path, label, payload))
    return datasets


def collect_columns(datasets: List[Dataset]) -> List[Tuple[Dataset, str, str]]:
    columns = []
    seen = set()
    for ds in datasets:
        groups = ds.groups() or ["DISPLAYIO"]
        multi = len(groups) > 1
        for group in groups:
            heading = "%s:%s" % (ds.label, group) if multi else ds.label
            key = (heading, str(ds.source))
            if key in seen:
                continue
            seen.add(key)
            columns.append((ds, group, heading))
    return columns


def format_value(row: dict | None) -> str:
    if not row:
        return "-"
    metric = row.get("metric")
    value = row.get("value", 0)
    if metric == "fps":
        return "%.2f FPS" % value
    if metric == "mp_s":
        return "%.2f MP/s" % value
    if metric == "ms":
        return "%.2f ms" % value
    return str(value)


def make_table(title: str, metrics: Iterable[str], columns: List[Tuple[Dataset, str, str]]) -> str:
    rows = []
    metric_list = list(metrics)
    active_metrics = []
    for metric in metric_list:
        if any((group, metric) in ds.values for ds, group, _heading in columns):
            active_metrics.append(metric)
    if not active_metrics:
        return ""

    headers = ["metric"] + [heading for _ds, _group, heading in columns]
    widths = [len(h) for h in headers]
    rendered = []
    for metric in active_metrics:
        row = [metric]
        for ds, group, _heading in columns:
            row.append(format_value(ds.values.get((group, metric))))
        rendered.append(row)
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    lines = [title]
    header_line = " | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(headers))
    sep_line = "-+-".join("-" * widths[idx] for idx in range(len(headers)))
    lines.append(header_line)
    lines.append(sep_line)
    for row in rendered:
        lines.append(" | ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(row)))
    return "\n".join(lines)


def make_sources_block(columns: List[Tuple[Dataset, str, str]]) -> str:
    lines = ["Sources"]
    seen = set()
    for ds, group, heading in columns:
        key = (heading, str(ds.source))
        if key in seen:
            continue
        seen.add(key)
        lines.append("- %s" % heading)
        lines.append("  file: %s" % ds.source)
        lines.append("  backend/profile: %s/%s" % (ds.backend, ds.profile))
        lines.append("  system: %s" % ds.system)
        if group:
            lines.append("  group: %s" % group)
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: benchmark_compare.py [label=]path1.json [label=]path2.json ...")
        print("Example: benchmark_compare.py fb=fb_standard.json dl=dl_standard.json dio=displayio_standard.json")
        return 1

    datasets = load_datasets(argv[1:])
    columns = collect_columns(datasets)

    print("=" * 88)
    print("Consolidated Benchmark Comparison")
    print("=" * 88)
    print(make_sources_block(columns))
    print()
    core_table = make_table("Core Comparable Metrics", CORE_METRICS, columns)
    if core_table:
        print(core_table)
        print()
    backend_table = make_table("Backend-Specific Metrics", BACKEND_SPECIFIC_METRICS, columns)
    if backend_table:
        print(backend_table)
        print()

    print("Notes")
    print("- Compare core metrics across FB-SINGLE, FB-DOUBLE, DL and DISPLAYIO.")
    print("- Compare backend-specific metrics only within rm690b0 backends that implement them.")
    print("- For routine checks prefer standard-vs-standard, not mixed profiles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
