#!/usr/bin/env python3
"""Render timeline JSON files into self-contained HTML visualizations."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from murder_she_inferred.settings import run_stage_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render timeline JSON files to HTML charts.",
    )
    parser.add_argument(
        "--run-root",
        type=Path,
        default=None,
        help="Optional numbered run root. Uses 03-timelines and 05-html under this root.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing *.timeline.json files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated HTML files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of episodes to render.",
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_name(value: Any) -> str:
    return str(value).strip()


def _all_suspects(events: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    for ev in events:
        for key in (
            "introduced",
            "eliminated",
            "active_suspects_after_chunk",
            "eliminated_suspects_after_chunk",
        ):
            for name in ev.get(key) or []:
                clean = _clean_name(name)
                if clean:
                    seen.add(clean)
    return sorted(seen)


def _chunk_sets(events: list[dict[str, Any]], key: str) -> list[set[str]]:
    return [{_clean_name(name) for name in (ev.get(key) or []) if _clean_name(name)} for ev in events]


def _suspect_sort_key(
    suspect: str,
    first_seen_at: dict[str, int],
    final_active: set[str],
) -> tuple[int, int, str]:
    return (
        0 if suspect in final_active else 1,
        first_seen_at.get(suspect, 10**9),
        suspect.lower(),
    )


def _ordered_suspects(events: list[dict[str, Any]]) -> list[str]:
    suspects = _all_suspects(events)
    active_by_chunk = _chunk_sets(events, "active_suspects_after_chunk")
    eliminated_by_chunk = _chunk_sets(events, "eliminated_suspects_after_chunk")
    introduced_by_chunk = _chunk_sets(events, "introduced")

    first_seen_at: dict[str, int] = {}
    for idx, names in enumerate(introduced_by_chunk):
        for name in names:
            first_seen_at.setdefault(name, idx)
    for idx, names in enumerate(active_by_chunk):
        for name in names:
            first_seen_at.setdefault(name, idx)
    for idx, names in enumerate(eliminated_by_chunk):
        for name in names:
            first_seen_at.setdefault(name, idx)

    final_active = active_by_chunk[-1] if active_by_chunk else set()
    return sorted(suspects, key=lambda suspect: _suspect_sort_key(suspect, first_seen_at, final_active))


def _state_matrix(events: list[dict[str, Any]], suspects: list[str]) -> list[list[str]]:
    """Return rows per suspect and columns per chunk with state labels."""
    rows: list[list[str]] = []
    active_by_chunk = _chunk_sets(events, "active_suspects_after_chunk")
    eliminated_by_chunk = _chunk_sets(events, "eliminated_suspects_after_chunk")
    introduced_by_chunk = _chunk_sets(events, "introduced")

    first_seen_at: dict[str, int] = {}
    for idx, names in enumerate(introduced_by_chunk):
        for name in names:
            first_seen_at.setdefault(name, idx)
    for idx, names in enumerate(active_by_chunk):
        for name in names:
            first_seen_at.setdefault(name, idx)
    for idx, names in enumerate(eliminated_by_chunk):
        for name in names:
            first_seen_at.setdefault(name, idx)

    for suspect in suspects:
        row: list[str] = []
        introduced_at = first_seen_at.get(suspect)
        for idx, ev in enumerate(events):
            active = active_by_chunk[idx]
            eliminated = eliminated_by_chunk[idx]
            if suspect in active:
                row.append("active")
            elif suspect in eliminated:
                row.append("eliminated")
            elif introduced_at is None or idx < introduced_at:
                row.append("not-introduced")
            else:
                row.append("inactive")
        rows.append(row)
    return rows


def _evidence_lookup(events: list[dict[str, Any]]) -> dict[tuple[int, str], set[str]]:
    lookup: dict[tuple[int, str], set[str]] = {}
    for idx, ev in enumerate(events):
        for item in ev.get("evidence") or []:
            if not isinstance(item, dict):
                continue
            character = _clean_name(item.get("character", ""))
            evidence_type = _clean_name(item.get("type", "")).lower()
            if not character or evidence_type not in {"implicates", "clears"}:
                continue
            lookup.setdefault((idx, character), set()).add(evidence_type)
    return lookup


def _evidence_groups(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for ev in events:
        notes: list[dict[str, str]] = []
        for item in ev.get("evidence") or []:
            if not isinstance(item, dict):
                continue
            evidence_type = _clean_name(item.get("type", "")).lower()
            character = _clean_name(item.get("character", ""))
            note = _clean_name(item.get("note", ""))
            if not character or evidence_type not in {"implicates", "clears"}:
                continue
            notes.append(
                {
                    "type": evidence_type,
                    "character": character,
                    "note": note,
                }
            )
        if notes:
            groups.append(
                {
                    "chunk_index": int(ev.get("chunk_index", -1)),
                    "notes": notes,
                }
            )
    return groups


def _page_chrome(title: str, body: str, extra_styles: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #f7f5ef;
      --ink: #122025;
      --muted: #61717f;
      --card: #ffffff;
      --line: #d7dde4;
      --active: #2f80ed;
      --eliminated: #94a3b8;
      --inactive: #dde6ec;
      --not-introduced: #f8fafc;
      --implicates: #c96d1a;
      --clears: #157f6b;
    }}
    body {{
      margin: 0;
      background: radial-gradient(circle at 20% 0%, #fff9e9 0%, var(--bg) 40%, #eef4f8 100%);
      color: var(--ink);
      font-family: "Avenir Next", "Helvetica Neue", Helvetica, sans-serif;
    }}
    .wrap {{
      max-width: 1300px;
      margin: 28px auto;
      padding: 0 18px 40px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 28px;
      letter-spacing: 0.3px;
    }}
    p.meta {{
      margin: 0 0 16px;
      color: var(--muted);
      font-size: 14px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      box-shadow: 0 8px 20px rgba(15, 25, 35, 0.06);
    }}
    .nav {{
      display: flex;
      gap: 10px;
      margin: 0 0 14px;
      flex-wrap: wrap;
    }}
    .nav a {{
      color: #0c5cc0;
      text-decoration: none;
      font-size: 13px;
      font-weight: 600;
    }}
    .nav a:hover {{
      text-decoration: underline;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 16px;
      font-size: 13px;
      background: #fff;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f0f4f7;
    }}
{extra_styles}
  </style>
</head>
<body>
  <div class="wrap">
{body}
  </div>
</body>
</html>
"""


