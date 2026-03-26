# PROJECT CENTRALESUPELEC-BRGM 2025-2026

## Hydrological Visualization Tool

This project provides a command-line Python tool to analyze, process, and visualize hydrological datasets. It supports NetCDF and CSV inputs, computes indicators and statistics, and generates plots.

The workflow is interactive: users select indicators, statistical operations, and visualization types step by step.

---

## Features

* Supports **NetCDF (.nc)** and **CSV** files
* Interactive data analysis pipeline
* Hydrological indicators computation
* Statistical processing (mean, percentile, etc.)
* Multiple visualization types
* Built on **xarray**, ideal for multidimensional data

---

## Project Structure

```
PROJET_RE_EAU_2025/
├── input/                   # Input files
├── output/                  # Generated figures
├── old/                     # Deprecated code
│
├── data_formatting.py       # Data loading and formatting
├── indicators_xr.py         # Compute hydrological indicators
├── statistics_xr.py         # Compute statistical functions
├── visualization_xr.py      # Plotting functions
├── main_full_xarray.py      # Main CLI script
│
├── README.md
└── .gitignore
```

---

## Supported Input Data

### NetCDF

* Supports one or multiple `.nc` files
* Ideal for climate, hydrology, or environmental datasets
* Multidimensional data supported (time, space, model, etc.)
* Loaded as `xarray.Dataset`

Example dimensions:

* `time`
* `lat`, `lon`
* `model`
* `station`
* any other accurate dimensions

---

### CSV

* Single file only
* Must be convertible to structured tabular data
* Automatically converted to xarray format

Typical structure:

| time | variable1 | variable2 |
| ---- | --------- | --------- |

---

## Outputs

### Figures

* Saved automatically in the `output/` directory
* Format: **PNG**
* Filename based on visualization type

Example:

```
output/line_chart.png
```

Figures are also displayed interactively.

---

## Available Visualizations

* Bar chart
* Scatter plot
* Line chart
* Radar chart
* Histogram

---

## Available Statistical Operations

* Flexible mean
* Flexible maximum
* Flexible minimum
* Flexible percentile
* Temporal rolling mean
* Monthly interannual average

---

## Available Hydrological Indicators

* IPS
* Qmean
* Q90 / Q95
* Q10 / Q05
* VCN10
* VCX3
* Over-threshold indicator

These indicators are computed directly on the dataset and can be chained with statistical operations.

---

## Required Libraries

The project relies on scientific Python libraries commonly used for environmental data analysis.

### Core dependencies

* pandas
* xarray
* matplotlib
* netCDF4
* pathlib (standard library)
* os (standard library)

---

### Installation with pip and requirements.txt

Install all required packages:

```bash
pip install -r requirements.txt
```

---

## How to Run

### 1. Run the main script

```bash
python main_full_xarray.py
```

---

### 2. Follow the interactive prompts

You will be asked to:

1. Select file format (NetCDF or CSV)
2. Provide file path(s)
3. Choose indicators to compute
4. Choose statistical operations
5. Select a visualization
6. Decide whether to continue analysis

---

## Workflow Overview

```
Load data → Compute indicators → Apply statistics → Visualize → Save output
```

The process can be repeated multiple times on the same dataset.

---

## Technical Stack

* Python 3.x
* pandas
* xarray
* matplotlib
* pathlib

---

## Notes

* Multiple files are supported **only for NetCDF**
* Input data must be properly formatted

---

## Authors

Project developed as part of the RE_EAU_2025 project.
