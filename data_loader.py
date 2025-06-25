import pandas as pd
import os
import re
from typing import Dict, List, Any, Tuple, Optional

class DataLoader:
    """
    Class for loading and processing Excel data files for the production scheduling system.
    """
    
    def __init__(self, data_dir: str = "数据表"):
        """
        Initialize the DataLoader with the directory containing data files.
        
        Args:
            data_dir: Directory containing the Excel data files
        """
        self.data_dir = data_dir
        self.data: Dict[str, pd.DataFrame] = {}
        self.file_paths = {
            "HSA Daily Plan": os.path.join(data_dir, "daily plan.xlsx"),
            "HSA FG EOH": os.path.join(data_dir, "FG EOH.xlsx"),
            "HSA Capacity": os.path.join(data_dir, "capacity .xlsx"),
            "Learning Curve": os.path.join(data_dir, "Learning Curve.xlsx")
        }
        
    def clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清理DataFrame的列名，特别是处理时间格式的列名
        统一将带有时间部分的列名格式化为纯日期格式 "YYYY-MM-DD"
        
        Args:
            df: 要清理列名的DataFrame
            
        Returns:
            清理后的DataFrame
        """
        import datetime
        
        new_columns = []
        for col in df.columns:
            # 处理datetime对象
            if isinstance(col, datetime.datetime):
                # 格式化为 YYYY-MM-DD
                new_columns.append(col.strftime('%Y-%m-%d'))
            # 处理字符串格式的日期时间
            elif isinstance(col, str):
                # 匹配各种时间格式：
                # '2025-03-02 00:00:00.1', '2025-03-02 00:00:00', '2025-03-02T00:00:00' 等
                if re.match(r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}', col):
                    date_part = col.split(' ')[0].split('T')[0]  # 提取日期部分
                    new_columns.append(date_part)
                else:
                    new_columns.append(col)
            else:
                new_columns.append(col)
        
        # 创建新的DataFrame使用清理后的列名
        df.columns = new_columns
        return df
        
    def load_data(self, data_type: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Load data from the specified Excel file.
        
        Args:
            data_type: Type of data to load (must be a key in self.file_paths)
            
        Returns:
            Tuple containing:
                - Boolean indicating success/failure
                - Message describing the result
                - DataFrame if successful, None otherwise
        """
        if data_type not in self.file_paths:
            return False, f"Unknown data type: {data_type}", None
            
        file_path = self.file_paths[data_type]
        
        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}", None
            
        try:
            # Handle different data types with their specific loading logic
            if data_type == "HSA Daily Plan":
                # Daily Plan需要特殊处理，因为表头有多行
                df = pd.read_excel(file_path, sheet_name=0)
                
                # 清理列名中的时间部分
                df = self.clean_column_names(df)
                
                # 清理数据 - 从第4行开始是实际数据（前3行是日期、班次和时段）
                # 前3行保留为表头，但不参与前向填充
                headers = df.iloc[:3].copy()
                data_rows = df.iloc[3:].copy()
                
                # 提取"Line", "Build Type", "Part Number"列，这些列需要前向填充
                id_columns = data_rows.iloc[:, :3].copy()
                # 使用ffill来填充Line列的空值（这样可以让LCA等值填充到后面的行）
                id_columns['Line'] = id_columns['Line'].ffill()
                
                # 数值数据部分不应该有"Day"和"Night"，保持原样
                value_columns = data_rows.iloc[:, 3:].copy()
                
                # 重新组合数据
                processed_data = pd.concat([id_columns, value_columns], axis=1)
                
                # 保存处理后的数据
                self.data[data_type] = processed_data
                
                # 同时保存表头信息，以便在UI中显示
                self.data[f"{data_type}_headers"] = headers
                
                return True, f"Successfully loaded {data_type}", processed_data
                
            elif data_type == "HSA FG EOH":
                df = pd.read_excel(file_path, sheet_name="HSA EOH")
                self.data[data_type] = df
                return True, f"Successfully loaded {data_type}", df
                
            elif data_type == "HSA Capacity":
                # Load the LCA sheet which appears to be the main capacity data
                df = pd.read_excel(file_path, sheet_name="LCA")
                
                # 特殊处理capacity表 - 只在特定列应用前向填充
                # 通常只有Lines和Product列需要前向填充
                columns_to_fill = ['Lines', 'Product']
                for col in columns_to_fill:
                    if col in df.columns:
                        df[col] = df[col].ffill()
                
                # 保存原始数据（不进行全局前向填充）
                self.data[data_type] = df
                
                # 加载其他sheet以供后续使用
                manual_df = pd.read_excel(file_path, sheet_name="Manual")
                special_df = pd.read_excel(file_path, sheet_name="Special HSA PN")
                min_pkg_df = pd.read_excel(file_path, sheet_name="Minimum packaging")
                
                self.data[f"{data_type}_Manual"] = manual_df
                self.data[f"{data_type}_Special"] = special_df
                self.data[f"{data_type}_MinPkg"] = min_pkg_df
                
                return True, f"Successfully loaded {data_type}", df
                
            elif data_type == "Learning Curve":
                # Load the conversion learning curve data
                df = pd.read_excel(file_path, sheet_name="Learning curve for conversion")
                
                # 特殊处理Learning Curve表 - 只在特定列应用前向填充
                # 通常只有Product列需要前向填充
                columns_to_fill = ['Product1', 'Config', 'Head_Qty']
                for col in columns_to_fill:
                    if col in df.columns:
                        df[col] = df[col].ffill()
                
                self.data[data_type] = df
                
                # 加载其他sheet以供后续使用
                other_df = pd.read_excel(file_path, sheet_name="Learning curve (2)")
                shutdown_df = pd.read_excel(file_path, sheet_name="Learning curve for shutdown")
                
                self.data[f"{data_type}_Other"] = other_df
                self.data[f"{data_type}_Shutdown"] = shutdown_df
                
                return True, f"Successfully loaded {data_type}", df
                
        except Exception as e:
            return False, f"Error loading {data_type}: {str(e)}", None
            
        return False, "Unknown error occurred", None
    
    def get_sheet_names(self, data_type: str) -> List[str]:
        """
        获取指定数据类型的所有可用sheet名称
        
        Args:
            data_type: 数据类型
            
        Returns:
            sheet名称列表
        """
        if data_type not in self.file_paths:
            return []
            
        file_path = self.file_paths[data_type]
        if not os.path.exists(file_path):
            return []
            
        try:
            # 动态获取Excel文件的所有sheet名称
            xlsx = pd.ExcelFile(file_path)
            return xlsx.sheet_names
        except Exception as e:
            print(f"Error getting sheet names for {data_type}: {e}")
            # 如果获取失败，使用备用的硬编码名称
            if data_type == "HSA Daily Plan":
                return ["Sheet1", "Sheet1 (2)"]
            elif data_type == "HSA FG EOH":
                return ["HSA EOH"]
            elif data_type == "HSA Capacity":
                return ["LCA", "Manual", "Special HSA PN", "Minimum packaging"]
            elif data_type == "Learning Curve":
                return ["Learning curve (2)", "Learning curve for conversion", "Learning curve for shutdown"]
            return []
        
    def get_data(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        Get the loaded data for the specified type.
        
        Args:
            data_type: Type of data to retrieve
            
        Returns:
            DataFrame if data is loaded, None otherwise
        """
        return self.data.get(data_type)
    
    def get_data_for_sheet(self, data_type: str, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        根据数据类型和sheet名称获取相应的数据
        
        Args:
            data_type: 数据类型
            sheet_name: sheet名称
        
        Returns:
            DataFrame if data is loaded, None otherwise
        """
        if data_type == "HSA Daily Plan":
            # 为每个sheet生成唯一的存储键
            sheet_key = f"{data_type}_{sheet_name.replace(' ', '_').replace('(', '').replace(')', '')}"
            
            # 如果是第一个sheet且已经加载过，直接返回
            if sheet_name == "Sheet1" and data_type in self.data:
                return self.get_data(data_type)
            
            # 如果这个sheet的数据尚未加载，则加载它
            if sheet_key not in self.data:
                file_path = self.file_paths[data_type]
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    
                    # 清理列名 - 统一格式化时间列名
                    df = self.clean_column_names(df)
                    
                    # 提取表头数据（前3行）
                    headers = df.iloc[:3].copy()
                    
                    # 提取数据行（从第4行开始）
                    data_rows = df.iloc[3:].copy()
                    
                    # 处理前3列的ID信息
                    id_columns = data_rows.iloc[:, :3].copy()
                    id_columns.iloc[:, 0] = id_columns.iloc[:, 0].ffill()  # 对第一列（通常是Line列）进行前向填充
                    
                    # 数值数据部分
                    value_columns = data_rows.iloc[:, 3:].copy()
                    
                    # 重新组合数据
                    processed_data = pd.concat([id_columns, value_columns], axis=1)
                    
                    # 保存处理后的数据和表头
                    self.data[sheet_key] = processed_data
                    self.data[f"{sheet_key}_headers"] = headers
                    
                    # 如果是第一个sheet，也保存到默认位置
                    if sheet_name == "Sheet1":
                        self.data[data_type] = processed_data
                        self.data[f"{data_type}_headers"] = headers
                        
                except Exception as e:
                    print(f"Error loading {sheet_name}: {e}")
                    return None
            
            return self.data.get(sheet_key)
        
        return self.get_data(data_type)
    
    def get_headers(self, data_type: str) -> Optional[pd.DataFrame]:
        """
        Get the headers for daily plan data.
        
        Args:
            data_type: Type of data 
            
        Returns:
            DataFrame containing headers if available, None otherwise
        """
        # 只有Daily Plan有单独保存的表头
        if data_type == "HSA Daily Plan":
            return self.data.get(f"{data_type}_headers")
        return None
    
    def get_headers_for_sheet(self, data_type: str, sheet_name: str) -> Optional[pd.DataFrame]:
        """
        根据数据类型和sheet名称获取相应的表头数据
        
        Args:
            data_type: 数据类型
            sheet_name: sheet名称
        
        Returns:
            DataFrame containing headers if available, None otherwise
        """
        if data_type == "HSA Daily Plan":
            # 生成对应的sheet键
            sheet_key = f"{data_type}_{sheet_name.replace(' ', '_').replace('(', '').replace(')', '')}"
            
            # 如果是第一个sheet且已经加载过
            if sheet_name == "Sheet1" and f"{data_type}_headers" in self.data:
                return self.get_headers(data_type)
            
            # 确保数据已加载
            self.get_data_for_sheet(data_type, sheet_name)
            return self.data.get(f"{sheet_key}_headers")
        
        return self.get_headers(data_type)
        
    def get_available_data_types(self) -> List[str]:
        """
        Get a list of available data types.
        
        Returns:
            List of data type names
        """
        return list(self.file_paths.keys()) 