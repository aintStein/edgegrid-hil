# Imports shutil for use in this program.
import shutil
# Supports the calculation, data processing, or display operation on this line.
from datetime import datetime
# Supports the calculation, data processing, or display operation on this line.
from pathlib import Path

# Imports pandas to read and analyse CSV tables.
import pandas as pd
# Imports Streamlit to build the interactive dashboard.
import streamlit as st


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

# Configures the dashboard page title and layout.
st.set_page_config(
    # Assigns a value to a variable for later use.
    page_title="Smart Township Energy Dashboard",
    # Assigns a value to a variable for later use.
    layout="wide"
# Continues or closes the surrounding function call or data structure.
)

# Finds the folder where this dashboard script is saved.
BASE_DIR = Path(__file__).resolve().parent

# Builds the path to the relevant input or results CSV file.
ENERGY_INPUT_FILE = BASE_DIR / "energy_data.csv"
# Builds the path to the relevant input or results CSV file.
ENERGY_FILE = BASE_DIR / "energy_results.csv"
# Builds the path to the relevant input or results CSV file.
NORMAL_FILE = BASE_DIR / "normal_results.csv"
# Builds the path to the relevant input or results CSV file.
SMART_FILE = BASE_DIR / "smart_results.csv"


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

# Defines a helper that safely loads a CSV file.
def load_csv(file_path):
    # Documents the purpose of this function.
    """Load a CSV file safely. Return None if unavailable."""
    # Checks a condition before running the following code.
    if not file_path.exists():
        # Returns the calculated value or result to the caller.
        return None

    # Starts a block that handles possible errors.
    try:
        # Reads the CSV file into a pandas DataFrame.
        df = pd.read_csv(file_path)
        # Returns the calculated value or result to the caller.
        return None if df.empty else df
    # Handles file-reading or CSV-format errors.
    except (
        # Supports the calculation, data processing, or display operation on this line.
        OSError,
        # Supports the calculation, data processing, or display operation on this line.
        pd.errors.ParserError,
        # Supports the calculation, data processing, or display operation on this line.
        pd.errors.EmptyDataError,
        # Supports the calculation, data processing, or display operation on this line.
        UnicodeDecodeError,
    # Begins a code block for the condition, loop, or context above.
    ):
        # Returns the calculated value or result to the caller.
        return None


# Defines a helper that safely reads a numeric value from a row.
def numeric_value(row, column, default=0.0):
    # Documents the purpose of this function.
    """Read one numeric value from a row safely."""
    # Checks a condition before running the following code.
    if column not in row.index:
        # Returns the calculated value or result to the caller.
        return default

    # Converts values to numbers and handles invalid entries.
    value = pd.to_numeric(row[column], errors="coerce")
    # Returns the calculated value or result to the caller.
    return default if pd.isna(value) else float(value)


# Defines a helper that totals a numeric column.
def sum_column(df, column):
    # Documents the purpose of this function.
    """Sum a numeric column safely."""
    # Checks a condition before running the following code.
    if df is None or column not in df.columns:
        # Returns the calculated value or result to the caller.
        return 0.0

    # Returns the calculated value or result to the caller.
    return pd.to_numeric(df[column], errors="coerce").fillna(0).sum()


# Defines a helper that formats an energy value in kWh.
def format_kwh(value):
    # Returns the calculated value or result to the caller.
    return f"{value:,.2f} kWh"


# Defines a helper that filters rows for the selected household.
def filter_house(df, selected_house):
    # Documents the purpose of this function.
    """Filter a DataFrame to one house or all houses."""
    # Checks a condition before running the following code.
    if df is None:
        # Returns the calculated value or result to the caller.
        return None

    # Checks a condition before running the following code.
    if selected_house == "All Houses" or "House ID" not in df.columns:
        # Returns the calculated value or result to the caller.
        return df.copy()

    # Returns the calculated value or result to the caller.
    return df[df["House ID"].astype(str) == str(selected_house)].copy()


# Defines a helper that collects household IDs without duplicates.
def unique_house_values(*dataframes):
    # Documents the purpose of this function.
    """Collect unique household IDs across available CSV files."""
    # Starts a list of values used by the dashboard.
    values = []

    # Loops through each item in the collection.
    for df in dataframes:
        # Checks a condition before running the following code.
        if df is not None and "House ID" in df.columns:
            # Supports the calculation, data processing, or display operation on this line.
            values.extend(df["House ID"].dropna().tolist())

    # Returns the calculated value or result to the caller.
    return list(dict.fromkeys(str(value) for value in values))


# Defines a helper that keeps one summary row per household.
def household_summary(df):
    # Documents the purpose of this function.
    """Keep one household-level summary row to avoid counting it per AC."""
    # Checks a condition before running the following code.
    if df is None or df.empty or "House ID" not in df.columns:
        # Returns the calculated value or result to the caller.
        return pd.DataFrame()

    # Returns the calculated value or result to the caller.
    return df.drop_duplicates(subset=["House ID"]).copy()


# Defines a helper that finds the first available column name.
def first_existing_column(df, candidates):
    # Checks a condition before running the following code.
    if df is None:
        # Returns the calculated value or result to the caller.
        return None

    # Loops through each item in the collection.
    for column in candidates:
        # Checks a condition before running the following code.
        if column in df.columns:
            # Returns the calculated value or result to the caller.
            return column

    # Returns the calculated value or result to the caller.
    return None


# Defines a helper that displays a CSV download button.
def display_download_button(label, df, filename, key):
    # Checks a condition before running the following code.
    if df is not None:
        # Creates a button to download data as a CSV file.
        st.download_button(
            # Assigns a value to a variable for later use.
            label=label,
            # Converts the DataFrame into CSV format.
            data=df.to_csv(index=False).encode("utf-8"),
            # Assigns a value to a variable for later use.
            file_name=filename,
            # Assigns a value to a variable for later use.
            mime="text/csv",
            # Assigns a value to a variable for later use.
            key=key,
        # Continues or closes the surrounding function call or data structure.
        )


# ==========================================
# 3. LOAD RESULT FILES
# ==========================================

# Assigns a value to a variable for later use.
energy_df = load_csv(ENERGY_FILE)
# Assigns a value to a variable for later use.
normal_df = load_csv(NORMAL_FILE)
# Assigns a value to a variable for later use.
smart_df = load_csv(SMART_FILE)


# ==========================================
# 4. DASHBOARD HEADER
# ==========================================

# Displays the main dashboard title.
st.title("Smart Township Energy Optimisation")

# Displays explanatory text on the dashboard.
st.write(
    # Provides a text label or message used by the dashboard.
    "Monitor household energy balance and compare normal AC control "
    # Provides a text label or message used by the dashboard.
    "with smart solar-aware AC scheduling."
# Continues or closes the surrounding function call or data structure.
)

