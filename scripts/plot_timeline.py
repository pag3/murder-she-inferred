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
                clean = str(name).strip()
                if clean:
                    seen.add(clean)
    return sorted(seen)


def _state_matrix(events: list[dict[str, Any]], suspects: list[str]) -> list[list[str]]:
    """Return rows per suspect and columns per chunk with state labels."""
    rows: list[list[str]] = []
    for suspect in suspects:
        row: list[str] = []
        for ev in events:
            active = set(str(x).strip() for x in (ev.get("active_suspects_after_chunk") or []))
            eliminated = set(
                str(x).strip() for x in (ev.get("eliminated_suspects_after_chunk") or [])
            )
            if suspect in active:
                row.append("active")
            elif suspect in eliminated:
                row.append("eliminated")
            else:
                row.append("none")
        rows.append(row)
    return rows


def _render_episode(payload: dict[str, Any]) -> str:
    episode_id = str(payload.get("episode_id", "unknown-episode"))
    events = [e for e in (payload.get("events") or []) if isinstance(e, dict)]
    suspects = _all_suspects(events)
    matrix = _state_matrix(events, suspects)
    chunks = len(events)

    cell_w = 22
    cell_h = 22
    left_pad = 260
    top_pad = 70
    width = left_pad + (chunks * cell_w) + 40
    height = top_pad + (max(1, len(suspects)) * cell_h) + 70

    svg_parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Suspect timeline for {html.escape(episode_id)}">'
    ]

    # Chunk labels
    for i in range(chunks):
        x = left_pad + i * cell_w + (cell_w / 2)
        if i % 5 == 0:
            svg_parts.append(
                f'<text x="{x}" y="{top_pad - 14}" text-anchor="middle" '
                'font-size="10" fill="#335">c'
                f"{i}</text>"
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
            state = matrix[r][c] if r < len(matrix) else "none"
            x = left_pad + c * cell_w
            if state == "active":
                fill = "#2f80ed"
            elif state == "eliminated":
                fill = "#9aa5b1"
            else:
                fill = "#f0f3f6"
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_w - 2}" height="{cell_h - 2}" '
                f'fill="{fill}" stroke="#d6dbe1" />'
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

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(episode_id)} Timeline</title>
  <style>
    :root {{
      --bg: #f7f5ef;
      --ink: #122025;
      --muted: #61717f;
      --card: #ffffff;
      --line: #d7dde4;
      --active: #2f80ed;
      --eliminated: #9aa5b1;
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
    .legend {{
      display: flex;
      gap: 14px;
      margin: 8px 0 14px;
      font-size: 13px;
      color: var(--muted);
    }}
    .swatch {{
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 1px solid var(--line);
      margin-right: 6px;
      vertical-align: -2px;
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
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{html.escape(episode_id)}</h1>
    <p class="meta">Chunks: {chunks} | Suspects observed: {len(suspects)}</p>
    <div class="card">
      <div class="legend">
        <span><span class="swatch" style="background:var(--active)"></span>active</span>
        <span><span class="swatch" style="background:var(--eliminated)"></span>eliminated</span>
        <span><span class="swatch" style="background:#f0f3f6"></span>no state</span>
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
  </div>
</body>
</html>
"""


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
    index_rows: list[str] = []
    for path in files:
        payload = _read_json(path)
        episode_id = str(payload.get("episode_id", path.stem))
        out_name = f"{path.stem.replace('.timeline', '')}.timeline.html"
        out_path = output_dir / out_name
        out_path.write_text(_render_episode(payload), encoding="utf-8")
        rendered += 1
        index_rows.append(
            f'<li><a href="{html.escape(out_name)}">{html.escape(episode_id)}</a></li>'
        )

    index_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Timeline Visualizations</title>
  <style>
    body {{
      font-family: "Avenir Next", "Helvetica Neue", Helvetica, sans-serif;
      background: #f4f7f9;
      color: #122025;
      margin: 0;
    }}
    .wrap {{
      max-width: 900px;
      margin: 30px auto;
      padding: 0 16px 30px;
    }}
    ul {{
      background: #fff;
      border: 1px solid #d6dbe1;
      border-radius: 10px;
      padding: 16px 24px;
      line-height: 1.7;
    }}
    a {{
      color: #0c5cc0;
      text-decoration: none;
    }}
    a:hover {{
      text-decoration: underline;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Timeline Visualizations</h1>
    <p>Rendered episodes: {rendered}</p>
    <ul>
      {"".join(index_rows)}
    </ul>
  </div>
</body>
</html>
"""
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    print(f"Rendered HTML files: {rendered}")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