def _render_heatmap_episode(payload: dict[str, Any], evidence_href: str) -> str:
    episode_id = str(payload.get("episode_id", "unknown-episode"))
    events = [e for e in (payload.get("events") or []) if isinstance(e, dict)]
    suspects = _ordered_suspects(events)
    matrix = _state_matrix(events, suspects)
    evidence_lookup = _evidence_lookup(events)
    chunks = len(events)

    cell_w = 26
    cell_h = 24
    left_pad = 260
    top_pad = 82
    width = left_pad + (chunks * cell_w) + 40
    height = top_pad + (max(1, len(suspects)) * cell_h) + 78

    svg_parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Suspect timeline for {html.escape(episode_id)}">'
    ]

    svg_parts.append(
        f'<text x="{left_pad}" y="22" font-size="14" font-weight="700" fill="#183642">'
        "Suspicion State Heatmap</text>"
    )
    svg_parts.append(
        f'<text x="{left_pad}" y="42" font-size="11" fill="#61717f">'
        "Markers show whether a chunk implicates or clears a suspect.</text>"
    )

    # Chunk labels
    for i in range(chunks):
        x = left_pad + i * cell_w + (cell_w / 2)
        if chunks <= 12 or i % 2 == 0:
            svg_parts.append(
                f'<text x="{x}" y="{top_pad - 14}" text-anchor="middle" '
                'font-size="10" fill="#335">c'
                f"{i}</text>"
            )
        svg_parts.append(
            f'<line x1="{x}" y1="{top_pad - 8}" x2="{x}" y2="{top_pad - 2}" '
            'stroke="#b7c4cf" stroke-width="1" />'
        )

    # Suspect labels and cells
    for r, suspect in enumerate(suspects):
        y = top_pad + r * cell_h
        safe_name = html.escape(suspect)
        svg_parts.append(
            f'<text x="{left_pad - 10}" y="{y + 16}" text-anchor="end" '
            'font-size="12" fill="#122">'
            f"{safe_name}</text>"
        )
        for c in range(chunks):
            state = matrix[r][c] if r < len(matrix) else "not-introduced"
            x = left_pad + c * cell_w
            if state == "active":
                fill = "#2f80ed"
            elif state == "eliminated":
                fill = "#94a3b8"
            elif state == "inactive":
                fill = "#dde6ec"
            else:
                fill = "#f8fafc"
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_w - 2}" height="{cell_h - 2}" '
                f'rx="4" fill="{fill}" stroke="#d6dbe1" />'
            )
            markers = evidence_lookup.get((c, suspect), set())
            if "implicates" in markers:
                svg_parts.append(
                    f'<circle cx="{x + 8}" cy="{y + 8}" r="4.2" fill="#c96d1a" '
                    'stroke="#fff7ed" stroke-width="1.2" />'
                )
            if "clears" in markers:
                svg_parts.append(
                    f'<circle cx="{x + cell_w - 10}" cy="{y + 8}" r="4.2" fill="#ffffff" '
                    'stroke="#157f6b" stroke-width="2" />'
                )
                svg_parts.append(
                    f'<line x1="{x + cell_w - 13}" y1="{y + 8}" '
                    f'x2="{x + cell_w - 7}" y2="{y + 8}" stroke="#157f6b" stroke-width="1.5" />'
        )

    svg_parts.append("</svg>")
    chart_svg = "\n".join(svg_parts)

    # Event table
    rows: list[str] = []
    for ev in events:
        idx = int(ev.get("chunk_index", -1))
        introduced = ", ".join(ev.get("introduced") or [])
        eliminated = ", ".join(ev.get("eliminated") or [])
        evidence = ev.get("evidence") or []
        evidence_txt = "; ".join(
            f"{e.get('type', '')}:{e.get('character', '')}" for e in evidence if isinstance(e, dict)
        )
        error = str(ev.get("error", "")).strip()
        rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td>{html.escape(introduced)}</td>"
            f"<td>{html.escape(eliminated)}</td>"
            f"<td>{html.escape(evidence_txt)}</td>"
            f"<td>{html.escape(error)}</td>"
            "</tr>"
        )

    body = f"""
    <h1>{html.escape(episode_id)}</h1>
    <div class="nav">
      <a href="{html.escape(evidence_href)}">View Evidence Ladder</a>
      <a href="index.html">Back to Index</a>
    </div>
    <p class="meta">Chunks: {chunks} | Suspects observed: {len(suspects)}</p>
    <div class="card">
      <div class="legend">
        <span><span class="swatch" style="background:var(--not-introduced)"></span>not introduced</span>
        <span><span class="swatch" style="background:var(--active)"></span>active</span>
        <span><span class="swatch" style="background:var(--eliminated)"></span>eliminated</span>
        <span><span class="swatch" style="background:var(--inactive)"></span>inactive after introduction</span>
        <span><span class="marker" style="background:var(--implicates)"></span>implicates</span>
        <span><span class="marker marker-clears"></span>clears</span>
      </div>
      {chart_svg}
    </div>
    <div class="card" style="margin-top:14px">
      <strong>Chunk Events</strong>
      <table>
        <thead>
          <tr>
            <th>chunk</th>
            <th>introduced</th>
            <th>eliminated</th>
            <th>evidence</th>
            <th>error</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </div>
"""
    extra_styles = """
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      margin: 8px 0 14px;
      font-size: 13px;
      color: var(--muted);
    }
    .swatch {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 1px solid var(--line);
      margin-right: 6px;
      vertical-align: -2px;
      border-radius: 4px;
    }
    .marker {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 999px;
      margin-right: 6px;
      vertical-align: -1px;
    }
    .marker-clears {
      width: 10px;
      height: 10px;
      border: 2px solid var(--clears);
      background: transparent;
    }
"""
    return _page_chrome(f"{episode_id} Timeline", body, extra_styles)


