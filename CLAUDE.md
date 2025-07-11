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
pip install -r config/requirements.txt
```

### Data Exploration (for development)
```bash
python src/utils/explore_data.py
```

### Project Structure
```
tableEOO/
├── main.py                    # Main application entry point
├── config/
│   └── requirements.txt       # Python dependencies
├── src/                       # Source code directory
│   ├── core/                  # Core business logic modules
│   │   ├── data_loader.py     # Excel data loading and processing
│   │   ├── event_manager.py   # Event management logic
│   │   ├── event_processor.py # Event processing algorithms
│   │   ├── lca_capacity_loss.py # LCA capacity loss processing
│   │   └── database_manager.py # SQLite database operations
│   ├── ui/                    # User interface modules
│   │   ├── main_ui.py         # Main application GUI
│   │   └── event_ui.py        # Event management forms
│   └── utils/                 # Utility modules
│       └── explore_data.py    # Data exploration tool
├── data/                      # Data files directory
│   ├── daily plan.xlsx        # Production schedules
│   ├── FG EOH.xlsx           # Finished goods inventory
│   ├── capacity .xlsx        # Production line capacity
│   ├── Learning Curve.xlsx   # Line change efficiency curves
│   └── events.db             # SQLite database for events
└── docs/                     # Documentation (Chinese)
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

2. **data_loader.py** - Data loading and processing module (src/core/)
   - Contains `DataLoader` class for loading Excel files from `data/` directory
   - Handles four main data types: HSA Daily Plan, HSA FG EOH, HSA Capacity, Learning Curve
   - Implements special processing for multi-sheet Excel files
   - Performs selective forward-filling for specific columns (not global)
   - Cleans column names, especially datetime formats

3. **event_manager.py** - Event management core logic (src/core/)
   - Contains `EventManager` class for handling production events
   - Supports five event types: LCA产量损失, 物料情况, SBR信息, PM状态, Drive loading计划
   - Implements multi-level cascading data validation
   - Provides data source integration with Daily Plan and other production data
   - Handles event persistence and export functionality

4. **event_ui.py** - Event management user interface (src/ui/)
   - Contains `EventFormUI` class for dynamic multi-level form generation
   - Supports up to 7-level cascading dropdown/input forms
   - Implements branch logic for complex event types (SBR, Drive loading)
   - Provides real-time validation and data consistency checks
   - Includes event list management and export features

5. **event_processor.py** - Core business logic for processing production events (src/core/)
   - Contains `EventProcessor` class that implements the actual event processing algorithms
   - Handles five event types: LCA产能损失, 物料情况, SBR信息, PM状态, Drive loading计划
   - Implements specific sub-processing for Drive Loading events (date advance/delay, quantity changes, PN changes)
   - Provides result export functionality
   - Integrates with data_loader for accessing production data

6. **lca_capacity_loss.py** - LCA capacity loss processing module (src/core/)
   - Contains `LCACapacityLossProcessor` class for handling LCA capacity loss events
   - Implements DOS (Daily Output Shortage) calculation with E, H, I values
   - Checks if cumulative losses exceed thresholds across shifts
   - Core business logic for production capacity loss compensation
   - Provides detailed logging and result tracking for LCA processing decisions

7. **database_manager.py** - Database management for event persistence (src/core/)
   - SQLite database integration for storing events and processing results
   - Event CRUD operations with proper data validation
   - Export functionality for event data to Excel format
   - Database statistics and maintenance operations

8. **main_ui.py** - Main GUI interface (src/ui/)
   - Contains `ProductionSchedulingSystem` class for the main application window
   - Implements tabbed interface with Control Panel, Data Preview, Event Management, Result Analysis
   - Manages threading for responsive UI during data operations
   - Integrates all system components into unified interface

9. **explore_data.py** - Development utility for examining Excel file structure (src/utils/)

### Data Sources

The system works with Excel files in the `data/` directory:
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
6. **Event-Driven Processing**: Events trigger automatic processing workflows (e.g., LCA events auto-execute capacity loss analysis)
7. **Database Persistence**: All events and processing results are stored in SQLite database for tracking and analysis
8. **Cascading Validation**: Multi-level data validation ensures consistency across event data and production plans
9. **Smart Cascading Selection**: GUI form fields dynamically update based on user selections, fetching real data from Daily Plan
10. **Context-Aware Data Sources**: Data options change based on previous selections (date → shifts → production lines → products)
11. **Intelligent Field Validation**: Only clears dependent fields when selections become invalid, preserving user choices