# Displays a smaller explanatory caption.
st.caption(
    # Provides a text label or message used by the dashboard.
    "Simulation dashboard. Energy values are in kWh per simulation interval. "
    # Provides a text label or message used by the dashboard.
    "This dashboard uses saved CSV results, not live energy meters."
# Continues or closes the surrounding function call or data structure.
)


# ==========================================
# 5. DATA FILE STATUS
# ==========================================

# Displays a subsection heading.
st.subheader("Data File Status")

# Creates columns to arrange dashboard content horizontally.
status1, status2, status3 = st.columns(3)

# Groups the following operations under this Streamlit layout or context.
with status1:
    # Checks a condition before running the following code.
    if energy_df is not None:
        # Displays a success message.
        st.success("energy_results.csv loaded")
    # Runs this alternative branch when the preceding condition is false.
    else:
        # Displays a warning message.
        st.warning("energy_results.csv unavailable")

# Groups the following operations under this Streamlit layout or context.
with status2:
    # Checks a condition before running the following code.
    if normal_df is not None:
        # Displays a success message.
        st.success("normal_results.csv loaded")
    # Runs this alternative branch when the preceding condition is false.
    else:
        # Displays a warning message.
        st.warning("normal_results.csv unavailable")

# Groups the following operations under this Streamlit layout or context.
with status3:
    # Checks a condition before running the following code.
    if smart_df is not None:
        # Displays a success message.
        st.success("smart_results.csv loaded")
    # Runs this alternative branch when the preceding condition is false.
    else:
        # Displays a warning message.
        st.warning("smart_results.csv unavailable")

# Checks a condition before running the following code.
if energy_df is None:
    # Displays a warning message.
    st.warning("Run `python3 energy.py` to generate energy_results.csv.")

# Checks a condition before running the following code.
if normal_df is None:
    # Displays an informational message.
    st.info("Method A results are unavailable. Run `python3 normal.py`.")

# Checks a condition before running the following code.
if smart_df is None:
    # Displays an informational message.
    st.info("Method B results are unavailable. Run `python3 smart.py`.")

# Checks a condition before running the following code.
if all(df is None for df in [energy_df, normal_df, smart_df]):
    # Stops the dashboard from continuing.
    st.stop()


# ==========================================
# 6. HOUSEHOLD FILTER
# ==========================================

# Adds a filter or message to the dashboard sidebar.
st.sidebar.header("Dashboard Filters")

# Assigns a value to a variable for later use.
houses = unique_house_values(energy_df, normal_df, smart_df)

# Checks a condition before running the following code.
if not houses:
    # Displays an error message.
    st.error("No House ID column was found in the available CSV files.")
    # Stops the dashboard from continuing.
    st.stop()

# Adds a filter or message to the dashboard sidebar.
selected_house = st.sidebar.selectbox(
    # Provides a text label or message used by the dashboard.
    "Select household",
    # Supports the calculation, data processing, or display operation on this line.
    ["All Houses"] + houses,
# Continues or closes the surrounding function call or data structure.
)

# Adds a filter or message to the dashboard sidebar.
st.sidebar.caption(
    # Provides a text label or message used by the dashboard.
    "Choose All Houses for the overall view or select one household."
# Continues or closes the surrounding function call or data structure.
)

# Assigns a value to a variable for later use.
energy_view = filter_house(energy_df, selected_house)
# Assigns a value to a variable for later use.
normal_view = filter_house(normal_df, selected_house)
# Assigns a value to a variable for later use.
smart_view = filter_house(smart_df, selected_house)


# ==========================================
# 7. HOUSEHOLD ENERGY OVERVIEW
# ==========================================

# Displays a main section heading.
st.header("1. Household Energy Overview")

# Checks a condition before running the following code.
if energy_view is not None:
    # Assigns a value to a variable for later use.
    solar_col = "Solar Generation (kWh)"
    # Assigns a value to a variable for later use.
    demand_col = "House Electricity Demand (kWh)"
    # Assigns a value to a variable for later use.
    surplus_col = "Surplus Solar (kWh)"
    # Assigns a value to a variable for later use.
    shortfall_col = "Power Shortfall (kWh)"

    # Checks a condition before running the following code.
    if solar_col in energy_view.columns and demand_col in energy_view.columns:
        # Assigns a value to a variable for later use.
        solar_total = sum_column(energy_view, solar_col)
        # Assigns a value to a variable for later use.
        demand_total = sum_column(energy_view, demand_col)
        # Assigns a value to a variable for later use.
        surplus_total = sum_column(energy_view, surplus_col)
        # Assigns a value to a variable for later use.
        shortfall_total = sum_column(energy_view, shortfall_col)

        # Creates columns to arrange dashboard content horizontally.
        col1, col2, col3, col4 = st.columns(4)

        # Displays a key performance indicator.
        col1.metric("Solar Generation", format_kwh(solar_total))
        # Displays a key performance indicator.
        col2.metric("Household Demand", format_kwh(demand_total))
        # Displays a key performance indicator.
        col3.metric("Solar Surplus", format_kwh(surplus_total))
        # Displays a key performance indicator.
        col4.metric("Power Shortfall", format_kwh(shortfall_total))
    # Runs this alternative branch when the preceding condition is false.
    else:
        # Displays a warning message.
        st.warning(
            # Provides a text label or message used by the dashboard.
            "energy_results.csv must include Solar Generation (kWh) "
            # Provides a text label or message used by the dashboard.
            "and House Electricity Demand (kWh)."
        # Continues or closes the surrounding function call or data structure.
        )

    # Assigns a value to a variable for later use.
    temperature_col = "Current Room Temperature (°C)"
    # Checks a condition before running the following code.
    if temperature_col in energy_view.columns:
        # Displays a subsection heading.
        st.subheader("Current Room Temperature")

        # Assigns a value to a variable for later use.
        temperature_table = energy_view[
            # Supports the calculation, data processing, or display operation on this line.
            ["House ID", temperature_col]
        # Creates a copy so changes do not modify the original DataFrame.
        ].copy()

        # Converts values to numbers and handles invalid entries.
        temperature_table[temperature_col] = pd.to_numeric(
            # Assigns a value to a variable for later use.
            temperature_table[temperature_col], errors="coerce"
        # Continues or closes the surrounding function call or data structure.
        )

        # Displays a DataFrame as an interactive table.
        st.dataframe(
            # Supports the calculation, data processing, or display operation on this line.
            temperature_table,
            # Assigns a value to a variable for later use.
            use_container_width=True,
            # Assigns a value to a variable for later use.
            hide_index=True,
        # Continues or closes the surrounding function call or data structure.
        )

        # Assigns a value to a variable for later use.
        temperature_chart = temperature_table.dropna()
        # Checks a condition before running the following code.
        if not temperature_chart.empty:
            # Displays a subsection heading.
            st.subheader("Room Temperature by Household")
            # Displays a bar chart from the supplied data.
            st.bar_chart(temperature_chart.set_index("House ID"))
    # Runs this alternative branch when the preceding condition is false.
    else:
        # Displays a warning message.
        st.warning(
            # Provides a text label or message used by the dashboard.
            "Current Room Temperature (°C) is missing from energy_results.csv. "
            # Provides a text label or message used by the dashboard.
            "Update energy.py to preserve this column from energy_data.csv."
        # Continues or closes the surrounding function call or data structure.
        )
