# PROJECT CENTRALESUPELEC-BRGM 2025-2026
## Table of Contents

- [Hydrological Visualization Tool](#hydrological-visualization-tool)
- [Features](#features)
- [Project Structure](#project-structure)
- [Supported Input Data](#supported-input-data)
  - [NetCDF](#netcdf-input-data-specification)
    - [Multiple Files Support](#multiple-files-support)
    - [Time Handling](#time-handling)
    - [Spatial Dimension Handling (Interactive)](#spatial-dimension-handling-interactive)
      - [Recognized Point Dimensions](#recognized-point-dimensions)
      - [Recognized Grid Dimensions](#recognized-grid-dimensions)
    - [Required Metadata for Model Identification](#required-metadata-for-model-identification)
    - [Automatic Creation of Dimensions](#automatic-creation-of-dimensions)
      - [Scenario Dimension](#scenario-dimension)
      - [Model Dimension](#model-dimension)
    - [Dataset Combination](#dataset-combination)
    - [Not Supported](#not-supported)
  - [CSV](#csv-input-data-specification)
    - [Date Column (REQUIRED)](#date-column-required)
    - [Optional Dimension Columns](#optional-dimension-columns)
    - [Long Format for Multimodel Data](#long-format-for-multimodel-data)
    - [Variable Columns](#variable-columns)
    - [Not Supported](#not-supported-1)
    - [Example Minimal Valid CSV](#example-minimal-valid-csv)
    - [Example Multidimensional CSV](#example-multidimensional-csv)
- [Outputs](#outputs)
  - [Figures](#figures)
- [Available Visualizations](#available-visualizations)
- [Available Statistical Operations](#available-statistical-operations)
- [Available Hydrological Indicators](#available-hydrological-indicators)
- [Required Libraries](#required-libraries)
  - [Core dependencies](#core-dependencies)
  - [Installation with pip and requirements.txt](#installation-with-pip-and-requirementstxt)
- [How to Run](#how-to-run)
- [Workflow Overview](#workflow-overview)
- [Notes](#notes)
- [Authors](#authors)

## Hydrological Visualization Tool

This project provides a command-line Python tool to analyze, process, and visualize hydrological datasets. It supports NetCDF and CSV inputs, computes indicators and statistics, and generates plots.

The workflow is interactive: users select indicators, statistical operations, and visualization types step by step.

---
## For the Impatient Reader

If you just want to quickly test the tool without reading all the details, here is what you need:

**Main Requirements:**  
- Python 3.8+ 
- pandas  
- xarray  
- matplotlib  
- netCDF4  

**Supported Input Data:**  
- **NetCDF (.nc)** files – recommended for large datasets  
- **CSV files (long format only)** – must be structured as a table, separated by semicolons (`;`)  

**CSV Requirements:**  
- Must have at least one **date/time column**. Accepted names (must match exactly, case-sensitive):  
  - `Date`, `date`, `DATE`  
  - `Time`, `time`, `TIME`  
  - `Dates`, `dates`, `DATES`  
  - `Times`, `times`, `TIMES`  
- Optional additional dimension columns (must be spelled exactly as below, case-sensitive):  
  - `model`, `scenario`  
  - `station`, `stations`  
  - `site`, `sites`  
  - `piezometre`  
  - `location`, `locations`  
  - `latitude`, `longitude`  
  - `lat`, `lon`  
  - `x`, `y`  
- Remaining columns are interpreted as numeric variables  
- Long format only: each row represents one observation uniquely identified by time + dimensions  
- Wide-format tables or multi-level headers are **not supported**  

**Quick Start Commands:**  
```bash
pip install -r requirements.txt
python main_full_xarray.py
```

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

## NetCDF Input Data Specification

The tool supports one or multiple NetCDF files (`.nc`) and converts them into a single multidimensional `xarray.Dataset`.

NetCDF is the recommended format for large hydrological or climate datasets.

---

### Multiple Files Support

Multiple NetCDF files can be provided simultaneously.

Each file is:

1. Opened individually
2. Processed
3. Augmented with model metadata
4. Combined into a single dataset

Combination is performed using `xarray.combine_by_coords`.

---

### Time Handling

Time coordinates are decoded manually.

If a `time` variable is present, it will be converted to datetime using its CF metadata:

- `units`
- `calendar`

If no valid time coordinate exists, results may be incorrect or unusable.

---

### Spatial Dimension Handling (Interactive)

The program automatically detects spatial dimensions and asks how to handle them.

Two options are available:

1. **Keep all spatial data**
2. **Select a single entity (point/station/grid cell)**

---

#### Recognized Point Dimensions

The following dimension names are treated as discrete entities:

- piezometre  
- station, stations  
- site, sites  
- location, locations  

---

#### Recognized Grid Dimensions

If no point dimension is found, grid coordinates are searched:

- latitude, longitude  
- lat, lon  
- x, y  

---
If a spatial dimension is detected:

- The program displays available entities
- The user may select one entity by index
- The dataset is subset accordingly

If no spatial dimension is detected, the dataset is used as-is.

---

### Required Metadata for Model Identification

Each NetCDF file must contain specific global attributes describing the model chain.

Recognized attributes:

- `experiment_id` → scenario  
- `driving_model_id` → GCM  
- `model_id` → RCM  
- `bc_method_id` → bias correction method  
- `hy_model_id` → hydrological model  

These attributes are used to construct new dimensions.

If any of these attributes are missing, the file will be rejected.

---

### Automatic Creation of Dimensions

Two new dimensions are automatically added to each dataset based on NetCDF metadata.

---

#### Scenario Dimension

The **scenario** dimension is derived from the global attribute:

```text
experiment_id
```
scenario = "RCP85"

#### Model Dimension

A single combined model chain identifier is created from several metadata attributes:

driving_model_id (GCM)
model_id (RCM)
bc_method_id (bias correction method)
hy_model_id (hydrological model)

These components are concatenated into one dimension:

model = "GCM-RCM-BC-HY"

Example:
IPSL-CM5A-MR-RCA4-QM-GR4J

---

### Dataset Combination

After preprocessing, all datasets are merged into one multidimensional dataset.

Combination features:

- Coordinate-based merging
- Outer join (keeps all available data)
- Attribute conflicts are dropped

---

### Not Supported

The following cases may cause errors or incorrect results:

- Missing required metadata attributes  
- Inconsistent coordinate definitions between files  
- Non-CF-compliant time variables  
- Files without meaningful dimensions  
- Extremely large datasets exceeding available disk space  

---

### CSV Input Data Specification

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

These names must match exactly (same spelling and casing).  
Columns with different names (e.g., `Model`, `StationID`, `Longitude_deg`, `site_name`) will **not** be automatically recognized as dimensions and will instead be treated as regular data variables.

No automatic renaming or fuzzy matching is performed.

For example:

- `model` → recognized ✔️  
- `Model` → NOT recognized ❌  
- `station` → recognized ✔️  
- `station_id` → NOT recognized ❌

Recognized dimension columns are converted to categorical coordinates in xarray and used to build a multidimensional dataset.

---

#### Long Format for Multimodel Data

For datasets containing multiple models, stations, or scenarios, a **long format** is required:

| Date | model | station | variable |
|------|-------|---------|----------|
| ...  | M1    | S1      | ...      |

Each row represents one observation defined by:

- Time (Date column)
- One or more dimension columns (model, station, scenario, etc.)
- One or more data variables

The combination of time + dimension columns must uniquely identify each observation.

If duplicates exist, the conversion will fail.

---

Wide formats are NOT supported.

Tables where models, stations, or scenarios are encoded in column names — for example:

- `flow_M1`, `flow_M2`
- `temperature_modelA`
- one column per station or model

will not be interpreted as multidimensional data.

Such columns will be treated as independent variables, not as coordinates.

As a result, advanced features of the tool will not be available, including:

- Inter-model statistics (e.g., averages across models)
- Model envelopes (min/max across models)
- Dimension-based filtering
- Multidimensional visualizations

To use these features, the dataset must be converted to long format with explicit dimension columns.

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


Example of a valid CSV containing a single time series (no additional dimensions):

```csv
Date;flow
01/01/2000;12.5
02/01/2000;13.1
03/01/2000;11.8
```
---

#### Example Multidimensional CSV

Example of a valid CSV containing multiple models and stations (long format):

```csv
Date;model;station;flow
01/01/2000;M1;S1;12.5
01/01/2000;M2;S1;13.2
02/01/2000;M1;S1;12.9
```


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

* **Bar Chart**
  
  Displays values of a variable as bars for categories or points on the X-axis.  
  - Can compare multiple series side by side (e.g., different models, stations, or scenarios).  
  - X-axis can represent time, categories, months, or other dimensions.  
  - Bars can be sorted if X-axis represents months, seasons, or categorical data.  
  - Useful for comparing values across groups or over a period.

* **Line Chart**
  
  Shows a variable as a line over time or another continuous dimension.  
  - Supports multiple Y variables simultaneously.  
  - Can display model envelopes (min-max range) or individual model lines.  
  - Ideal for visualizing temporal trends, changes, or comparisons across models, stations, or scenarios.

* **Scatter Plot**
 
  Displays individual observations as points to show the relationship between two variables.  
  - Multiple Y variables can be plotted against a single X variable.  
  - Useful for detecting correlations, clusters, or outliers.

* **Radar Chart**
  
  Compares multiple variables or entities on a circular grid.  
  - Each axis represents a variable or indicator.  
  - Useful for comparing profiles across models, stations, or scenarios.  
  - Requires at least 3 categories for meaningful visualization.

* **Histogram**
  
  Shows the distribution of a numeric variable.  
  - Values are grouped into bins on the X-axis; frequency is on the Y-axis.  
  - Can handle multiple series for comparison.  
  - Useful to visualize variability, detect skewness, or identify extreme values.

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
