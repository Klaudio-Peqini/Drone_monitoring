import argparse
import sys
from pathlib import Path


def main(argv):
    parser=argparse.ArgumentParser(description='Matrice 350: three-dimensional station placement within 1 m.')
    sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('study',help='Run sensitivity, operating envelope and installed-station checks')
    run.add_argument('--case',type=Path,required=True);run.add_argument('--out',type=Path,required=True)
    run.add_argument('--jobs',type=int,default=1,help='Independent cases in parallel; jobs * threads must fit the CPU budget')
    run.add_argument('--threads',default='1',help='FFT workers per case; momentum/scalars use NumPy')
    run.add_argument('--no-render',action='store_true')
    run.add_argument('--installed-position',nargs=3,type=float,action='append',default=[],metavar=('X','Y','Z'),help='Also test this station centre in body metres; may be repeated')
    draw=sub.add_parser('render-study',help='Create the seven full-volume GIFs from saved study fields')
    draw.add_argument('--input',required=True,type=Path);draw.add_argument('--fps',type=int,default=8)
    draw.add_argument('--dpi',type=int,default=80);draw.add_argument('--orbit',action='store_true')
    draw.add_argument('--styles',nargs='+',default=['all'],choices=['all','velocity','streamlines','particles','pressure','vorticity','concentration','placement'])
    verify=sub.add_parser('verify-study',help='Recheck numerical outputs and qualification gates')
    verify.add_argument('--input',required=True,type=Path)
    calibrate=sub.add_parser('calibrate',help='Fit measured RPM/thrust/torque CSV; no synthetic defaults')
    calibrate.add_argument('--csv',required=True,type=Path);calibrate.add_argument('--out',required=True,type=Path)
    measurements=sub.add_parser('validate-measurements',help='Compare held-out velocity measurements with exported probes')
    measurements.add_argument('--input',required=True,type=Path);measurements.add_argument('--csv',required=True,type=Path)
    measurements.add_argument('--out',required=True,type=Path);measurements.add_argument('--max-error',type=float,default=.15)
    args=parser.parse_args(argv)
    try:
        from .runtime import configure_threads
        threads,budget=configure_threads(getattr(args,'threads','1'))
        if args.command=='study':
            if not 1<=args.jobs<=budget or args.jobs*threads>budget:raise ValueError('jobs * threads exceeds the detected CPU budget')
            from .placement_config import load_study
            from .study import execute_study
            result=execute_study(load_study(args.case),args.out,args.jobs,threads,not args.no_render,args.installed_position)
            print(result['status']);return 0
        if args.command=='render-study':
            from .study_render import render_all
            render_all(args.input,styles=args.styles,fps=args.fps,dpi=args.dpi,orbit=args.orbit);return 0
        if args.command=='verify-study':
            from .study_verify import verify_outputs
            result=verify_outputs(args.input);return 0 if result['numerical_gates_passed'] else 1
        if args.command=='calibrate':
            from .actuator import fit_calibration
            fit_calibration(args.csv,args.out);print(f'Saved calibration {args.out}');return 0
        if args.command=='validate-measurements':
            from .study_verify import compare_measurements
            result=compare_measurements(args.input,args.csv,args.out,args.max_error)
            print(result);return 0 if result['passed'] else 1
    except (ValueError,OSError,FloatingPointError,RuntimeError,KeyError) as exc:
        print(f'Error: {exc}',file=sys.stderr);return 2