def _render_evidence_ladder_episode(payload: dict[str, Any], heatmap_href: str) -> str:
    episode_id = str(payload.get("episode_id", "unknown-episode"))
    events = [e for e in (payload.get("events") or []) if isinstance(e, dict)]
    groups = _evidence_groups(events)
    total_notes = sum(len(group["notes"]) for group in groups)
    implicates = sum(
        1
        for group in groups
        for note in group["notes"]
        if note["type"] == "implicates"
    )
    clears = sum(
        1
        for group in groups
        for note in group["notes"]
        if note["type"] == "clears"
    )

    if groups:
        sections: list[str] = []
        for group in groups:
            chunk_index = group["chunk_index"]
            note_items: list[str] = []
            for note in group["notes"]:
                chip_class = "chip-implicates" if note["type"] == "implicates" else "chip-clears"
                safe_character = html.escape(note["character"])
                safe_note = html.escape(note["note"] or "No note provided.")
                note_items.append(
                    '<li class="evidence-item">'
                    f'<span class="chip {chip_class}">{html.escape(note["type"])}</span>'
                    f'<strong>{safe_character}</strong>'
                    f'<p>{safe_note}</p>'
                    "</li>"
                )
            sections.append(
                '<section class="chunk-group">'
                f'<div class="chunk-label">Chunk {chunk_index}</div>'
                f'<ul class="evidence-list">{"".join(note_items)}</ul>'
                "</section>"
            )
        ladder_body = "".join(sections)
    else:
        ladder_body = (
            '<div class="card empty-state">'
            "<strong>No evidence annotations yet.</strong>"
            "<p>This episode produced no implicates or clears notes, so the ladder view has nothing to list yet.</p>"
            "</div>"
        )

    body = f"""
    <h1>{html.escape(episode_id)}</h1>
    <div class="nav">
      <a href="{html.escape(heatmap_href)}">View Heatmap</a>
      <a href="index.html">Back to Index</a>
    </div>
    <p class="meta">Evidence Impact Ladder</p>
    <div class="summary-grid">
      <div class="card summary-card">
        <div class="summary-value">{total_notes}</div>
        <div class="summary-label">evidence notes</div>
      </div>
      <div class="card summary-card">
        <div class="summary-value">{len(groups)}</div>
        <div class="summary-label">chunks with evidence</div>
      </div>
      <div class="card summary-card">
        <div class="summary-value">{implicates}</div>
        <div class="summary-label">implicates</div>
      </div>
      <div class="card summary-card">
        <div class="summary-value">{clears}</div>
        <div class="summary-label">clears</div>
      </div>
    </div>
    <div class="ladder">
      {ladder_body}
    </div>
"""
    extra_styles = """
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }
    .summary-card {
      text-align: center;
      padding: 18px 14px;
    }
    .summary-value {
      font-size: 30px;
      font-weight: 700;
      color: #183642;
    }
    .summary-label {
      font-size: 13px;
      color: var(--muted);
      margin-top: 4px;
    }
    .ladder {
      display: grid;
      gap: 14px;
    }
    .chunk-group {
      position: relative;
      padding-left: 26px;
    }
    .chunk-group::before {
      content: "";
      position: absolute;
      left: 8px;
      top: 4px;
      bottom: -14px;
      width: 2px;
      background: linear-gradient(to bottom, #cfd8df 0%, #e6edf2 100%);
    }
    .chunk-label {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .evidence-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 10px;
    }
    .evidence-item {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px 16px;
      box-shadow: 0 8px 20px rgba(15, 25, 35, 0.06);
    }
    .evidence-item strong {
      display: inline-block;
      margin-left: 8px;
      color: #183642;
    }
    .evidence-item p {
      margin: 10px 0 0;
      color: #29404b;
      line-height: 1.5;
      font-size: 14px;
    }
    .chip {
      display: inline-block;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .chip-implicates {
      background: #fff0df;
      color: #9c4d0a;
    }
    .chip-clears {
      background: #e9f7f4;
      color: #0f6b5b;
    }
    .empty-state p {
      margin: 8px 0 0;
      color: var(--muted);
    }
"""
    return _page_chrome(f"{episode_id} Evidence Ladder", body, extra_styles)