# Runs this alternative branch when the preceding condition is false.
else:
    # Displays an informational message.
    st.info("Household energy results are not available.")


# ==========================================
# 8. ENERGY BALANCE TABLE AND GRAPH
# ==========================================

# Displays a main section heading.
st.header("2. Energy Balance by House")

# Checks a condition before running the following code.
if energy_view is not None:
    # Displays a DataFrame as an interactive table.
    st.dataframe(
        # Supports the calculation, data processing, or display operation on this line.
        energy_view,
        # Assigns a value to a variable for later use.
        use_container_width=True,
        # Assigns a value to a variable for later use.
        hide_index=True,
    # Continues or closes the surrounding function call or data structure.
    )

    # Starts a list of values used by the dashboard.
    chart_columns = [
        # Provides a text label or message used by the dashboard.
        "House ID",
        # Provides a text label or message used by the dashboard.
        "Solar Generation (kWh)",
        # Provides a text label or message used by the dashboard.
        "House Electricity Demand (kWh)",
    # Continues or closes the surrounding function call or data structure.
    ]

    # Checks a condition before running the following code.
    if all(column in energy_view.columns for column in chart_columns):
        # Creates a copy so changes do not modify the original DataFrame.
        chart_df = energy_view[chart_columns].copy()
        # Sets the selected column as the chart or table index.
        chart_df = chart_df.set_index("House ID")
        # Assigns a value to a variable for later use.
        chart_df = chart_df.rename(
            # Starts a dictionary of related values.
            columns={
                # Provides a text label or message used by the dashboard.
                "Solar Generation (kWh)": "Solar Generation (kWh)",
                # Provides a text label or message used by the dashboard.
                "House Electricity Demand (kWh)": "Household Demand (kWh)",
            # Supports the calculation, data processing, or display operation on this line.
            }
        # Continues or closes the surrounding function call or data structure.
        )

        # Displays a subsection heading.
        st.subheader("Solar Generation vs Household Demand")
        # Displays a bar chart from the supplied data.
        st.bar_chart(chart_df)
# Runs this alternative branch when the preceding condition is false.
else:
    # Displays an informational message.
    st.info("No energy balance data is available.")


# ==========================================
# 9. METHOD A: NORMAL AC CONTROL
# ==========================================

# Displays a main section heading.
st.header("3. Method A — Normal AC Control")

# Displays explanatory text on the dashboard.
st.write(
    # Provides a text label or message used by the dashboard.
    "Each AC makes an independent decision using room temperature "
    # Provides a text label or message used by the dashboard.
    "and the user's comfort settings."
# Continues or closes the surrounding function call or data structure.
)

# Checks a condition before running the following code.
if normal_view is not None:
    # Displays a subsection heading.
    st.subheader("Method A AC Results")
    # Displays a DataFrame as an interactive table.
    st.dataframe(
        # Supports the calculation, data processing, or display operation on this line.
        normal_view,
        # Assigns a value to a variable for later use.
        use_container_width=True,
        # Assigns a value to a variable for later use.
        hide_index=True,
    # Continues or closes the surrounding function call or data structure.
    )

    # Assigns a value to a variable for later use.
    normal_summary = household_summary(normal_view)
    # Starts a list of values used by the dashboard.
    normal_summary_columns = [
        # Provides a text label or message used by the dashboard.
        "House ID",
        # Provides a text label or message used by the dashboard.
        "Total AC Energy Demand (kWh)",
        # Provides a text label or message used by the dashboard.
        "Solar Allocated to ACs (kWh)",
        # Provides a text label or message used by the dashboard.
        "Grid Energy for ACs (kWh)",
        # Provides a text label or message used by the dashboard.
        "Estimated Total Grid Import (kWh)",
    # Continues or closes the surrounding function call or data structure.
    ]
    # Starts a list of values used by the dashboard.
    available = [
        # Supports the calculation, data processing, or display operation on this line.
        column for column in normal_summary_columns
        # Checks a condition before running the following code.
        if column in normal_summary.columns
    # Continues or closes the surrounding function call or data structure.
    ]

    # Checks a condition before running the following code.
    if len(available) > 1:
        # Displays a subsection heading.
        st.subheader("Method A Household Energy Summary")
        # Displays a DataFrame as an interactive table.
        st.dataframe(
            # Supports the calculation, data processing, or display operation on this line.
            normal_summary[available],
            # Assigns a value to a variable for later use.
            use_container_width=True,
            # Assigns a value to a variable for later use.
            hide_index=True,
        # Continues or closes the surrounding function call or data structure.
        )
# Runs this alternative branch when the preceding condition is false.
else:
    # Displays an informational message.
    st.info("Method A results are unavailable. Run normal.py.")


# ==========================================
# 10. METHOD B: SMART SOLAR AC SCHEDULING
# ==========================================

# Displays a main section heading.
st.header("4. Method B — Smart Solar AC Scheduling")

# Displays explanatory text on the dashboard.
st.write(
    # Provides a text label or message used by the dashboard.
    "The smart scheduler prioritises cooling requirements, uses available "
    # Provides a text label or message used by the dashboard.
    "solar surplus first, and uses TNB electricity when selected."
# Continues or closes the surrounding function call or data structure.
)

