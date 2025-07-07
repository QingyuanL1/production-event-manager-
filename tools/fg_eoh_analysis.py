#!/usr/bin/env python3
"""
FG EOH.xlsx Analysis Script

This script analyzes the FG EOH.xlsx file structure and provides functions
to calculate G values for DOS calculation: (G+F-H)/I

File Structure:
- Product: Product name (e.g., EvansBP, CIMARRONBP)
- Head_Qty: Group identifier (e.g., 16, 12, 3)
- P/N: Part Number (e.g., 200723400)
- WHFH: Warehouse FH quantity
- WHFP: Warehouse FP quantity
- WHFR: Warehouse FR quantity
- TTL QTY: Total quantity (WHFH + WHFP + WHFR)

Key Insight: Head_Qty represents a group structure where all PNs with the same
Product and Head_Qty belong to the same group. The G value is the sum of all
TTL QTY values within that group.
"""

import pandas as pd
import numpy as np

def load_fg_eoh_data(file_path):
    """Load FG EOH.xlsx file and return DataFrame"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        print(f"Error loading file: {e}")
        return None

def get_g_value_for_pn(df, part_number):
    """
    Get G value (上一个班的合计EOH) for a given Part Number
    
    Args:
        df: DataFrame containing FG EOH data
        part_number: Part Number to look up
        
    Returns:
        tuple: (g_value, details_dict) or (None, error_message)
    """
    # Find the row with the given part number
    pn_row = df[df['P/N'] == part_number]
    
    if len(pn_row) == 0:
        return None, f'Part Number {part_number} not found'
    
    # Get the Product and Head_Qty for this PN
    product = pn_row.iloc[0]['Product']
    head_qty = pn_row.iloc[0]['Head_Qty']
    
    # Get all rows in the same Head_Qty group
    group_rows = df[(df['Product'] == product) & (df['Head_Qty'] == head_qty)]
    
    # Calculate G (sum of TTL QTY for the entire group)
    g_value = group_rows['TTL  QTY'].sum()
    
    return g_value, {
        'product': product,
        'head_qty': head_qty,
        'group_size': len(group_rows),
        'group_pns': group_rows['P/N'].tolist(),
        'group_details': group_rows[['P/N', 'WHFH', 'WHFP', 'WHFR', 'TTL  QTY']].to_dict('records')
    }

def analyze_head_qty_groups(df):
    """Analyze all Head_Qty groups in the data"""
    print("=== HEAD_QTY GROUPS ANALYSIS ===")
    
    # Group by Product and Head_Qty
    grouped = df.groupby(['Product', 'Head_Qty'])
    
    for (product, head_qty), group in grouped:
        total_ttl_qty = group['TTL  QTY'].sum()
        print(f"\n{product} - Head_Qty {head_qty}:")
        print(f"  PNs in group: {len(group)}")
        print(f"  Total TTL QTY (G value): {total_ttl_qty}")
        print(f"  Part Numbers: {group['P/N'].tolist()}")

def main():
    """Main function to demonstrate usage"""
    # Load data
    file_path = '../data/FG EOH.xlsx'
    df = load_fg_eoh_data(file_path)
    
    if df is None:
        return
    
    print("=== FG EOH.xlsx STRUCTURE ANALYSIS ===")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Unique Products: {df['Product'].nunique()}")
    print(f"Unique Head_Qty values: {sorted(df['Head_Qty'].dropna().unique())}")
    
    # Example: Get G value for specific PNs
    test_pns = [200723400, 207623300, 205516900]
    
    print("\n=== G VALUE CALCULATIONS ===")
    for pn in test_pns:
        g_value, details = get_g_value_for_pn(df, pn)
        if g_value is not None:
            print(f"\nPN {pn}:")
            print(f"  G Value: {g_value}")
            print(f"  Product: {details['product']}")
            print(f"  Head_Qty: {details['head_qty']}")
            print(f"  Group size: {details['group_size']} PNs")
        else:
            print(f"\nPN {pn}: {details}")
    
    # Show detailed group analysis
    print("\n")
    analyze_head_qty_groups(df)
    
    print("\n=== USAGE FOR DOS CALCULATION ===")
    print("To calculate DOS: (G+F-H)/I")
    print("1. G = get_g_value_for_pn(df, part_number)[0]")
    print("2. F = Production forecast value")
    print("3. H = Capacity loss value")
    print("4. I = This shift's forecast production")
    print("5. DOS = (G + F - H) / I")

if __name__ == "__main__":
    main()