### UI Structure

- **Control Panel**: Data loading buttons and system controls
- **Data Preview**: Dynamic table display with sheet selection
- **Event Management**: Fully functional event handling with five event types
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
- ✅ Event processing framework with EventProcessor class
- ✅ **LCA capacity loss processing logic (完整实现，简化版本)**
- ✅ **DOS calculation and threshold management (DOS计算和阈值管理)**
- ✅ **Compensation production calculation (补偿产量计算)**
- ✅ **DOS acceptance decision flow (DOS损失接受性决策流程)**
- ✅ Database integration for event storage (SQLite)
- ✅ Automatic LCA processing on event creation
- ✅ Multi-shift loss tracking and validation
- ✅ **GUI cascading selection system (智能级联选择)**
- ✅ **Dynamic data source integration (动态数据源集成)**
- ✅ **Production line filtering (F-series only)**
- ✅ **Simplified logging output (简化日志输出)**
- ⚠️ Other event type processing algorithms (framework complete, business logic partially implemented)
- ❌ Result analysis (placeholder)
- ❌ Production plan adjustment logic
- ❌ Capacity calculation and optimization algorithms

## Development Guidelines

When extending this system:
1. Follow the existing pattern of separate data processing logic in `DataLoader`
2. Use threading for any operations that might take time
3. Maintain the sheet-aware data loading pattern for multi-sheet files
4. Preserve the selective column processing approach (avoid global operations)
5. Update the status display and logging for new features
6. New event types should follow the existing cascading form pattern in `EventManager`
7. All event processing should use the established pattern: create processor class, implement validation, add database persistence
8. Use the existing logger adapters for consistent logging across modules
9. Test new event types thoroughly with real data from the `data/` directory
10. When adding new cascading form fields, follow the pattern in EventManager.get_data_source_options()
11. Always implement both static fallback data and dynamic context-aware data sources
12. Use regex filtering for production line validation to maintain F-series only display

## Recent Major Updates (Level 3 Priority for New Developers)

### LCA DOS Decision Flow Implementation (July 2025)
- **Problem Solved**: Implemented complete DOS (Days of Supply) calculation and decision workflow for LCA capacity loss events
- **Solution**: Added DOS threshold management, acceptance decision logic, and compensation calculation
- **Key Files Modified**: `src/core/lca_capacity_loss.py`, `src/core/database_manager.py`, `src/ui/main_ui.py`
- **Core Features**:
  - DOS calculation formula: (G+F-H)/I
  - Configurable DOS thresholds with database storage (default 0.5 days)
  - Compensation production calculation: F' = J*I + H - G
  - Decision outcomes: "损失已用DOS覆盖" vs "新DOS预计降为X.XX天"
- **Logging**: Simplified to show only essential calculations and indicators (no suggestions/recommendations)

### GUI Cascading Selection System (December 2024)
- **Problem Solved**: Event forms were using static dropdown options instead of dynamic data from Daily Plan
- **Solution**: Implemented smart cascading selection with context-aware data sources
- **Key Files Modified**: `src/core/event_manager.py`, `src/ui/event_ui.py`
- **Behavior**: Date selection → updates available shifts → updates production lines → updates product PNs
- **Technical Details**: Uses three-level header parsing from Excel, regex filtering for F-series lines only

### Production Line Filtering Enhancement
- **Requirement**: Only show actual production lines (F16, F25, F29, etc.), not system entries
- **Implementation**: Regex pattern `^F\d+$` filters production lines in both backend and GUI
- **Impact**: Cleaner UI, prevents selection of invalid production lines like "Forecast", "LCA", "SBR"

## Development Notes

### Testing
- No formal test framework is currently configured
- Manual testing is done through the main application
- Data exploration can be performed using `python src/utils/explore_data.py`

### Code Quality
- No linting or code quality tools are currently configured
- Consider adding flake8, black, or similar tools for larger development teams

### Debugging
- System uses Python's logging module with real-time display in GUI
- SQLite database (`data/events.db`) stores all events for debugging and analysis
- Use the explore_data.py utility to examine Excel file structures during development

## Important Files and Directories

- `data/events.db` - SQLite database storing all events and processing results
- `data/daily plan.xlsx` - Primary production schedule data source  
- `tools/` - Additional analysis tools (FG EOH analysis)
- `docs/` - Contains project documentation and requirements in Chinese
- `log.txt` - Application log file