import pandas as pd
import os

# Directory containing the Excel files
data_dir = "数据表"

# List of Excel files to explore
files = [
    "daily plan.xlsx",
    "FG EOH.xlsx",
    "capacity .xlsx",
    "Learning Curve.xlsx"
]

# Function to print basic information about the Excel file
def explore_excel(file_path):
    print(f"\n{'='*50}")
    print(f"Exploring: {file_path}")
    print(f"{'='*50}")
    
    # Get sheet names
    xlsx = pd.ExcelFile(file_path)
    sheets = xlsx.sheet_names
    print(f"Sheet names: {sheets}")
    
    # For each sheet, print basic information
    for sheet in sheets:
        print(f"\nSheet: {sheet}")
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            print(f"Shape: {df.shape}")
            print(f"Columns: {df.columns.tolist()}")
            print("First few rows:")
            print(df.head(3))
        except Exception as e:
            print(f"Error reading sheet {sheet}: {e}")

# Explore each Excel file
for file in files:
    file_path = os.path.join(data_dir, file)
    explore_excel(file_path) 