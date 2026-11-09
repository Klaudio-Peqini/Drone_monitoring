"""Headless command line; solve once and render again without rerunning CFD."""
import argparse
import json
import sys
from pathlib import Path


def parser():
    p = argparse.ArgumentParser(description='Compute and visualise full-volume 3-D rotor airflow in SI units.')
    commands = p.add_subparsers(dest='command', required=True)
    for name,help_text in [('study','Matrice station-placement study'),('render-study','Seven full-volume study animations'),
                           ('verify-study','Audit completed study outputs'),('calibrate','Fit measured rotor-load data'),
                           ('validate-measurements','Compare independent airflow measurements')]:
        commands.add_parser(name,help=help_text)
    run = commands.add_parser('run', help='Solve a JSON case and optionally create 3-D GIFs')
    run.add_argument('--case', required=True, type=Path)
    run.add_argument('--out', required=True, type=Path)
    run.add_argument('--threads', default='auto', help='Pressure FFT workers: auto or an integer within your CPU budget')
    run.add_argument('--duration', type=float, help='Override simulated physical duration in seconds')
    run.add_argument('--frames', type=int, help='Override saved physical-time frames (2..120)')
    run.add_argument('--overwrite', action='store_true', help='Replace known generated files in a package-owned result folder')
    draw = commands.add_parser('render', help='Render existing 3-D snapshots without solving again')
    draw.add_argument('--input', required=True, type=Path)
    draw.add_argument('--overwrite', action='store_true', help='Replace existing animations of the selected style')
    for command in (run, draw):
        command.add_argument('--style', choices=('streamlines', 'particles', 'both'), default='both')
        command.add_argument('--fps', type=int, default=12, help='Playback frames/second; does not change physical time')
        command.add_argument('--dpi', type=int, default=90)
        command.add_argument('--orbit', action='store_true', help='Slow camera orbit; otherwise the camera stays fixed')
    run.add_argument('--no-render', action='store_true', help='Only compute and save snapshots')
    return p


def main(argv=None):
    actual=sys.argv[1:] if argv is None else argv
    if actual and actual[0] in ('study','render-study','verify-study','calibrate','validate-measurements'):
        from .study_cli import main as study_main
        return study_main(actual)
    args = parser().parse_args(argv)
    try:
        if not 1 <= args.fps <= 60 or not 50 <= args.dpi <= 160:
            raise ValueError('Require fps 1..60 and dpi 50..160')
        if args.command == 'run':
            # Configure the environment before importing numerical libraries.
            from .runtime import configure_threads
            threads, available = configure_threads(args.threads)
            from .config import load_case, validate
            from .simulation import simulate
            c = load_case(args.case)
            if args.duration is not None:
                c['duration_s'] = args.duration
            if args.frames is not None:
                c['frames'] = args.frames
            c = validate(c)
            print(f'CPU budget: {available}; pressure FFT workers: {threads}. Momentum and force deposition use NumPy.', flush=True)
            result = simulate(c, args.out, threads=threads, overwrite=args.overwrite)
            print(json.dumps(result, indent=2), flush=True)
            folder = args.out
            if args.no_render:
                return 0
        else:
            folder = args.input
        from .visualization import render
        for style in (('streamlines', 'particles') if args.style == 'both' else (args.style,)):
            print(f'Rendering 3-D {style}...', flush=True)
            render(folder, style=style, fps=args.fps, dpi=args.dpi, orbit=args.orbit,
                   overwrite=args.overwrite)
        return 0
    except (ValueError, OSError, FloatingPointError, RuntimeError, KeyError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
