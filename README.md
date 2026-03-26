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

- Single file only  
- Must be a structured table (rows = observations, columns = variables)  
- Columns must be separated by semicolons (`;`)
- Long format is required for multimodel data
- Metadata lines before the header are allowed (user specifies how many to skip)

---

#### Date Column (REQUIRED)

The file must contain at least one column representing time.

**Accepted column names (priority detection):**

- Date, date, DATE  
- Time, time, TIME  
- Dates, dates, DATES  
- Times, times, TIMES  

If none of these names are present, the program will attempt automatic detection:

- Any column convertible to datetime  
- At least ~80% of values must be valid dates  
- European date formats are supported (day-first)

Example accepted formats:

- `31/12/2020`
- `2020-12-31`
- `31-12-2020`
- ISO datetime strings

If no valid date column is detected, the import will fail.

---

#### Optional Dimension Columns

Additional columns can define coordinates (dimensions) in the dataset.

Recognized dimension names include:

- model, scenario  
- station, stations  
- site, sites  
- piezometre  
- location, locations  
- latitude, longitude  
- lat, lon  
- x, y  

These columns will be treated as categorical coordinates in xarray.

---

#### Long Format for Multimodel Data

For datasets containing multiple models, stations, or scenarios, a **long format** is required:

| Date | model | station | variable |
|------|-------|---------|----------|
| ...  | M1    | S1      | ...      |

The combination of time + dimension columns must uniquely identify each observation.

If duplicates exist, the conversion will fail.

---

#### Variable Columns

All remaining columns are interpreted as data variables.

- Must contain numeric values (preferred)
- Missing values are allowed
- Non-numeric columns (except dimensions) may be ignored or cause issues

---

#### Not Supported

- Files without a valid date/time column  
- Wide-format Excel-style tables with multi-level headers  
- Duplicate rows for the same time + dimension combination  
- Multiple CSV files at once  
- Non-tabular formats  

---

#### Example Minimal Valid CSV


Typical structure:

| time | variable1 | variable2 |
| ---- | --------- | --------- |

---

#### Example Multidimensional CSV

```csv
Date;model;station;flow
01/01/2000;M1;S1;12.5
01/01/2000;M2;S1;13.2
02/01/2000;M1;S1;12.9


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

## Notes

* Multiple files are supported **only for NetCDF**
* Input data must be properly formatted

---

## Authors

Project developed as part of the RE_EAU_2025 project.
