# Import of the packages needed

import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import statistics_xr as stat_xr
import visualization_xr as visu_xr
import data_formatting as dt_form
import indicators_xr as indic_xr
from pathlib import Path
from os import makedirs

#Determine file format
supported_file_format = {
        1: "NetCDF",
        2: "CSV"
    }


while True:

    print("\nSupported file formats:")
    for num, name in supported_file_format.items():
        print(f"[{num}] {name}")

    print("\nNote: Multiple files are supported only for NetCDF files.")

    user_input = input("\nSelect the format of your file: ").strip()

    # Check that it's an integer
    try:
        file_format = int(user_input)
    except ValueError:
        print("Invalid input. Please enter a number.")
        continue

    # Check that it's a valid choice
    if file_format not in supported_file_format:
        print("Invalid choice, please try again.")
        continue

    break



#Opening CSV file
if supported_file_format[file_format] == "CSV":

    path = input("Please enter your path to your file :")
    path = Path(path.strip().replace("\\", "/"))

    ds = dt_form.csv_to_xarray(path)

#Opening NetCDF file(s)
elif supported_file_format[file_format] == "NetCDF": # NetCDF case

    paths = input("Enter path(s) separated by commas : ").split(",")

    paths = [Path(p.strip().replace("\\", "/")) for p in paths]

    ds = dt_form.load_multiple_datasets(paths)


#Creation of dictionaries
dict_visu={"bar chart":1,"scatter plot":2,"line chart":3, "radar chart":4, "histogram chart":5}
menu_visu = {
    1: visu_xr.bar_chart,
    2: visu_xr.scatter_chart,
    3: visu_xr.line_chart,
    4: visu_xr.radar_chart,
    5: visu_xr.histogram_chart
}

dict_stats={"Flexible mean":1,"Flexible maximum":2, "Flexible minimum":3, "Flexible percentile":4, "Temporal rolling mean":5, "Monthly Interannual average":6}
menu_stats_xr = {
    1: stat_xr.mean_value_flexible,
    2: stat_xr.maximum_value_flexible,
    3: stat_xr.minimum_value_flexible,
    4: stat_xr.percentile_value_flexible,
    5: stat_xr.rolling_mean_value,
    6: stat_xr.monthly_interannual_average_xr
}

# Indicator selection dictionaries

dict_indicateurs = {
    "IPS": 1,
    "Qmean": 2,
    "Q90/95": 3,
    "Q10/05": 4,
    "VCN10": 5,
    "VCX3": 6,
    "over_threshold":7
}

menu_indicateurs = {
    1:indic_xr.IPS,
    2:indic_xr.Qmean,
    3:indic_xr.Q90_95,
    4:indic_xr.Q10_05,
    5:indic_xr.VCN10,
    6:indic_xr.VCX3,
    7:indic_xr.over_threshold
}


while True:
# Ask for indicators
    while True:
        print("\nAvailable indicators:")
        for name, num in dict_indicateurs.items():
            print(f"[{num}] {name}")

        # indicator_choice = int(input("Entrez le numéro de l'indicateur à calculer (0 pour terminer) : "))
        while True:
            try:
                indicator_choice = int(input("Enter the number of the indicator to calculate (0 to finish): "))

                if indicator_choice == 0:
                    break

                if indicator_choice not in menu_indicateurs:
                    print("Invalid choice, please try again.")
                    continue

                break

            except ValueError:
                print("Please enter a valid integer.")
        if indicator_choice == 0:
            break  # exit the loop

        # Call the chosen function
        ds = menu_indicateurs[indicator_choice](ds)


    # Ask for statistics
    while True:
        print("\nAvailable statistical calculations:")
        for name, num in dict_stats.items():
            print(f"[{num}] {name}")

        while True:
            try:
                stat_choice = int(input("Enter the number of the stat to apply (0 to finish): "))

                if stat_choice == 0:
                    break

                if stat_choice not in menu_stats_xr:
                    print("Invalid choice, please try again.")
                    continue

                break

            except ValueError:
                print("Please enter a valid integer.")
        if stat_choice == 0:
            break  # exit the loop
        
        # Call the chosen function
        ds = menu_stats_xr[stat_choice](ds)

    # Ask for visualization
    print("\nAvailable visualizations:")
    for name, num in dict_visu.items():
        print(f"[{num}] {name}")
    #visualization = int(input("Enter the index of the visualization you want: "))
    while True:
        try:
            visualization = int(input("Enter the index of the visualization you want: "))

            if visualization not in menu_visu:
                print("Invalid choice.")
                continue

            break

        except ValueError:
            print("Please enter a valid integer.")

    makedirs("output", exist_ok=True)

    fig = menu_visu[visualization](ds)
    plt.savefig(f"output/{menu_visu[visualization].__name__}.png", bbox_inches="tight")
    print("Displaying the figure, close the window to continue the script.")
    plt.show()
    plt.close(fig)

    print(f"{menu_visu[visualization].__name__}.png saved in output/")


    # choice to continue
    while True:
        continuer = input(
            "\nDo you want to perform another analysis/visualization on this file? (y/n): "
        ).strip().lower()

        if continuer in ["y", "n"]:
            break

        print("Invalid input. Please answer with 'y' or 'n'.")

    if continuer != "y":
        print("End of program. Goodbye!")
        break