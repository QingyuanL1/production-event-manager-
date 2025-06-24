# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production scheduling system (生产排班系统) designed to automatically handle and adjust production plans based on production events. The system operates as a local application that parses local Excel data tables to implement functionality.

## Architecture

### Core Components

- **main.py**: Entry point that initializes the Tkinter GUI application
- **data_loader.py**: Contains the main `ProductionSchedulingApp` class that handles:
  - GUI layout with three-panel design (control panel, tabbed interface, log panel)
  - Excel data loading and parsing from the "数据表" directory
  - Data preview with specialized handling for daily plan files
  - Event management interface (not yet implemented)
  - System logging

### Data Structure

The system processes four main types of Excel files located in the "数据表" directory:
- **daily plan.xlsx**: Production planning data (requires special header parsing)
- **FG EOH.xlsx**: Finished goods inventory tracking
- **Learning Curve.xlsx**: Production line efficiency recovery curves after changeovers
- **capacity .xlsx**: Production line capacity data

### GUI Architecture

- **Three-panel layout**: Control panel (left), main tabs (right), system log (bottom)
- **Main tabs**: Data Preview, Event Management, Results Analysis
- **Data preview**: Handles complex Excel structures with merged cells and multi-row headers
- **Event management**: Form-based interface for production events (产量调整, 产品转换, etc.)

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Dependencies
- pandas>=1.3.0 (Excel data processing)
- numpy>=1.20.0 (numerical operations)
- openpyxl>=3.0.7 (Excel file handling)
- tkinter (GUI - included with Python)

## Key Implementation Details

### Excel Data Handling
- The system uses pandas.ExcelFile for loading workbooks
- Special handling for "daily plan.xlsx" with multi-row headers (first 4 rows)
- Forward filling for merged cells to handle Excel formatting
- Automatic data type detection and date formatting

### GUI Features
- Treeview widgets with zebra striping for data display
- Scrollable data views with both horizontal and vertical scrollbars
- Real-time logging with timestamps
- Responsive layout using PanedWindow widgets

### Current Status
- Phase 1: Data loading and preview functionality (implemented)
- Phases 2-3: Event processing logic and advanced scheduling (planned but not implemented)
- Many buttons show "此功能尚未实现" (functionality not yet implemented)

## Development Notes

- Code uses Chinese language for UI elements and log messages
- The system is designed to handle irregular Excel formatting common in manual data entry
- Event processing logic will implement three main modules: 加线模块 (add line), 减线模块 (reduce line), and 其他辅助模块 (auxiliary modules)
- Future implementation should maintain separation between main program and component modules