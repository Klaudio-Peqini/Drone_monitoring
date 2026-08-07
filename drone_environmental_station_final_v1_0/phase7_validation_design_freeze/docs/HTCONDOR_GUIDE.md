# HTCondor analysis guide

Phase 7 jobs are generally analysis/aggregation jobs rather than the largest CFD campaigns. Keep CFD on the validated phase-specific workflows and use this directory for reproducible analysis batches. Submit with explicit `request_cpus`, `request_memory` and `request_disk`; keep output/error/log paths unique. Start with the supplied smoke-test submit file, then create job tables for independent run groups, bootstrap replicas or Monte Carlo uncertainty samples. Do not allow two jobs to write the same output path.
