# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Production Scheduling System (生产排班系统) built in Python with Tkinter GUI. The system processes and manages production events by automatically adjusting production plans based on various data sources like daily plans, inventory, capacity, and learning curves.

## Core Commands

### Running the Application
```bash
python main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Data Exploration (for development)
```bash
python explore_data.py
```

## Dependencies
- pandas==2.2.3
- openpyxl==3.1.5  
- numpy==1.26.0
- tkinter (built-in with Python)

## Architecture

### Main Components

1. **main.py** - Main application entry point
   - Contains `ProductionSchedulingSystem` class that manages the entire GUI application
   - Implements tabbed interface with Control Panel, Data Preview, Event Management, and Result Analysis
   - Handles UI threading for data loading to prevent freezing
   - Manages system logging and status updates
   - Integrates event management functionality

2. **data_loader.py** - Data loading and processing module
   - Contains `DataLoader` class for loading Excel files from `数据表/` directory
   - Handles four main data types: HSA Daily Plan, HSA FG EOH, HSA Capacity, Learning Curve
   - Implements special processing for multi-sheet Excel files
   - Performs selective forward-filling for specific columns (not global)
   - Cleans column names, especially datetime formats

3. **event_manager.py** - Event management core logic
   - Contains `EventManager` class for handling production events
   - Supports five event types: LCA产量损失, 物料情况, SBR信息, PM状态, Drive loading计划
   - Implements multi-level cascading data validation
   - Provides data source integration with Daily Plan and other production data
   - Handles event persistence and export functionality

4. **event_ui.py** - Event management user interface
   - Contains `EventFormUI` class for dynamic multi-level form generation
   - Supports up to 7-level cascading dropdown/input forms
   - Implements branch logic for complex event types (SBR, Drive loading)
   - Provides real-time validation and data consistency checks
   - Includes event list management and export features

5. **explore_data.py** - Development utility for examining Excel file structure

### Data Sources

The system works with Excel files in the `数据表/` directory:
- `daily plan.xlsx` - Production schedules with multi-row headers
- `FG EOH.xlsx` - Finished goods inventory data  
- `capacity .xlsx` - Production line capacity information
- `Learning Curve.xlsx` - Efficiency recovery curves after line changes

### Key Design Patterns

1. **Special Header Handling**: Daily Plan files have complex 3-row headers that are preserved separately from data rows
2. **Sheet-Aware Loading**: Multi-sheet Excel files are loaded with awareness of which sheet is being accessed
3. **Selective Data Processing**: Only specific columns get forward-filled (Lines, Product, etc.) rather than global forward-filling
4. **Threading**: Data loading operations use background threads to keep UI responsive
5. **Column Name Cleaning**: Automatic handling of datetime column formats and cleanup

### UI Structure

- **Control Panel**: Data loading buttons and system controls
- **Data Preview**: Dynamic table display with sheet selection
- **Event Management**: Placeholder for future event handling features
- **Result Analysis**: Placeholder for future analysis features
- **System Log**: Real-time logging of operations

### Data Processing Notes

- Daily Plan requires special 3-row header extraction and Line column forward-filling
- Capacity data only forward-fills Lines and Product columns
- Learning Curve only forward-fills Product1, Config, and Head_Qty columns
- Column names with datetime formats are automatically cleaned
- Each data type can have multiple sheets with different processing rules

### Current Implementation Status

- ✅ Data loading and preview functionality
- ✅ Event management system with multi-level cascading forms
- ✅ Five event types with full 7-level input support
- ✅ Data validation and logical consistency checks
- ✅ Event export functionality
- ❌ Result analysis (placeholder)
- ❌ Event processing algorithms
- ❌ Production plan adjustment logic

## Development Guidelines

When extending this system:
1. Follow the existing pattern of separate data processing logic in `DataLoader`
2. Use threading for any operations that might take time
3. Maintain the sheet-aware data loading pattern for multi-sheet files
4. Preserve the selective column processing approach (avoid global operations)
5. Update the status display and logging for new features