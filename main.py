#######################
#######################
# Import of the packages needed

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# Ask for the path to the file we want to analyze
path = Path(input("Please enter your path to your file (with / instead of anti-slash and without quotation marks):"))

suffix = path.suffix.lower()

if suffix == ".csv":
    print("It is a CSV")
elif suffix in (".nc", ".nc4", ".netcdf"):
    print("it is a NetCDF")
else:
    print("It is not a CSV nor a NetCDF")