_RACE_COLORS = [
    "#2f80ed", "#e74c3c", "#27ae60", "#f39c12", "#8e44ad",
    "#16a085", "#d35400", "#2c3e50", "#c0392b", "#1abc9c",
    "#e67e22", "#3498db", "#9b59b6", "#2ecc71", "#e84393",
]


def _has_suspicion_scores(events: list[dict[str, Any]]) -> bool:
    return any(ev.get("suspicion_scores") for ev in events if isinstance(ev, dict))


def _render_race_chart_episode(payload: dict[str, Any], heatmap_href: str) -> str:
    episode_id = str(payload.get("episode_id", "unknown-episode"))
    events = [e for e in (payload.get("events") or []) if isinstance(e, dict)]

    if not _has_suspicion_scores(events):
        body = f"""
    <h1>{html.escape(episode_id)}</h1>
    <div class="nav">
      <a href="{html.escape(heatmap_href)}">Heatmap</a>
      <a href="index.html">Index</a>
    </div>
    <div class="card">
      <p style="color: var(--muted); padding: 20px;">No suspicion scores available for this episode. Re-run inference with suspicion score support to generate this chart.</p>
    </div>
"""
        return _page_chrome(f"{episode_id} Suspicion Race", body)

    suspects = _ordered_suspects(events)
    chunks = len(events)

    # Build score series per suspect
    score_series: dict[str, list[int | None]] = {s: [] for s in suspects}
    for ev in events:
        scores = ev.get("suspicion_scores", {}) or {}
        active_after = set(ev.get("active_suspects_after_chunk", []))
        for s in suspects:
            if s in scores:
                score_series[s].append(int(scores[s]))
            elif s in active_after:
                score_series[s].append(0)
            else:
                score_series[s].append(None)

    # SVG dimensions
    chart_w = max(600, chunks * 50)
    chart_h = 320
    left_pad = 50
    right_pad = 180
    top_pad = 50
    bottom_pad = 40
    svg_w = left_pad + chart_w + right_pad
    svg_h = top_pad + chart_h + bottom_pad

    svg_parts: list[str] = [
        f'<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" role="img" '
        f'aria-label="Suspicion race chart for {html.escape(episode_id)}">'
    ]

    # Title
    svg_parts.append(
        f'<text x="{left_pad}" y="28" font-size="14" font-weight="700" fill="#183642">'
        "Suspicion Race</text>"
    )

    # Grid lines and Y-axis labels
    for pct in (0, 25, 50, 75, 100):
        y = top_pad + chart_h - (pct / 100 * chart_h)
        svg_parts.append(
            f'<line x1="{left_pad}" y1="{y}" x2="{left_pad + chart_w}" y2="{y}" '
            'stroke="#e2e8f0" stroke-width="1" />'
        )
        svg_parts.append(
            f'<text x="{left_pad - 8}" y="{y + 4}" text-anchor="end" '
            f'font-size="10" fill="#94a3b8">{pct}</text>'
        )

    # X-axis labels
    for i in range(chunks):
        x = left_pad + (i / max(1, chunks - 1)) * chart_w if chunks > 1 else left_pad
        if chunks <= 20 or i % 2 == 0:
            svg_parts.append(
                f'<text x="{x}" y="{top_pad + chart_h + 18}" text-anchor="middle" '
                f'font-size="10" fill="#94a3b8">c{i}</text>'
            )

    # Plot lines
    color_map: dict[str, str] = {}
    for idx, suspect in enumerate(suspects):
        color_map[suspect] = _RACE_COLORS[idx % len(_RACE_COLORS)]

    for suspect in suspects:
        series = score_series[suspect]
        color = color_map[suspect]
        points: list[str] = []
        for i, val in enumerate(series):
            if val is None:
                continue
            x = left_pad + (i / max(1, chunks - 1)) * chart_w if chunks > 1 else left_pad
            y = top_pad + chart_h - (val / 100 * chart_h)
            points.append(f"{x:.1f},{y:.1f}")

        if len(points) >= 2:
            svg_parts.append(
                f'<polyline points="{" ".join(points)}" fill="none" '
                f'stroke="{color}" stroke-width="2.5" stroke-linejoin="round" '
                f'stroke-linecap="round" />'
            )

        # Dots at each data point
        for i, val in enumerate(series):
            if val is None:
                continue
            x = left_pad + (i / max(1, chunks - 1)) * chart_w if chunks > 1 else left_pad
            y = top_pad + chart_h - (val / 100 * chart_h)
            svg_parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" '
                f'fill="{color}" stroke="#fff" stroke-width="1.5" />'
            )

    # Legend (right side)
    for idx, suspect in enumerate(suspects):
        color = color_map[suspect]
        ly = top_pad + 10 + idx * 20
        svg_parts.append(
            f'<line x1="{left_pad + chart_w + 14}" y1="{ly}" '
            f'x2="{left_pad + chart_w + 30}" y2="{ly}" '
            f'stroke="{color}" stroke-width="2.5" stroke-linecap="round" />'
        )
        svg_parts.append(
            f'<text x="{left_pad + chart_w + 36}" y="{ly + 4}" '
            f'font-size="11" fill="#183642">{html.escape(suspect)}</text>'
        )

    svg_parts.append("</svg>")
    chart_svg = "\n".join(svg_parts)

    body = f"""
    <h1>{html.escape(episode_id)}</h1>
    <p class="meta">Suspicion scores across {chunks} chunks &middot; {len(suspects)} suspects</p>
    <div class="nav">
      <a href="{html.escape(heatmap_href)}">Heatmap</a>
      <a href="index.html">Index</a>
    </div>
    <div class="card" style="overflow-x: auto;">
      {chart_svg}
    </div>
"""
    return _page_chrome(f"{episode_id} Suspicion Race", body)