# Checks a condition before running the following code.
if smart_view is not None:
    # Displays a subsection heading.
    st.subheader("Method B AC Results")
    # Displays a DataFrame as an interactive table.
    st.dataframe(
        # Supports the calculation, data processing, or display operation on this line.
        smart_view,
        # Assigns a value to a variable for later use.
        use_container_width=True,
        # Assigns a value to a variable for later use.
        hide_index=True,
    # Continues or closes the surrounding function call or data structure.
    )

    # Assigns a value to a variable for later use.
    smart_summary = household_summary(smart_view)

    # Household-level totals are repeated on every AC row in smart_results.csv.
    # Sum those totals only after removing duplicate household rows.
    # Assigns a value to a variable for later use.
    smart_demand_total = sum_column(
        # Supports the calculation, data processing, or display operation on this line.
        smart_summary, "Total AC Energy Demand (kWh)"
    # Continues or closes the surrounding function call or data structure.
    )
    # Assigns a value to a variable for later use.
    smart_solar_total = sum_column(
        # Supports the calculation, data processing, or display operation on this line.
        smart_summary, "Total Solar Used by ACs (kWh)"
    # Continues or closes the surrounding function call or data structure.
    )
    # Assigns a value to a variable for later use.
    smart_tnb_total = sum_column(
        # Supports the calculation, data processing, or display operation on this line.
        smart_summary, "Total TNB Energy for ACs (kWh)"
    # Continues or closes the surrounding function call or data structure.
    )

    # If household totals are absent, calculate from individual AC rows.
    # Checks a condition before running the following code.
    if (
        # Checks or accesses the DataFrame's column names.
        "Total AC Energy Demand (kWh)" not in smart_summary.columns
        # Checks or accesses the DataFrame's column names.
        and "AC Energy Requirement (kWh)" in smart_view.columns
    # Begins a code block for the condition, loop, or context above.
    ):
        # Assigns a value to a variable for later use.
        smart_demand_total = sum_column(
            # Supports the calculation, data processing, or display operation on this line.
            smart_view, "AC Energy Requirement (kWh)"
        # Continues or closes the surrounding function call or data structure.
        )

    # Checks a condition before running the following code.
    if (
        # Checks or accesses the DataFrame's column names.
        "Total Solar Used by ACs (kWh)" not in smart_summary.columns
        # Checks or accesses the DataFrame's column names.
        and "Solar Energy Used (kWh)" in smart_view.columns
    # Begins a code block for the condition, loop, or context above.
    ):
        # Assigns a value to a variable for later use.
        smart_solar_total = sum_column(
            # Supports the calculation, data processing, or display operation on this line.
            smart_view, "Solar Energy Used (kWh)"
        # Continues or closes the surrounding function call or data structure.
        )

    # Checks a condition before running the following code.
    if (
        # Checks or accesses the DataFrame's column names.
        "Total TNB Energy for ACs (kWh)" not in smart_summary.columns
        # Checks or accesses the DataFrame's column names.
        and "TNB Energy Used (kWh)" in smart_view.columns
    # Begins a code block for the condition, loop, or context above.
    ):
        # Assigns a value to a variable for later use.
        smart_tnb_total = sum_column(
            # Supports the calculation, data processing, or display operation on this line.
            smart_view, "TNB Energy Used (kWh)"
        # Continues or closes the surrounding function call or data structure.
        )

    # Displays a subsection heading.
    st.subheader("Method B Energy Indicators")
    # Creates columns to arrange dashboard content horizontally.
    col1, col2, col3 = st.columns(3)

    # Displays a key performance indicator.
    col1.metric("AC Energy Demand", format_kwh(smart_demand_total))
    # Displays a key performance indicator.
    col2.metric("Solar Used by ACs", format_kwh(smart_solar_total))
    # Displays a key performance indicator.
    col3.metric("TNB Energy for ACs", format_kwh(smart_tnb_total))

    # Checks a condition before running the following code.
    if "AC Action" in smart_view.columns:
        # Displays a subsection heading.
        st.subheader("Smart AC Decisions")

        # Assigns a value to a variable for later use.
        action_summary = (
            # Groups records by the specified column or columns.
            smart_view.groupby("AC Action")
            # Supports the calculation, data processing, or display operation on this line.
            .size()
            # Resets the DataFrame index and creates regular columns.
            .reset_index(name="Number of ACs")
            # Assigns a value to a variable for later use.
            .rename(columns={"AC Action": "Action"})
        # Continues or closes the surrounding function call or data structure.
        )

        # Displays a DataFrame as an interactive table.
        st.dataframe(
            # Supports the calculation, data processing, or display operation on this line.
            action_summary,
            # Assigns a value to a variable for later use.
            use_container_width=True,
            # Assigns a value to a variable for later use.
            hide_index=True,
        # Continues or closes the surrounding function call or data structure.
        )
        # Displays a bar chart from the supplied data.
        st.bar_chart(action_summary.set_index("Action"))

    # Starts a list of values used by the dashboard.
    smart_summary_columns = [
        # Provides a text label or message used by the dashboard.
        "House ID",
        # Provides a text label or message used by the dashboard.
        "Total AC Energy Demand (kWh)",
        # Provides a text label or message used by the dashboard.
        "Total Solar Used by ACs (kWh)",
        # Provides a text label or message used by the dashboard.
        "Total TNB Energy for ACs (kWh)",
        # Provides a text label or message used by the dashboard.
        "Solar Remaining After AC (kWh)",
        # Provides a text label or message used by the dashboard.
        "Estimated Total Grid Import (kWh)",
    # Continues or closes the surrounding function call or data structure.
    ]
    # Starts a list of values used by the dashboard.
    available = [
        # Supports the calculation, data processing, or display operation on this line.
        column for column in smart_summary_columns
        # Checks a condition before running the following code.
        if column in smart_summary.columns
    # Continues or closes the surrounding function call or data structure.
    ]

    # Checks a condition before running the following code.
    if len(available) > 1:
        # Displays a subsection heading.
        st.subheader("Method B Household Energy Summary")
        # Displays a DataFrame as an interactive table.
        st.dataframe(
            # Supports the calculation, data processing, or display operation on this line.
            smart_summary[available],
            # Assigns a value to a variable for later use.
            use_container_width=True,
            # Assigns a value to a variable for later use.
            hide_index=True,
        # Continues or closes the surrounding function call or data structure.
        )

    # Starts a list of values used by the dashboard.
    temperature_columns = [
        # Provides a text label or message used by the dashboard.
        "House ID",
        # Provides a text label or message used by the dashboard.
        "AC ID",
        # Provides a text label or message used by the dashboard.
        "Room Temperature (°C)",
        # Provides a text label or message used by the dashboard.
        "Minimum Comfort Temperature (°C)",
        # Provides a text label or message used by the dashboard.
        "Maximum Comfort Temperature (°C)",
        # Provides a text label or message used by the dashboard.
        "Adjusted Maximum Comfort Temperature (°C)",
        # Provides a text label or message used by the dashboard.
        "Temperature Setting Increase (°C)",
        # Provides a text label or message used by the dashboard.
        "Original AC Energy (kWh)",
        # Provides a text label or message used by the dashboard.
        "AC Energy Requirement (kWh)",
        # Provides a text label or message used by the dashboard.
        "AC Action",
    # Continues or closes the surrounding function call or data structure.
    ]
    # Starts a list of values used by the dashboard.
    available_temperature_columns = [
        # Supports the calculation, data processing, or display operation on this line.
        column for column in temperature_columns
        # Checks a condition before running the following code.
        if column in smart_view.columns
    # Continues or closes the surrounding function call or data structure.
    ]

    # Checks a condition before running the following code.
    if available_temperature_columns:
        # Groups the following operations under this Streamlit layout or context.
        with st.expander("View AC Temperature and Energy Details"):
            # Displays a DataFrame as an interactive table.
            st.dataframe(
                # Supports the calculation, data processing, or display operation on this line.
                smart_view[available_temperature_columns],
                # Assigns a value to a variable for later use.
                use_container_width=True,
                # Assigns a value to a variable for later use.
                hide_index=True,
            # Continues or closes the surrounding function call or data structure.
            )
