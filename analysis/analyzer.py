import pandas as pd
import numpy as np

class DataAnalyzer:
    def __init__(self, data):
        self.data = data
    
    def get_summary_stats(self):
        """Get summary statistics"""
        return {
            "rows": len(self.data),
            "columns": len(self.data.columns),
            "numeric_columns": len(self.data.select_dtypes(include=[np.number]).columns),
            "text_columns": len(self.data.select_dtypes(include=['object']).columns),
            "missing_values": self.data.isnull().sum().sum(),
            "missing_percentage": (self.data.isnull().sum().sum() / (len(self.data) * len(self.data.columns)) * 100)
        }
    
    def get_column_analysis(self):
        """Analyze each column"""
        analysis = []
        
        for col in self.data.columns:
            col_info = {
                "column": col,
                "type": str(self.data[col].dtype),
                "unique_values": self.data[col].nunique(),
                "missing": self.data[col].isnull().sum(),
                "missing_pct": (self.data[col].isnull().sum() / len(self.data) * 100)
            }
            
            if pd.api.types.is_numeric_dtype(self.data[col]):
                col_info.update({
                    "mean": self.data[col].mean(),
                    "std": self.data[col].std(),
                    "min": self.data[col].min(),
                    "max": self.data[col].max()
                })
            
            analysis.append(col_info)
        
        return pd.DataFrame(analysis)