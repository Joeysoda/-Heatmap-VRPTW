# Run In `pytorch_gpu` Without C-Drive Growth

This guide keeps runtime caches and temp files on `D:` and runs the project with:

- Python: `D:\anaconda3\envs\pytorch_gpu\python.exe`
- Project: `D:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ`

## 1) PowerShell (correct path switch)

Do not use `cd /d ...` in PowerShell (that syntax is for `cmd.exe`).

Use:

```powershell
Set-Location "D:\1nottingham\Year4a\FYP\hospital_main_copy\-Heatmap-VRPTW\New_GCN_XYZ"
```

## 2) Set D-drive caches for this session

```powershell
$cacheRoot = "D:\runtime_cache\pytorch_gpu"
New-Item -ItemType Directory -Force -Path "$cacheRoot\pip","$cacheRoot\tmp","$cacheRoot\mpl" | Out-Null

$env:PIP_CACHE_DIR = "$cacheRoot\pip"
$env:TEMP = "$cacheRoot\tmp"
$env:TMP = "$cacheRoot\tmp"
$env:MPLCONFIGDIR = "$cacheRoot\mpl"
```

## 3) Run comparison

```powershell
& "D:\anaconda3\envs\pytorch_gpu\python.exe" .\run_comparison.py
```

Outputs are written to:

```text
New_GCN_XYZ\results\comparison_YYYYMMDD_HHMMSS\
```

Including:

- `summary.csv`
- `raw_results.json`
- `comparison_report.txt`
- chart files (`.png` if matplotlib exists, otherwise `.svg`)

## 4) Optional dependencies (still D-drive cache)

Current code can run without `openpyxl` and `matplotlib`:

- built-in XLSX parser is used when `openpyxl` is missing
- SVG charts are generated when `matplotlib` is missing

If you still want to install optional packages:

```powershell
& "D:\anaconda3\envs\pytorch_gpu\python.exe" -m pip install --cache-dir "$env:PIP_CACHE_DIR" openpyxl matplotlib pytest
```

## 5) One-line helper script

You can also run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_comparison_gpu_no_c.ps1
```