# Runs this alternative branch when the preceding condition is false.
else:
    # Displays an informational message.
    st.info("Method B results are unavailable. Run smart.py.")


# ==========================================
# 11. METHOD A VS METHOD B COMPARISON
# ==========================================

# Displays a main section heading.
st.header("5. Method A vs Method B Comparison")

# Checks a condition before running the following code.
if normal_view is not None and smart_view is not None:
    # Assigns a value to a variable for later use.
    normal_summary = household_summary(normal_view)
    # Assigns a value to a variable for later use.
    smart_summary = household_summary(smart_view)

    # Assigns a value to a variable for later use.
    normal_grid_col = first_existing_column(
        # Supports the calculation, data processing, or display operation on this line.
        normal_summary, ["Estimated Total Grid Import (kWh)"]
    # Continues or closes the surrounding function call or data structure.
    )
    # Assigns a value to a variable for later use.
    smart_grid_col = first_existing_column(
        # Supports the calculation, data processing, or display operation on this line.
        smart_summary, ["Estimated Total Grid Import (kWh)"]
    # Continues or closes the surrounding function call or data structure.
    )
    # Assigns a value to a variable for later use.
    normal_solar_col = first_existing_column(
        # Supports the calculation, data processing, or display operation on this line.
        normal_summary, ["Solar Allocated to ACs (kWh)"]
    # Continues or closes the surrounding function call or data structure.
    )
    # Assigns a value to a variable for later use.
    smart_solar_col = first_existing_column(
        # Supports the calculation, data processing, or display operation on this line.
        smart_summary, ["Total Solar Used by ACs (kWh)"]
    # Continues or closes the surrounding function call or data structure.
    )
    # Assigns a value to a variable for later use.
    normal_ac_grid_col = first_existing_column(
        # Supports the calculation, data processing, or display operation on this line.
        normal_summary, ["Grid Energy for ACs (kWh)"]
    # Continues or closes the surrounding function call or data structure.
    )
    # Assigns a value to a variable for later use.
    smart_ac_grid_col = first_existing_column(
        # Supports the calculation, data processing, or display operation on this line.
        smart_summary, ["Total TNB Energy for ACs (kWh)"]
    # Continues or closes the surrounding function call or data structure.
    )

    # Starts a list of values used by the dashboard.
    comparison_rows = []

    # Loops through each item in the collection.
    for house_id in houses:
        # Checks a condition before running the following code.
        if selected_house != "All Houses" and str(house_id) != str(selected_house):
            # Supports the calculation, data processing, or display operation on this line.
            continue

        # Assigns a value to a variable for later use.
        normal_house = normal_summary[
            # Supports the calculation, data processing, or display operation on this line.
            normal_summary["House ID"].astype(str) == str(house_id)
        # Continues or closes the surrounding function call or data structure.
        ]
        # Assigns a value to a variable for later use.
        smart_house = smart_summary[
            # Supports the calculation, data processing, or display operation on this line.
            smart_summary["House ID"].astype(str) == str(house_id)
        # Continues or closes the surrounding function call or data structure.
        ]

        # Checks a condition before running the following code.
        if normal_house.empty or smart_house.empty:
            # Supports the calculation, data processing, or display operation on this line.
            continue

        # Assigns a value to a variable for later use.
        normal_row = normal_house.iloc[0]
        # Assigns a value to a variable for later use.
        smart_row = smart_house.iloc[0]

        # Assigns a value to a variable for later use.
        normal_grid = (
            # Supports the calculation, data processing, or display operation on this line.
            numeric_value(normal_row, normal_grid_col)
            # Checks a condition before running the following code.
            if normal_grid_col else None
        # Continues or closes the surrounding function call or data structure.
        )
        # Assigns a value to a variable for later use.
        smart_grid = (
            # Supports the calculation, data processing, or display operation on this line.
            numeric_value(smart_row, smart_grid_col)
            # Checks a condition before running the following code.
            if smart_grid_col else None
        # Continues or closes the surrounding function call or data structure.
        )
        # Assigns a value to a variable for later use.
        normal_solar = (
            # Supports the calculation, data processing, or display operation on this line.
            numeric_value(normal_row, normal_solar_col)
            # Checks a condition before running the following code.
            if normal_solar_col else None
        # Continues or closes the surrounding function call or data structure.
        )
        # Assigns a value to a variable for later use.
        smart_solar = (
            # Supports the calculation, data processing, or display operation on this line.
            numeric_value(smart_row, smart_solar_col)
            # Checks a condition before running the following code.
            if smart_solar_col else None
        # Continues or closes the surrounding function call or data structure.
        )
        # Assigns a value to a variable for later use.
        normal_ac_grid = (
            # Supports the calculation, data processing, or display operation on this line.
            numeric_value(normal_row, normal_ac_grid_col)
            # Checks a condition before running the following code.
            if normal_ac_grid_col else None
        # Continues or closes the surrounding function call or data structure.
        )
        # Assigns a value to a variable for later use.
        smart_ac_grid = (
            # Supports the calculation, data processing, or display operation on this line.
            numeric_value(smart_row, smart_ac_grid_col)
            # Checks a condition before running the following code.
            if smart_ac_grid_col else None
        # Continues or closes the surrounding function call or data structure.
        )

        # Adds this item to the list.
        comparison_rows.append(
            # Continues or closes the surrounding function call or data structure.
            {
                # Provides a text label or message used by the dashboard.
                "House ID": house_id,
                # Provides a text label or message used by the dashboard.
                "Method A Solar Used by ACs (kWh)": normal_solar,
                # Provides a text label or message used by the dashboard.
                "Method B Solar Used by ACs (kWh)": smart_solar,
                # Provides a text label or message used by the dashboard.
                "Method A TNB for ACs (kWh)": normal_ac_grid,
                # Provides a text label or message used by the dashboard.
                "Method B TNB for ACs (kWh)": smart_ac_grid,
                # Provides a text label or message used by the dashboard.
                "Method A Total Grid Import (kWh)": normal_grid,
                # Provides a text label or message used by the dashboard.
                "Method B Total Grid Import (kWh)": smart_grid,
                # Provides a text label or message used by the dashboard.
                "Grid Import Difference (A - B, kWh)": (
                    # Supports the calculation, data processing, or display operation on this line.
                    normal_grid - smart_grid
                    # Checks a condition before running the following code.
                    if normal_grid is not None and smart_grid is not None
                    # Supports the calculation, data processing, or display operation on this line.
                    else None
                # Supports the calculation, data processing, or display operation on this line.
                ),
            # Supports the calculation, data processing, or display operation on this line.
            }
        # Continues or closes the surrounding function call or data structure.
        )

    # Checks a condition before running the following code.
    if comparison_rows:
        # Creates a pandas DataFrame.
        comparison_df = pd.DataFrame(comparison_rows)

        # Displays a subsection heading.
        st.subheader("Energy Comparison by Household")
        # Displays a DataFrame as an interactive table.
        st.dataframe(
            # Supports the calculation, data processing, or display operation on this line.
            comparison_df,
            # Assigns a value to a variable for later use.
            use_container_width=True,
            # Assigns a value to a variable for later use.
            hide_index=True,
        # Continues or closes the surrounding function call or data structure.
        )

        # Starts a list of values used by the dashboard.
        grid_columns = [
            # Provides a text label or message used by the dashboard.
            "Method A Total Grid Import (kWh)",
            # Provides a text label or message used by the dashboard.
            "Method B Total Grid Import (kWh)",
        # Continues or closes the surrounding function call or data structure.
        ]
        # Assigns a value to a variable for later use.
        valid_grid_df = comparison_df.dropna(subset=grid_columns)

        # Checks a condition before running the following code.
        if not valid_grid_df.empty:
            # Displays a subsection heading.
            st.subheader("Estimated Grid Import Comparison")
            # Displays a bar chart from the supplied data.
            st.bar_chart(valid_grid_df.set_index("House ID")[grid_columns])

            # Assigns a value to a variable for later use.
            total_normal_grid = valid_grid_df[
                # Provides a text label or message used by the dashboard.
                "Method A Total Grid Import (kWh)"
            # Calculates the total of the selected numeric values.
            ].sum()
            # Assigns a value to a variable for later use.
            total_smart_grid = valid_grid_df[
                # Provides a text label or message used by the dashboard.
                "Method B Total Grid Import (kWh)"
            # Calculates the total of the selected numeric values.
            ].sum()
            # Assigns a value to a variable for later use.
            grid_difference = total_normal_grid - total_smart_grid

            # Creates columns to arrange dashboard content horizontally.
            col1, col2, col3 = st.columns(3)
            # Displays a key performance indicator.
            col1.metric("Method A Grid Import", format_kwh(total_normal_grid))
            # Displays a key performance indicator.
            col2.metric("Method B Grid Import", format_kwh(total_smart_grid))
            # Displays a key performance indicator.
            col3.metric(
                # Provides a text label or message used by the dashboard.
                "Grid Import Difference (A - B)",
                # Supports the calculation, data processing, or display operation on this line.
                format_kwh(grid_difference),
            # Continues or closes the surrounding function call or data structure.
            )

            # Checks a condition before running the following code.
            if grid_difference > 0:
                # Displays a success message.
                st.success(
                    # Provides a text label or message used by the dashboard.
                    "Method B has lower estimated grid import "
                    # Provides a text label or message used by the dashboard.
                    "for the selected households."
                # Continues or closes the surrounding function call or data structure.
                )
            # Checks another condition if the previous condition was false.
            elif grid_difference < 0:
                # Displays a warning message.
                st.warning(
                    # Provides a text label or message used by the dashboard.
                    "Method B has higher estimated grid import "
                    # Provides a text label or message used by the dashboard.
                    "for the selected households."
                # Continues or closes the surrounding function call or data structure.
                )
            # Runs this alternative branch when the preceding condition is false.
            else:
                # Displays an informational message.
                st.info(
                    # Provides a text label or message used by the dashboard.
                    "Both methods have the same estimated grid import."
                # Continues or closes the surrounding function call or data structure.
                )

        # Displays a smaller explanatory caption.
        st.caption(
            # Provides a text label or message used by the dashboard.
            "Positive grid import difference means Method B uses less "
            # Provides a text label or message used by the dashboard.
            "estimated grid electricity. For a fair comparison, use "
            # Provides a text label or message used by the dashboard.
            "consistent household inputs, AC settings, and intervals."
        # Continues or closes the surrounding function call or data structure.
        )
    # Runs this alternative branch when the preceding condition is false.
    else:
        # Displays an informational message.
        st.info(
            # Provides a text label or message used by the dashboard.
            "No matching households were found in both methods, "
            # Provides a text label or message used by the dashboard.
            "or the result files do not contain matching House IDs."
        # Continues or closes the surrounding function call or data structure.
        )
