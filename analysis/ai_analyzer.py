import google.generativeai as genai
import pandas as pd
import os
from dotenv import load_dotenv
import json

load_dotenv()

class AIAnalyzer:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_data_comprehensive(self, data: pd.DataFrame, language: str = 'en') -> str:
        """Generate comprehensive AI analysis in specified language"""
        try:
            # Get basic statistics
            numeric_cols = data.select_dtypes(include=['number']).columns
            categorical_cols = data.select_dtypes(include=['object']).columns
            
            # Prepare detailed summary
            summary = f"""
            Dataset Overview:
            - Total rows: {len(data)}
            - Total columns: {len(data.columns)}
            - Numeric columns: {len(numeric_cols)}
            - Categorical columns: {len(categorical_cols)}
            - Missing values: {data.isnull().sum().sum()}
            
            Columns: {', '.join(data.columns.tolist())}
            
            Numeric Statistics:
            {data[numeric_cols].describe().to_string() if len(numeric_cols) > 0 else 'No numeric columns'}
            
            Missing Values by Column:
            {data.isnull().sum()[data.isnull().sum() > 0].to_string()}
            
            Sample Data (first 5 rows):
            {data.head().to_string()}
            """
            
            # Language-specific prompts
            language_instructions = {
                'en': "Provide the analysis in English.",
                'es': "Proporciona el análisis en español.",
                'fr': "Fournissez l'analyse en français.",
                'de': "Stellen Sie die Analyse auf Deutsch bereit.",
                'pt': "Forneça a análise em português.",
                'hi': "विश्लेषण हिंदी में प्रदान करें।",
                'zh': "请用中文提供分析。",
                'ja': "日本語で分析を提供してください。"
            }
            
            prompt = f"""
            Analyze this dataset and provide a comprehensive business intelligence report.
            
            {summary}
            
            Please provide:
            
            1. **Executive Summary** (3-4 sentences highlighting the most important findings)
            
            2. **Key Insights** (5-7 bullet points with specific findings)
            
            3. **Data Quality Assessment**
               - Missing data patterns
               - Data completeness score
               - Recommendations for data quality improvement
            
            4. **Statistical Highlights**
               - Most significant correlations
               - Outliers or anomalies
               - Distribution patterns
            
            5. **Business Recommendations** (3-5 actionable recommendations based on the data)
            
            6. **Suggested Further Analysis**
               - What additional data would be helpful
               - What questions remain unanswered
               - Potential next steps
            
            Format the response in markdown with clear sections and bullet points.
            Make it professional and insightful.
            
            {language_instructions.get(language, language_instructions['en'])}
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"Error in AI analysis: {str(e)}"