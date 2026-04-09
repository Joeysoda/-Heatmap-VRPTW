# New_GCN_XYZ (Clean Layout)

## Core entrypoints
- `run_comparison.py` : full 8-algorithm benchmark (hard constraints).
- `run_standalone.py` : single-run standalone scheduling.
- `anylogic_file_bridge.py` : AnyLogic file bridge mode.

## Core code
- `core/` : active implementation (solver, data loader, GCN, metaheuristics, scheduler, config).
- `tests/` : regression tests for constraints and ranking behavior.

## Data / outputs
- `models/` : trained model artifacts.
- `results/` : experiment outputs.
- `anylogic_bridge/` : AnyLogic input/output/status exchange folder.
- `baseline_snapshot/` : frozen baseline parameters/results.

## Documentation and scripts
- `docs/` : user guides and project docs.
- `scripts/` : `.bat` launch scripts.
- `docs/RUN_PYTORCH_GPU_NO_C.md` : run with `pytorch_gpu` while keeping cache/temp on `D:`.
- `scripts/run_comparison_gpu_no_c.ps1` : one-shot PowerShell runner for the above setup.

## Archived legacy content
- `archive/legacy_code/` : old root-level duplicated code.
- `archive/legacy_docs/` : historical troubleshooting/notes.
- `archive/legacy_outputs/` : old loose output files.
- `archive/legacy_tools/` : old setup/helper scripts.