# Runs this alternative branch when the preceding condition is false.
else:
    # Displays an informational message.
    st.info("Run both normal.py and smart.py before comparing results.")


# ==========================================
# 12. PERFORMANCE METRICS AND RECOMMENDATIONS
# ==========================================

# Displays a main section heading.
st.header("6. Performance Metrics and Recommendations")

# Checks a condition before running the following code.
if normal_view is not None and smart_view is not None:
    # Assigns a value to a variable for later use.
    normal_summary = household_summary(normal_view)
    # Assigns a value to a variable for later use.
    smart_summary = household_summary(smart_view)

    # Assigns a value to a variable for later use.
    normal_grid_col = "Estimated Total Grid Import (kWh)"
    # Assigns a value to a variable for later use.
    smart_grid_col = "Estimated Total Grid Import (kWh)"

    # Checks a condition before running the following code.
    if (
        # Checks or accesses the DataFrame's column names.
        normal_grid_col in normal_summary.columns
        # Checks or accesses the DataFrame's column names.
        and smart_grid_col in smart_summary.columns
    # Begins a code block for the condition, loop, or context above.
    ):
        # Assigns a value to a variable for later use.
        normal_grid = sum_column(normal_summary, normal_grid_col)
        # Assigns a value to a variable for later use.
        smart_grid = sum_column(smart_summary, smart_grid_col)

        # Assigns a value to a variable for later use.
        grid_reduction = normal_grid - smart_grid
        # Assigns a value to a variable for later use.
        reduction_percent = (
            # Builds a filesystem path.
            (grid_reduction / normal_grid) * 100
            # Checks a condition before running the following code.
            if normal_grid > 0
            # Supports the calculation, data processing, or display operation on this line.
            else 0.0
        # Continues or closes the surrounding function call or data structure.
        )

        # Creates columns to arrange dashboard content horizontally.
        col1, col2, col3 = st.columns(3)
        # Displays a key performance indicator.
        col1.metric("Method A Grid Import", format_kwh(normal_grid))
        # Displays a key performance indicator.
        col2.metric("Method B Grid Import", format_kwh(smart_grid))
        # Displays a key performance indicator.
        col3.metric(
            # Provides a text label or message used by the dashboard.
            "Grid Import Reduction",
            # Supports the calculation, data processing, or display operation on this line.
            f"{reduction_percent:.1f}%",
            # Assigns a value to a variable for later use.
            delta=format_kwh(grid_reduction),
        # Continues or closes the surrounding function call or data structure.
        )

        # Calculate solar surplus utilisation only if the required columns exist.
        # Checks a condition before running the following code.
        if (
            # Checks or accesses the DataFrame's column names.
            "Total Solar Used by ACs (kWh)" in smart_summary.columns
            # Supports the calculation, data processing, or display operation on this line.
            and energy_view is not None
            # Checks or accesses the DataFrame's column names.
            and "Surplus Solar (kWh)" in energy_view.columns
        # Begins a code block for the condition, loop, or context above.
        ):
            # Assigns a value to a variable for later use.
            available_surplus = sum_column(
                # Supports the calculation, data processing, or display operation on this line.
                energy_view, "Surplus Solar (kWh)"
            # Continues or closes the surrounding function call or data structure.
            )
            # Assigns a value to a variable for later use.
            solar_used = sum_column(
                # Supports the calculation, data processing, or display operation on this line.
                smart_summary, "Total Solar Used by ACs (kWh)"
            # Continues or closes the surrounding function call or data structure.
            )

            # Checks a condition before running the following code.
            if available_surplus > 0:
                # Builds a filesystem path.
                solar_utilisation = solar_used / available_surplus * 100
                # Displays a key performance indicator.
                st.metric(
                    # Provides a text label or message used by the dashboard.
                    "Solar Surplus Utilisation",
                    # Supports the calculation, data processing, or display operation on this line.
                    f"{solar_utilisation:.1f}%",
                # Continues or closes the surrounding function call or data structure.
                )

                # Checks a condition before running the following code.
                if solar_used > available_surplus:
                    # Displays a warning message.
                    st.warning(
                        # Provides a text label or message used by the dashboard.
                        "Recorded AC solar use exceeds available solar surplus. "
                        # Provides a text label or message used by the dashboard.
                        "Check the energy allocation logic and CSV totals."
                    # Continues or closes the surrounding function call or data structure.
                    )
            # Runs this alternative branch when the preceding condition is false.
            else:
                # Displays a key performance indicator.
                st.metric("Solar Surplus Utilisation", "N/A")
                # Displays a smaller explanatory caption.
                st.caption("No solar surplus was available in this selection.")

        # Displays a subsection heading.
        st.subheader("Recommendations")

        # Checks a condition before running the following code.
        if grid_reduction > 0:
            # Displays a success message.
            st.success(
                # Supports the calculation, data processing, or display operation on this line.
                f"Method B reduced estimated grid import by "
                # Supports the calculation, data processing, or display operation on this line.
                f"{format_kwh(grid_reduction)} ({reduction_percent:.1f}%) "
                # Provides a text label or message used by the dashboard.
                "compared with Method A."
            # Continues or closes the surrounding function call or data structure.
            )
        # Checks another condition if the previous condition was false.
        elif grid_reduction < 0:
            # Displays a warning message.
            st.warning(
                # Provides a text label or message used by the dashboard.
                "Method B used more estimated grid electricity than Method A. "
                # Provides a text label or message used by the dashboard.
                "Review AC settings, cooling priorities, and TNB usage."
            # Continues or closes the surrounding function call or data structure.
            )
        # Runs this alternative branch when the preceding condition is false.
        else:
            # Displays an informational message.
            st.info(
                # Provides a text label or message used by the dashboard.
                "Both methods have the same estimated grid import. "
                # Provides a text label or message used by the dashboard.
                "Review solar allocation and AC scheduling for possible improvements."
            # Continues or closes the surrounding function call or data structure.
            )

        # Checks a condition before running the following code.
        if energy_view is not None:
            # Checks a condition before running the following code.
            if "Surplus Solar (kWh)" in energy_view.columns:
                # Assigns a value to a variable for later use.
                surplus = sum_column(energy_view, "Surplus Solar (kWh)")
                # Checks a condition before running the following code.
                if surplus > 0:
                    # Displays explanatory text on the dashboard.
                    st.write(
                        # Provides a text label or message used by the dashboard.
                        "- Solar surplus is available. Consider scheduling "
                        # Provides a text label or message used by the dashboard.
                        "eligible AC operation during periods of higher solar generation."
                    # Continues or closes the surrounding function call or data structure.
                    )

            # Checks a condition before running the following code.
            if "Power Shortfall (kWh)" in energy_view.columns:
                # Assigns a value to a variable for later use.
                shortfall = sum_column(energy_view, "Power Shortfall (kWh)")
                # Checks a condition before running the following code.
                if shortfall > 0:
                    # Displays explanatory text on the dashboard.
                    st.write(
                        # Provides a text label or message used by the dashboard.
                        "- Some household demand exceeds solar generation. "
                        # Provides a text label or message used by the dashboard.
                        "Review demand timing and grid dependency."
                    # Continues or closes the surrounding function call or data structure.
                    )

        # Checks a condition before running the following code.
        if "AC Action" in smart_view.columns:
            # Assigns a value to a variable for later use.
            action_text = smart_view["AC Action"].fillna("").astype(str)
            # Assigns a value to a variable for later use.
            deferred_count = action_text.str.contains(
                # Provides a text label or message used by the dashboard.
                "DEFERRED|OFF",
                # Assigns a value to a variable for later use.
                case=False,
                # Assigns a value to a variable for later use.
                regex=True,
            # Calculates the total of the selected numeric values.
            ).sum()

            # Checks a condition before running the following code.
            if deferred_count > 0:
                # Displays explanatory text on the dashboard.
                st.write(
                    # Supports the calculation, data processing, or display operation on this line.
                    f"- {deferred_count} AC record(s) were deferred or switched off. "
                    # Provides a text label or message used by the dashboard.
                    "Check that cooling needs remain within users' comfort requirements."
                # Continues or closes the surrounding function call or data structure.
                )
    # Runs this alternative branch when the preceding condition is false.
    else:
        # Displays an informational message.
        st.info(
            # Provides a text label or message used by the dashboard.
            "Grid-import summary columns are missing. Regenerate both result files "
            # Provides a text label or message used by the dashboard.
            "using the latest normal.py and smart.py."
        # Continues or closes the surrounding function call or data structure.
        )
