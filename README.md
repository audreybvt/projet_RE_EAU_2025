# PROJECT CENTRALESUPELEC-BRGM 2025-2026
## Table of Contents

- [Hydrological Visualization Tool](#hydrological-visualization-tool)
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
    - [Datasets chunking](#datasets-chunking)
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
- [Spatial dimension handling](#spatial-dimension-handling)
- [Required Libraries](#required-libraries)
  - [Core dependencies](#core-dependencies)
  - [Installation with pip and requirements.txt](#installation-with-pip-and-requirementstxt)
- [How to Run](#how-to-run)
- [Workflow Overview](#workflow-overview)
- [How to update the code](#how-to-update-the-code)
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
- netcdf4  
- **streamlit** (for GUI)

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
python run streamlit gui_streamlit_xarray.py
```

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
├── gui_streamlit_xarray.py   # Main GUI script (Streamlit)
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
3. Augmented with model and scenario metadata
4. Combined into a single dataset

Combination is performed using `xarray.combine_by_coords`. Note that other metadata are discarded to avoid conflicts.

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

If the first option is selected, the following calculations (indicators and statistics) will be made over all the spatial dimension (note that this could lead to a long running time). Then, for the visualization, the user will have to chose wether to average over the spatial dimension or to chose specific location(s).

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

### Datasets chunking

After adding scenario and model dimensions, the datasets are split using the module `.chunk()`. This module split the dataset into smaller pieces. When the code is processed, these pieces are loaded on the RAM one after an other instead of loading all the dataset at once. Thus, it is possible to overcome memory size limitation and to be able to process larger data.

The code first try to do this spliting over time dimension and spatial dimension and, if it was not possible, split over the largest dimension.

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

## CSV Input Data Specification

- Single file only  
- Must be a structured table (rows = observations, columns = variables)  
- Columns must be separated by semicolons (`;`)
- Long format is required for multimodel data
- Metadata lines before the header are allowed (user specifies how many to skip)

---

### Date Column (REQUIRED)

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

### Optional Dimension Columns

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

### Long Format for Multimodel Data

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

### Variable Columns

All remaining columns are interpreted as data variables.

- Must contain numeric values (preferred)
- Missing values are allowed
- Non-numeric columns (except dimensions) may be ignored or cause issues

---

### Not Supported

- Files without a valid date/time column  
- Wide-format Excel-style tables with multi-level headers  
- Duplicate rows for the same time + dimension combination  
- Multiple CSV files at once  
- Non-tabular formats  

---

### Example Minimal Valid CSV


Example of a valid CSV containing a single time series (no additional dimensions):

```csv
Date;flow
01/01/2000;12.5
02/01/2000;13.1
03/01/2000;11.8
```
---

### Example Multidimensional CSV

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

## Available Statistical Processing Functions

* **Flexible Mean**
   
  Computes the mean of a selected variable across one or more dimensions.  
  - User can choose which dimensions to average over (e.g., time, model, location).  
  - Optionally, a specific time period can be applied.  
  - Result is added to the dataset with a descriptive name indicating reduced dimensions and period.

* **Flexible Maximum**

  Computes the maximum value of a variable along selected dimensions.  
  - Supports optional time period selection.  
  - Useful for identifying peak values across models, locations, or time slices.

* **Flexible Minimum**
   
  Computes the minimum value of a variable along selected dimensions.  
  - Works similarly to the maximum function.  
  - Helps to identify extreme low values.

* **Flexible Percentile**
  
  Computes any specified percentile (e.g., 10th, 90th) along selected dimensions.  
  - Allows focusing on extremes or specific thresholds of data distribution.  
  - Output is named to indicate percentile and reduced dimensions.

* **Temporal Rolling Mean**
  
  Computes a rolling mean along the time dimension with a user-specified window size.  
  - Smooths short-term fluctuations to reveal trends.  
  - Supports optional period selection for analysis.

* **Monthly Interannual Average**
  
  Computes the average of a variable for each month across all years.  
  - Groups data by month, then averages across the selected time dimension.  
  - Useful for detecting seasonal patterns and long-term monthly trends.  
  - Output variable includes month names as coordinates for clarity.

---

## Available Hydrological Indicators

| Function Name | Indicator Description | Operational Logic & Time Step |
|---------------|----------------------|--------------------------------|
| **SWBI** | **Soil Water Balance Index.** Estimates potential groundwater recharge using the formula **SWBI = P − ETR − ΔR**. | **Continuous calculation.** The balance is computed for every time step in the dataset to estimate cumulative water input available for recharge. |
| **SPLI** | **Standardised Piezometric Level Indicator.** Normalized groundwater level index that expresses deviations from long-term average conditions. Used to identify groundwater drought or recharge anomalies. | **This function is not yet completed** |
| **Qmoy** | **Mean Discharge.** The average volume of water passing through a section over time. | **Period Aggregation.** The averaging window is user-defined (e.g., monthly or yearly) to analyze seasonal or inter-annual discharge trends. |
| **Q90_95** | **Low-Flow Quantiles.** Flow rates exceeded **90% or 95%** of the time. Used as drought indicators. | **Statistical Threshold.** Typically computed over a **1-year period** to assess annual drought severity, or **multi-year periods** (e.g., 10 years) for long-term climate analysis. |
| **VCN10** | **Minimum 10-Day Mean Flow.** Lowest average flow over **10 consecutive days**. Reflects aquifer depletion conditions. | **Rolling + Minimum.** A 10-day rolling average is computed, and the minimum value within the selected period (e.g., yearly) is retained. |
| **Q10_05** | **High-Flow Quantiles.** Flow rates exceeded only **10% or 5%** of the time. Used as flood indicators. | **High-Value Filter.** Data is split into blocks (e.g., every 6 months), and high-flow thresholds are calculated to identify peak runoff periods. |
| **VCX3** | **Maximum 3-Day Mean Flow.** Highest average flow over **3 consecutive days**. Reflects basin reactivity to intense rainfall. | **Rolling + Maximum.** A 3-day rolling average is computed, and the maximum value within the selected period (e.g., monthly) is retained to capture short-duration flood peaks. |
| **OTI** | **Over-Threshold Indicator.** | To be completed |

These indicators are computed directly on the dataset and can be chained with statistical operations.

---

## Graphical User Interface (GUI)

The project includes a modern web-based interface built with **Streamlit**. This is the recommended way to use the tool for most users, as it provides a more visual and intuitive workflow.

### GUI Features

*   **Easy Data Loading**: Upload your NetCDF or CSV files directly through the browser.
*   **Interactive Visualization**: Explore your data with zooming, panning, and real-time parameter updates.
*   **Visual Dimension Filtering**: Easily select specific models, scenarios, or locations using dropdown menus and checkboxes.
*   **Custom Styling**: Adjust chart titles, labels, and color schemes on the fly.
*   **Data Export**: Preview and download processed data as CSV files after computation.

### GUI Workflow & Features

The interface is organized into a **Sidebar** for data management and a **Main Panel** for analysis, split into three functional tabs:

1.  **Sidebar (Data Management)**:
    - **Upload**: Drop your files here. The app automatically detects dimensions and variables.
    - **Inventory**: View a summary of the dimensions (time range, models, stations) and variables available in the loaded dataset.
    - **Reset**: Quickly clear the session state to start a new analysis.

2.  **Tab 1: Indicators & Statistics**:
    - **Selection**: Choose one or more variables and the hydrological indicators to calculate (e.g., Qmean, VCN10).
    - **Aggregation**: Perform statistical operations (mean, percentile) by choosing which dimensions to reduce.
    - **Results**: Calculated indicators are automatically added to the internal dataset, allowing for chained calculations.

3.  **Tab 2: Visualization**:
    - **Chart Selection**: Choose from Line, Bar, Scatter, Radar, or Histogram.
    - **Filters**: Fine-tune the displayed data by selecting specific scenarios, models, or time periods.
    - **Axis & Labels**: Customize the look of your chart before downloading the figure.

4.  **Tab 3: Export**:
    - Preview the final processed dataset.
    - Download the resulting table as a CSV file for further use in other software.

### Technical Architecture (GUI)

The GUI is designed to be a lightweight wrapper around the project's core processing logic, ensuring consistency between the CLI and the web interface.

*   **Modular Processing**: The GUI imports and uses the exact same logic modules as the CLI (`indicators_xr.py`, `statistics_xr.py`). 
*   **Non-Blocking Logic**: All core functions were refactored to check if they are running in "GUI mode". When active, they bypass terminal-based `input()` prompts and instead rely on parameters passed directly from Streamlit widgets.
*   **Stateful Pipeline**: The application uses `st.session_state` to persist the `xarray.Dataset`. This allows users to build a "pipeline" of calculations (e.g., calculate an indicator, then calculate a rolling mean on that indicator) without reloading the data.
*   **Matplotlib Integration**: Visualizations are generated using Matplotlib (from `visualization_xr.py`) and rendered in the browser using `st.pyplot()`, maintaining high-quality scientific plotting standards.

### Launching the GUI

To run the graphical interface, use the following command in your terminal:

```bash
streamlit run gui_streamlit_xarray.py
```

---

## Spatial dimension handling

It is possible to handle spatial dimension using NetCDF files (but not CSV files) as explained in the "NetCDF Input Data Specification" part but note that the code is not yet accomplished for this feature as it was not part of the first objectives. Further work may thus be done.

---

## Required Libraries

The project relies on scientific Python libraries commonly used for environmental data analysis.

### Core dependencies

* pandas
* xarray
* matplotlib
* netCDF4
* **streamlit**
* pathlib (standard library)
* os (standard library)

---

### Installation with pip and requirements.txt

Install all required packages:

```bash
pip install -r requirements.txt
```

---

### 1. Run the GUI (Recommended)

```bash
streamlit run gui_streamlit_xarray.py
```

### 2. Run the CLI version

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

## How to update the code

### Add a supported file format

1. **Create loader function** in `data_formatting.py`:
   ```python
   def your_format_to_xarray(filepath):
       """
       Convert YOUR_FORMAT to xarray.Dataset.
       Follow patterns of csv_to_xarray() or load_multiple_datasets().
       """
       # Implementation
       # Return: xarray.Dataset
   ```

2. **Update CLI menu** in `main_full_xarray.py`:
   ```python
   supported_file_format = {
       1: "NetCDF",  # existing
       2: "CSV",     # existing
       3: "YOUR_FORMAT"  # ← ADD THIS
   }
   ```

3. **Add loader call** after format selection:
   ```python
   elif supported_file_format[file_format] == "YOUR_FORMAT":
       path = input("Enter path: ")
       ds = dt_form.your_format_to_xarray(path)
   ```

4. **Test**: Run `python main_full_xarray.py`, select new format.

### Modify Plot Features and add visualization

**Note**: `visualization_xr.py` uses factored helpers like `ask_variable()`, `handle_xarray_dimensions()`, `configure_plot()`. Reuse these for consistency.

1. **Edit existing function** (e.g., `line_chart()`).

2. **Or add new visualization**:
   ```python
   def your_new_chart(ds):
       """
       New plot type following existing patterns.
       Use helpers: ask_variable(), configure_plot()
       """
       fig, ax = plt.subplots()
       # Plot code
       return fig
   ```

3. **Update visualization menu** in `main_full_xarray.py`:
   ```python
   dict_visu = {
       "bar chart": 1,           # existing
       # ...
       "your new chart": 6       # ← ADD THIS
   }
   menu_visu = {
       # existing...
       6: visu_xr.your_new_chart  # ← ADD THIS
   }
   ```

4. **Test**: Run script, select visualization → new plot appears + saves to `output/`.

### Add indicators or statistics

**Note**: Modules use **factored helper functions** (e.g., `categorical_filter()`, `get_time_freq()`, `ask_date()`) for common tasks. Reuse these in new functions to maintain consistency.

**For Indicators** (`indicators_xr.py`):
1. **Create function**:
   ```python
   def your_indicator(ds):
       """
       Compute new hydrological indicator.
       Input: xarray.Dataset
       Output: ds with new variable(s)
       """
       # Reuse helpers:
       # active_ds, selections = categorical_filter(ds, standard_dims)
       # freq, unite, nb, label = get_time_freq()
       # Example: ds['new_indicator'] = calculation
       return ds
   ```

**For Statistics** (`statistics_xr.py`):
1. **Create function** following `mean_value_flexible()` pattern, reusing `apply_time_selection()`, `ask_date()`.

2. **Update main menu** (`main_full_xarray.py`):
   ```python
   # For indicators:
   dict_indicateurs["Your Indicator"] = 9  # next number
   menu_indicateurs[9] = indic_xr.your_indicator

   # For statistics:
   dict_stats["Your Stat"] = 7
   menu_stats_xr[7] = stat_xr.your_stat
   ```

3. **Test**: New option appears in interactive menu.

### General Guidelines

- **Always** return modified `xarray.Dataset` from processing functions
- **New variables** get descriptive names (e.g., `Q90_3M_flow`)
- **Dependencies**: Add to `requirements.txt`, test `pip install -r requirements.txt`
- **Testing**: `python main_full_xarray.py` → full workflow unchanged
- **Spatial dims**: Support `handle_spatial_dimensions()` pattern for NetCDF
- **Multi-model**: Respect `scenario`/`model` dimensions auto-created from NetCDF attrs

**Example full addition**:
```
1. New func → indicators_xr.py
2. dict_indicateurs["New"] = N
3. menu_indicateurs[N] = indic_xr.new_func
4. Test!
```

---

### Leads for improvement identified

In this part we highlights features that we did not have the time to accomplished or some leads that we have identified to improve our code. This list is not exhaustive and all relevant improvement is welcomed.

#### Spatial dimension handling

So far the code is able to handle spatial dimension in a basic way only for NetCDF files. It checks if the files have a spatial dimension an give two options : keep all locations found or chose one. If all locations are kept, two options are availble for ploting : chose location(s), or average over all locations. This last option is physically not appropriate as it can average hydrological data over several water basins which does not make sense.

User should be able to chose to conduct they calculation either on one location or over an area included in a water basin. This choice could be masde using locations' coordinates instead of using stations' number as it is currently done.

It could be intersting to handle spatial dimension for other file type as well.

#### Ability to compare different time periods

Currently, it is possible to compute statistical metrics and indicators over multiple time periods by running separate calculations. Each calculation performed on a different period creates a new variable in the dataset.

However, the current visualization tools do not allow the superposition of results from different periods, which limits direct comparison between them.

For example, it is possible to compute monthly mean precipitation over 1 year using 10-year reference periods, calculated separately for different decades. However, it is not currently possible to overlay these decade-based results on the same visualization to compare them directly.

It would therefore be valuable to add functionality allowing users to overlay and compare results from different time periods within the same visualization.

#### Option to download the output file

Users may wish to retain the results of their calculations (statistics and/or indicators) at the end of the process. 

To support this, an option should be provided to download the processed dataset. If selected, the output file can be formatted either as a CSV file or a NetCDF file.


---

## Notes

* Multiple files are supported **only for NetCDF**
* Input data must be properly formatted

---

## Authors

Project developed as part of the RE_EAU_2025 project.