import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Tuple
import io
import base64

# Set style for professional look
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

class ChartGenerator:
    def __init__(self):
        self.figure_size = (12, 8)
        self.dpi = 300
        
    def generate_all_charts(self, data: pd.DataFrame) -> List[Tuple[str, plt.Figure]]:
        """Generate comprehensive charts for the dataset"""
        charts = []
        
        # Get column types
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = data.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = data.select_dtypes(include=['datetime64']).columns.tolist()
        
        # 1. Overview Chart - Data Composition
        fig = self._create_data_overview(data)
        if fig:
            charts.append(("Data Overview", fig))
        
        # 2. Distribution plots for numeric columns
        if numeric_cols:
            # Combined distribution plot
            fig = self._create_distributions_grid(data, numeric_cols[:9])
            if fig:
                charts.append(("Numeric Distributions", fig))
            
            # Box plots for outlier detection
            fig = self._create_box_plots(data, numeric_cols[:10])
            if fig:
                charts.append(("Outlier Analysis", fig))
        
        # 3. Correlation analysis
        if len(numeric_cols) > 1:
            fig = self._create_correlation_heatmap(data, numeric_cols)
            if fig:
                charts.append(("Correlation Analysis", fig))
        
        # 4. Categorical analysis
        if categorical_cols:
            for col in categorical_cols[:2]:  # Top 2 categorical columns
                fig = self._create_categorical_analysis(data, col)
                if fig:
                    charts.append((f"Analysis of {col}", fig))
        
        # 5. Time series if available
        if datetime_cols and numeric_cols:
            fig = self._create_time_series(data, datetime_cols[0], numeric_cols[:3])
            if fig:
                charts.append(("Time Series Analysis", fig))
        
        # 6. Missing data visualization
        fig = self._create_missing_data_plot(data)
        if fig:
            charts.append(("Missing Data Pattern", fig))
        
        return charts
    
    def _create_data_overview(self, data: pd.DataFrame) -> plt.Figure:
        """Create an overview of data composition"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figure_size)
            
            # Data types distribution
            type_counts = data.dtypes.value_counts()
            type_counts.plot(kind='pie', ax=ax1, autopct='%1.1f%%')
            ax1.set_title('Data Types Distribution', fontsize=16, fontweight='bold')
            
            # Missing values by column
            missing_counts = data.isnull().sum()
            missing_counts = missing_counts[missing_counts > 0].sort_values(ascending=True)
            
            if len(missing_counts) > 0:
                missing_counts.plot(kind='barh', ax=ax2, color='coral')
                ax2.set_title('Missing Values by Column', fontsize=16, fontweight='bold')
                ax2.set_xlabel('Number of Missing Values')
            else:
                ax2.text(0.5, 0.5, 'No Missing Values!', ha='center', va='center', 
                        fontsize=20, transform=ax2.transAxes)
                ax2.set_title('Missing Values Analysis', fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            return fig
        except Exception as e:
            print(f"Error creating overview: {e}")
            return None
    
    def _create_distributions_grid(self, data: pd.DataFrame, numeric_cols: List[str]) -> plt.Figure:
        """Create a grid of distribution plots"""
        try:
            n_cols = min(len(numeric_cols), 9)
            n_rows = (n_cols + 2) // 3
            
            fig, axes = plt.subplots(n_rows, 3, figsize=(15, 5*n_rows))
            axes = axes.flatten() if n_rows > 1 else [axes]
            
            for i, col in enumerate(numeric_cols[:n_cols]):
                ax = axes[i]
                
                # Remove outliers for better visualization
                q1 = data[col].quantile(0.01)
                q99 = data[col].quantile(0.99)
                filtered_data = data[col][(data[col] >= q1) & (data[col] <= q99)]
                
                # Plot histogram with KDE
                filtered_data.hist(bins=30, ax=ax, color='skyblue', alpha=0.7, edgecolor='black')
                ax.set_title(f'Distribution of {col}', fontsize=12, fontweight='bold')
                ax.set_xlabel(col)
                ax.set_ylabel('Frequency')
                
                # Add statistics
                mean_val = data[col].mean()
                median_val = data[col].median()
                ax.axvline(mean_val, color='red', linestyle='--', alpha=0.8, label=f'Mean: {mean_val:.2f}')
                ax.axvline(median_val, color='green', linestyle='--', alpha=0.8, label=f'Median: {median_val:.2f}')
                ax.legend(fontsize=8)
            
            # Hide empty subplots
            for j in range(i+1, len(axes)):
                axes[j].set_visible(False)
            
            plt.suptitle('Numeric Variables Distribution', fontsize=18, fontweight='bold', y=1.02)
            plt.tight_layout()
            return fig
        except Exception as e:
            print(f"Error creating distributions: {e}")
            return None
    
    def _create_correlation_heatmap(self, data: pd.DataFrame, numeric_cols: List[str]) -> plt.Figure:
        """Create an enhanced correlation heatmap"""
        try:
            fig, ax = plt.subplots(figsize=self.figure_size)
            
            # Calculate correlation matrix
            corr_matrix = data[numeric_cols].corr()
            
            # Create mask for upper triangle
            mask = np.triu(np.ones_like(corr_matrix), k=1)
            
            # Create heatmap
            sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', 
                       cmap='coolwarm', center=0, square=True, 
                       linewidths=1, cbar_kws={"shrink": .8}, ax=ax)
            
            ax.set_title('Correlation Matrix - Numeric Variables', fontsize=18, fontweight='bold', pad=20)
            
            plt.tight_layout()
            return fig
        except Exception as e:
            print(f"Error creating correlation heatmap: {e}")
            return None
    
    def _create_box_plots(self, data: pd.DataFrame, numeric_cols: List[str]) -> plt.Figure:
        """Create box plots for outlier detection"""
        try:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Normalize data for comparison
            normalized_data = pd.DataFrame()
            for col in numeric_cols[:10]:
                if data[col].std() > 0:
                    normalized_data[col] = (data[col] - data[col].mean()) / data[col].std()
            
            # Create box plots
            normalized_data.boxplot(ax=ax, grid=False)
            ax.set_title('Outlier Detection - Normalized Values', fontsize=18, fontweight='bold')
            ax.set_ylabel('Standardized Values')
            ax.set_xlabel('Variables')
            plt.xticks(rotation=45, ha='right')
            
            # Add reference lines
            ax.axhline(y=3, color='r', linestyle='--', alpha=0.7, label='±3 std')
            ax.axhline(y=-3, color='r', linestyle='--', alpha=0.7)
            ax.legend()
            
            plt.tight_layout()
            return fig
        except Exception as e:
            print(f"Error creating box plots: {e}")
            return None
    
    def _create_categorical_analysis(self, data: pd.DataFrame, cat_col: str) -> plt.Figure:
        """Create analysis for categorical variable"""
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figure_size)
            
            # Value counts
            value_counts = data[cat_col].value_counts().head(15)
            
            # Bar plot
            value_counts.plot(kind='bar', ax=ax1, color='lightcoral')
            ax1.set_title(f'Top Categories in {cat_col}', fontsize=14, fontweight='bold')
            ax1.set_xlabel(cat_col)
            ax1.set_ylabel('Count')
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Pie chart for top 10
            top_10 = value_counts.head(10)
            if len(value_counts) > 10:
                other_count = value_counts[10:].sum()
                top_10['Other'] = other_count
            
            top_10.plot(kind='pie', ax=ax2, autopct='%1.1f%%')
            ax2.set_title(f'Distribution of {cat_col}', fontsize=14, fontweight='bold')
            ax2.set_ylabel('')
            
            plt.tight_layout()
            return fig
        except Exception as e:
            print(f"Error creating categorical analysis: {e}")
            return None
    
    def _create_time_series(self, data: pd.DataFrame, date_col: str, value_cols: List[str]) -> plt.Figure:
        """Create time series visualization"""
        try:
            fig, ax = plt.subplots(figsize=self.figure_size)
            
            # Sort by date
            data_sorted = data.sort_values(date_col)
            
            # Plot each numeric column
            for col in value_cols[:3]:
                ax.plot(data_sorted[date_col], data_sorted[col], label=col, linewidth=2, marker='o', markersize=4)
            
            ax.set_title('Time Series Analysis', fontsize=18, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Values')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Rotate x labels
            plt.xticks(rotation=45, ha='right')
            
            plt.tight_layout()
            return fig
        except Exception as e:
            print(f"Error creating time series: {e}")
            return None
    
    def _create_missing_data_plot(self, data: pd.DataFrame) -> plt.Figure:
        """Create missing data visualization"""
        try:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Calculate missing data percentage
            missing_df = pd.DataFrame({
                'column': data.columns,
                'missing_count': data.isnull().sum(),
                'missing_percentage': (data.isnull().sum() / len(data)) * 100
            })
            
            missing_df = missing_df[missing_df['missing_count'] > 0].sort_values('missing_percentage', ascending=False)
            
            if len(missing_df) > 0:
                # Create bar plot
                bars = ax.bar(range(len(missing_df)), missing_df['missing_percentage'], color='salmon')
                
                # Add value labels on bars
                for i, bar in enumerate(bars):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}%', ha='center', va='bottom')
                
                ax.set_xticks(range(len(missing_df)))
                ax.set_xticklabels(missing_df['column'], rotation=45, ha='right')
                ax.set_ylabel('Missing Percentage (%)')
                ax.set_title('Missing Data Analysis by Column', fontsize=18, fontweight='bold')
                ax.set_ylim(0, max(missing_df['missing_percentage']) * 1.1)
            else:
                ax.text(0.5, 0.5, 'No Missing Data Found!', 
                       ha='center', va='center', fontsize=24, 
                       transform=ax.transAxes, color='green')
                ax.set_title('Missing Data Analysis', fontsize=18, fontweight='bold')
            
            plt.tight_layout()
            return fig
        except Exception as e:
            print(f"Error creating missing data plot: {e}")
            return None
    
    def fig_to_base64(self, fig):
        """Convert figure to base64 string"""
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight', facecolor='white')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return img_base64