# Runs this alternative branch when the preceding condition is false.
else:
    # Displays an informational message.
    st.info(
        # Provides a text label or message used by the dashboard.
        "Generate both Method A and Method B results to calculate performance metrics."
    # Continues or closes the surrounding function call or data structure.
    )


# ==========================================
# 13. AC ACTION COMPARISON
# ==========================================

# Displays a main section heading.
st.header("7. AC Action Comparison")

# Starts a list of values used by the dashboard.
action_frames = []

# Checks a condition before running the following code.
if normal_view is not None and "AC Action" in normal_view.columns:
    # Creates a copy so changes do not modify the original DataFrame.
    temp = normal_view[["AC Action"]].copy()
    # Assigns a value to a variable for later use.
    temp["Method"] = "Method A"
    # Assigns a value to a variable for later use.
    temp = temp.rename(columns={"AC Action": "Action"})
    # Adds this item to the list.
    action_frames.append(temp)

# Checks a condition before running the following code.
if smart_view is not None and "AC Action" in smart_view.columns:
    # Creates a copy so changes do not modify the original DataFrame.
    temp = smart_view[["AC Action"]].copy()
    # Assigns a value to a variable for later use.
    temp["Method"] = "Method B"
    # Assigns a value to a variable for later use.
    temp = temp.rename(columns={"AC Action": "Action"})
    # Adds this item to the list.
    action_frames.append(temp)

