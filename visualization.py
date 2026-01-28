import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# ---------------- Create test DataFrame ----------------
np.random.seed(42)

import numpy as np
import pandas as pd

np.random.seed(42)

columns = ["col1", "col2", "col3", "col4"]

# Create col1 explicitly
col1 = np.arange(1, 21)  # 1, 2, ..., 20

# Create DataFrame for the remaining columns (col2, col3, col4)
df_test = pd.DataFrame(
    np.random.rand(20, 3) * 20 + 10,  # values between 10 and 30
    columns=columns[1:]
)

# Insert col1 as the first column
df_test.insert(0, "col1", col1)

print("Test DataFrame:")
print(df_test.head())


# ---------------- Bar Chart ----------------

def bar_chart(df, col1, col2, title="Bar Chart", xlabel=None, ylabel=None, display=True):
    """
    Displays a bar chart using one column for categories (x-axis) and one column for values (y-axis).

    Parameters:
    df      : pandas DataFrame containing the data
    col1    : str, column name for x-axis (categories)
    col2    : str, column name for y-axis (values)
    title   : str, optional, title of the chart
    xlabel  : str, optional, label for x-axis (defaults to col1)
    ylabel  : str, optional, label for y-axis (defaults to col2)
     
    Example:
    bar_chart(df, "Day", "Precipitation", title="Daily Precipitation")

    """
    x = df[col1]
    y = df[col2]
    
    colors = cm.viridis(np.linspace(0, 1, len(x)))  # different color per bar
    plt.figure(figsize=(8,5))
    plt.bar(x, y, color=colors)
    
    plt.title(title)
    plt.xlabel(xlabel if xlabel else col1)
    plt.ylabel(ylabel if ylabel else col2)
    
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    
    # Display value on top of each bar
    if display: 
        for i, v in enumerate(y):
            plt.text(i+1, v + 0.1, f"{v:.2f}", ha='center', va='bottom')
    
    plt.show()



# ---------------- Line Chart ----------------

def line_chart(df, col1, columns, title="Line Chart", xlabel=None, ylabel=None, step=None):
    """
    Displays a line chart using one column for the x-axis and one or several columns for y-axis lines.

    Parameters:
    df      : pandas DataFrame containing the data
    col1    : str, column name for x-axis
    columns : list of str, column names to plot as lines
    title   : str, optional, title of the chart
    xlabel  : str, optional, label for x-axis (defaults to col1)
    ylabel  : str, optional, label for y-axis (defaults to "Values")
    step    : float, optional, step size for the grid on x and y axes
     
    Example:
    line_chart(df, "Time", ["Temperature1", "Temperature2"], title="Mean Temperature vs Time", step=2)
    """
    colors = cm.viridis(np.linspace(0, 1, len(columns)))  # generate different colors per line
    plt.figure(figsize=(10,6))
    
    # Plot each line
    for i, col in enumerate(columns):
        plt.plot(df[col1], df[col].astype(float), marker='o', color=colors[i], label=col)

    plt.title(title)
    plt.xlabel(xlabel if xlabel else col1)
    plt.ylabel(ylabel if ylabel else "Values")
    plt.ylim(bottom=0)  # start y-axis at 0
    
    # Optional: grid with step
    if step and step > 0:
        x_min, x_max = df[col1].min(), df[col1].max()
        y_min, y_max = 0, df[columns].max().max()
        plt.xticks(np.arange(x_min, x_max + step, step))
        plt.yticks(np.arange(y_min, y_max + step, step))
    
    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    plt.legend()
    plt.show()


##-------------- Scatter Plot ---------------

def scatter_chart(df, col1, columns, title="Scatter Plot", xlabel=None, ylabel=None, step=None):
    """
    Displays a scatter plot using one column for the x-axis and one or several columns for y-axis points.

    Parameters:
    df      : pandas DataFrame containing the data
    col1    : str, column name for x-axis
    columns : list of str, column names to plot as scatter points
    title   : str, optional, title of the chart
    xlabel  : str, optional, label for x-axis (defaults to col1)
    ylabel  : str, optional, label for y-axis (defaults to "Values")
    step    : float, optional, step size for the grid on x and y axes
     
    Example:
    scatter_chart(df, "Precipitation", ["fluid_flow1", "fluid_flow2"], title="Mean fluid flow vs precipitation", step=2)
    """
    colors = cm.viridis(np.linspace(0, 1, len(columns)))  # different color per column
    plt.figure(figsize=(10,6))
    
    # Plot each column as scatter points
    for i, col in enumerate(columns):
        plt.scatter(df[col1], df[col].astype(float), color=colors[i], label=col, s=50)

    plt.title(title)
    plt.xlabel(xlabel if xlabel else col1)
    plt.ylabel(ylabel if ylabel else "Values") 
    plt.ylim(bottom=0)
    plt.xlim(left=0)
    
    
    if step and step > 0: # Grid with optional step
        x_min, x_max = df[col1].min(), df[col1].max()
        y_min, y_max = 0, df[columns].max().max()
        plt.xticks(np.arange(x_min, x_max + step, step))
        plt.yticks(np.arange(y_min, y_max + step, step))
    
    plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.5)
    plt.legend()
    plt.show()



# ----------------- Test -----------------

# Bar chart 
bar_chart(df_test, "col1", "col2", title="Bar Chart")

# Line chart
line_chart(df_test, "col1", columns=[ "col2", "col3", "col4"], title="Line Chart Test")

# scatter plot
scatter_chart(df_test, "col1", columns=[ "col2", "col3", "col4"])