def _render_index(entries: list[dict[str, str]]) -> str:
    rows = []
    for entry in entries:
        race_cell = ""
        if entry.get("race_href"):
            race_cell = f'<td><a href="{html.escape(entry["race_href"])}">Suspicion Race</a></td>'
        else:
            race_cell = "<td></td>"
        rows.append(
            "<tr>"
            f"<td>{html.escape(entry['episode_id'])}</td>"
            f'<td><a href="{html.escape(entry["heatmap_href"])}">Heatmap</a></td>'
            f'<td><a href="{html.escape(entry["evidence_href"])}">Evidence Ladder</a></td>'
            f"{race_cell}"
            "</tr>"
        )
    body = f"""
    <h1>Timeline Visualizations</h1>
    <p class="meta">Rendered episodes: {len(entries)}</p>
    <div class="card">
      <table>
        <thead>
          <tr>
            <th>episode</th>
            <th>heatmap</th>
            <th>evidence ladder</th>
            <th>suspicion race</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
    </div>
"""
    return _page_chrome("Timeline Visualizations", body)


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir or (run_stage_path(args.run_root, "timelines") if args.run_root else None)
    output_dir = args.output_dir or (run_stage_path(args.run_root, "html") if args.run_root else None)
    if input_dir is None or output_dir is None:
        raise ValueError("Provide --run-root or both --input-dir and --output-dir.")
    if not input_dir.exists():
        if args.run_root and args.input_dir is None:
            raise FileNotFoundError(
                f"Input directory not found: {input_dir}\n"
                "Expected numbered input folder 03-timelines under the run root."
            )
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("*.timeline.json"))
    if args.limit is not None:
        files = files[: args.limit]
    if not files:
        raise FileNotFoundError(f"No timeline files found in: {input_dir}")

    rendered = 0
    index_entries: list[dict[str, str]] = []
    for path in files:
        payload = _read_json(path)
        episode_id = str(payload.get("episode_id", path.stem))
        stem = path.stem.replace(".timeline", "")
        heatmap_name = f"{stem}.timeline.html"
        evidence_name = f"{stem}.evidence.html"
        race_name = f"{stem}.race.html"
        (output_dir / heatmap_name).write_text(
            _render_heatmap_episode(payload, evidence_name),
            encoding="utf-8",
        )
        (output_dir / evidence_name).write_text(
            _render_evidence_ladder_episode(payload, heatmap_name),
            encoding="utf-8",
        )
        (output_dir / race_name).write_text(
            _render_race_chart_episode(payload, heatmap_name),
            encoding="utf-8",
        )
        rendered += 3
        entry: dict[str, str] = {
            "episode_id": episode_id,
            "heatmap_href": heatmap_name,
            "evidence_href": evidence_name,
        }
        events = payload.get("events") or []
        if _has_suspicion_scores(events):
            entry["race_href"] = race_name
        index_entries.append(entry)

    (output_dir / "index.html").write_text(_render_index(index_entries), encoding="utf-8")
    rendered += 1

    print(f"Rendered HTML files: {rendered}")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