# Checks a condition before running the following code.
if action_frames:
    # Combines multiple DataFrames into one.
    actions_df = pd.concat(action_frames, ignore_index=True)

    # Assigns a value to a variable for later use.
    action_summary = (
        # Groups records by the specified column or columns.
        actions_df.groupby(["Method", "Action"])
        # Supports the calculation, data processing, or display operation on this line.
        .size()
        # Resets the DataFrame index and creates regular columns.
        .reset_index(name="Number of ACs")
    # Continues or closes the surrounding function call or data structure.
    )

    # Displays a DataFrame as an interactive table.
    st.dataframe(
        # Supports the calculation, data processing, or display operation on this line.
        action_summary,
        # Assigns a value to a variable for later use.
        use_container_width=True,
        # Assigns a value to a variable for later use.
        hide_index=True,
    # Continues or closes the surrounding function call or data structure.
    )

    # Assigns a value to a variable for later use.
    action_chart = action_summary.pivot(
        # Assigns a value to a variable for later use.
        index="Action",
        # Assigns a value to a variable for later use.
        columns="Method",
        # Assigns a value to a variable for later use.
        values="Number of ACs",
    # Supports the calculation, data processing, or display operation on this line.
    ).fillna(0)

    # Displays a bar chart from the supplied data.
    st.bar_chart(action_chart)
# Runs this alternative branch when the preceding condition is false.
else:
    # Displays an informational message.
    st.info("No AC action results are available yet.")


# ==========================================
# 14. DOWNLOAD RESULTS
# ==========================================

# Displays a main section heading.
st.header("8. Download Results")

# Creates columns to arrange dashboard content horizontally.
download1, download2, download3 = st.columns(3)

# Groups the following operations under this Streamlit layout or context.
with download1:
    # Supports the calculation, data processing, or display operation on this line.
    display_download_button(
        # Provides a text label or message used by the dashboard.
        "Download Energy Results",
        # Supports the calculation, data processing, or display operation on this line.
        energy_view,
        # Provides a text label or message used by the dashboard.
        "energy_results_filtered.csv",
        # Provides a text label or message used by the dashboard.
        "download_energy",
    # Continues or closes the surrounding function call or data structure.
    )

# Groups the following operations under this Streamlit layout or context.
with download2:
    # Supports the calculation, data processing, or display operation on this line.
    display_download_button(
        # Provides a text label or message used by the dashboard.
        "Download Method A Results",
        # Supports the calculation, data processing, or display operation on this line.
        normal_view,
        # Provides a text label or message used by the dashboard.
        "normal_results_filtered.csv",
        # Provides a text label or message used by the dashboard.
        "download_normal",
    # Continues or closes the surrounding function call or data structure.
    )

# Groups the following operations under this Streamlit layout or context.
with download3:
    # Supports the calculation, data processing, or display operation on this line.
    display_download_button(
        # Provides a text label or message used by the dashboard.
        "Download Method B Results",
        # Supports the calculation, data processing, or display operation on this line.
        smart_view,
        # Provides a text label or message used by the dashboard.
        "smart_results_filtered.csv",
        # Provides a text label or message used by the dashboard.
        "download_smart",
    # Continues or closes the surrounding function call or data structure.
    )


# ==========================================
# 15. SAVE EXPERIMENT SNAPSHOT
# ==========================================

# Displays a main section heading.
st.header("9. Save Experiment")

# Displays explanatory text on the dashboard.
st.write(
    # Provides a text label or message used by the dashboard.
    "Save timestamped copies of the current input and result CSV files "
    # Provides a text label or message used by the dashboard.
    "so you can review and reproduce experiments later."
# Continues or closes the surrounding function call or data structure.
)

# Checks a condition before running the following code.
if st.button("Save Current Experiment"):
    # Gets the current date and time for a unique experiment name.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Assigns a value to a variable for later use.
    experiment_folder = (
        # Builds a filesystem path.
        BASE_DIR / "experiments" / f"experiment_{timestamp}"
    # Continues or closes the surrounding function call or data structure.
    )

    # Creates the experiment folder if it does not already exist.
    experiment_folder.mkdir(parents=True, exist_ok=True)

    # Starts a list of values used by the dashboard.
    files_to_save = [
        # Provides a text label or message used by the dashboard.
        "energy_data.csv",
        # Provides a text label or message used by the dashboard.
        "energy_results.csv",
        # Provides a text label or message used by the dashboard.
        "normal_results.csv",
        # Provides a text label or message used by the dashboard.
        "smart_results.csv",
    # Continues or closes the surrounding function call or data structure.
    ]

    # Starts a list of values used by the dashboard.
    saved_files = []

    # Loops through each item in the collection.
    for filename in files_to_save:
        # Builds a filesystem path.
        source_file = BASE_DIR / filename

        # Checks a condition before running the following code.
        if source_file.exists():
            # Copies a file into the experiment snapshot folder.
            shutil.copy2(
                # Supports the calculation, data processing, or display operation on this line.
                source_file,
                # Builds a filesystem path.
                experiment_folder / filename,
            # Continues or closes the surrounding function call or data structure.
            )
            # Adds this item to the list.
            saved_files.append(filename)

    # Checks a condition before running the following code.
    if saved_files:
        # Displays a success message.
        st.success(f"Experiment saved in: {experiment_folder}")
        # Displays explanatory text on the dashboard.
        st.write("Files saved:")
        # Loops through each item in the collection.
        for filename in saved_files:
            # Displays explanatory text on the dashboard.
            st.write(f"- {filename}")
    # Runs this alternative branch when the preceding condition is false.
    else:
        # Displays a warning message.
        st.warning("No CSV files were available to save.")


# ==========================================
# 16. FOOTER
# ==========================================

# Displays a horizontal divider.
st.divider()

# Displays a smaller explanatory caption.
st.caption(
    # Provides a text label or message used by the dashboard.
    "Smart Township Energy Optimisation System | Simulation only. "
    # Provides a text label or message used by the dashboard.
    "Results are based on CSV data and user-defined assumptions, "
    # Provides a text label or message used by the dashboard.
    "not live energy meters or physical AC control."
# Continues or closes the surrounding function call or data structure.
)
