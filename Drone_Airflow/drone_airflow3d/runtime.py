"""Conservative CPU budget; FFT parallelism only in the present 3-D solver."""
import os
from pathlib import Path


def cpu_budget():
    affinity = (len(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity')
                else os.cpu_count() or 1)
    limits = [affinity]
    # Inspect the current unified cgroup and its ancestors where exposed.
    roots = [Path('/sys/fs/cgroup')]
    try:
        for line in Path('/proc/self/cgroup').read_text().splitlines():
            if line.startswith('0::'):
                current = Path('/sys/fs/cgroup') / line.split('::', 1)[1].lstrip('/')
                roots.extend([current, *[p for p in current.parents
                                        if p.is_relative_to('/sys/fs/cgroup')]])
    except OSError:
        pass
    for root in set(roots):
        try:
            quota, period = (root / 'cpu.max').read_text().split()
            if quota != 'max':
                limits.append(max(1, int(quota) // int(period)))
        except (OSError, ValueError):
            pass
    # Never infer a whole-node reservation from a multi-task allocation.
    if 'SLURM_JOB_ID' in os.environ:
        limits.append(int(os.environ.get('SLURM_CPUS_PER_TASK', '1')))
    if '_CONDOR_JOB_AD' in os.environ:
        import re
        try:
            ad = Path(os.environ['_CONDOR_JOB_AD']).read_text()
            match = re.search(r'^\s*RequestCpus\s*=\s*(\d+)\s*$', ad, re.M | re.I)
            limits.append(int(match[1]) if match else 1)
        except OSError:
            limits.append(1)
    if 'CFD_CPU_LIMIT' in os.environ:
        limits.append(int(os.environ['CFD_CPU_LIMIT']))
    return max(1, min(limits))


def configure_threads(value='auto'):
    for key in ('OMPI_COMM_WORLD_SIZE', 'PMI_SIZE', 'PMIX_SIZE', 'MV2_COMM_WORLD_SIZE', 'SLURM_NTASKS'):
        if int(os.environ.get(key, '1')) > 1:
            raise ValueError('This solver uses one process. Request one task with multiple CPUs, not multiple MPI ranks.')
    available = cpu_budget()
    threads = min(4, available) if value == 'auto' else int(value)
    if not 1 <= threads <= available:
        raise ValueError(f'threads must be 1..{available} within the available CPU budget')
    for key in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
        os.environ[key] = '1'
    return threads, available
