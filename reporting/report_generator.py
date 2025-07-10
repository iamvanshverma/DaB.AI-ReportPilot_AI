from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from datetime import datetime
import matplotlib.pyplot as plt
from jinja2 import Template
import pandas as pd

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup custom styles for the report"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Heading style
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#1a73e8'),
            spaceBefore=20,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        )
        
        # Content style
        self.content_style = ParagraphStyle(
            'Content',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=TA_JUSTIFY
        )
    
    def generate_multilingual_report(self, data, language, report_name, 
                                   include_charts, include_raw_data, 
                                   ai_insights, charts):
        """Generate report in specified language"""
        
        # Generate AI analysis in the target language if not already
        from analysis.ai_analyzer import AIAnalyzer
        ai_analyzer = AIAnalyzer()
        
        # Get comprehensive analysis in target language
        if not ai_insights or language != 'en':
            ai_insights = ai_analyzer.analyze_data_comprehensive(data, language)
        
        # Generate PDF
        pdf_buffer = self._generate_enhanced_pdf(
            data, report_name, language, include_charts, 
            include_raw_data, ai_insights, charts
        )
        
        # Generate HTML
        html_content = self._generate_enhanced_html(
            data, report_name, language, ai_insights, charts
        )
        
        return {
            'pdf': pdf_buffer,
            'html': html_content
        }
    
    def _generate_enhanced_pdf(self, data, report_name, language, include_charts, 
                              include_raw_data, ai_insights, charts):
        """Generate enhanced PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # Add header with logo placeholder
        self._add_header(story, report_name, language)
        
        # Executive Summary Section
        self._add_executive_summary(story, data, language)
        
        # AI Insights Section
        if ai_insights:
            self._add_ai_insights(story, ai_insights, language)
        
        # Key Metrics Dashboard
        self._add_metrics_dashboard(story, data, language)
        
        # Charts Section
        if include_charts and charts:
            story.append(PageBreak())
            self._add_charts_section(story, charts, language)
        
        # Data Quality Report
        story.append(PageBreak())
        self._add_data_quality_section(story, data, language)
        
        # Raw Data Sample
        if include_raw_data:
            self._add_data_sample(story, data, language)
        
        # Footer
        self._add_footer(story, language)
        
        # Build PDF
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _add_header(self, story, report_name, language):
        """Add report header"""
        # Title
        title_text = self._get_translated_text("report_title", language).format(name=report_name)
        story.append(Paragraph(title_text, self.title_style))
        
        # Subtitle with date
        date_text = self._get_translated_text("generated_on", language) + f" {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        story.append(Paragraph(date_text, self.subtitle_style))
        
        story.append(Spacer(1, 0.5*inch))
    
    def _add_executive_summary(self, story, data, language):
        """Add executive summary section"""
        story.append(Paragraph(self._get_translated_text("executive_summary", language), self.heading_style))
        
        # Create summary table
        summary_data = [
            [self._get_translated_text("metric", language), 
             self._get_translated_text("value", language),
             self._get_translated_text("status", language)],
            
            [self._get_translated_text("total_records", language), 
             f"{len(data):,}", 
             self._get_status_indicator(len(data) > 100)],
            
            [self._get_translated_text("total_features", language), 
             str(len(data.columns)), 
             self._get_status_indicator(len(data.columns) < 50)],
            
            [self._get_translated_text("data_completeness", language), 
             f"{100 - (data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100):.1f}%",
             self._get_status_indicator((100 - (data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100)) > 90)],
            
            [self._get_translated_text("numeric_features", language), 
             str(len(data.select_dtypes(include=['number']).columns)),
             "📊"],
            
            [self._get_translated_text("categorical_features", language), 
             str(len(data.select_dtypes(include=['object']).columns)),
             "📝"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 0.8*inch])
        summary_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
    
    def _add_ai_insights(self, story, ai_insights, language):
        """Add AI insights section"""
        story.append(Paragraph(self._get_translated_text("ai_analysis", language), self.heading_style))
        
        # Process AI insights
        insights_lines = ai_insights.split('\n')
        
        for line in insights_lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.1*inch))
                continue
            
            # Handle different formatting
            if line.startswith('##'):
                # Subheading
                text = line.replace('##', '').replace('*', '').strip()
                story.append(Paragraph(text, self.styles['Heading3']))
            elif line.startswith('**') and line.endswith('**'):
                # Bold text
                text = line.replace('**', '').strip()
                story.append(Paragraph(f"<b>{text}</b>", self.content_style))
            elif line.startswith('-') or line.startswith('•'):
                # Bullet point
                text = line[1:].strip()
                story.append(Paragraph(f"• {text}", self.content_style))
            else:
                # Regular text
                story.append(Paragraph(line, self.content_style))
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_metrics_dashboard(self, story, data, language):
        """Add key metrics dashboard"""
        story.append(Paragraph(self._get_translated_text("key_metrics", language), self.heading_style))
        
        # Calculate metrics
        numeric_cols = data.select_dtypes(include=['number']).columns
        
        if len(numeric_cols) > 0:
            metrics_data = []
            
            # Add header
            metrics_data.append([
                self._get_translated_text("variable", language),
                self._get_translated_text("mean", language),
                self._get_translated_text("median", language),
                self._get_translated_text("std_dev", language),
                self._get_translated_text("min", language),
                self._get_translated_text("max", language)
            ])
            
            # Add top numeric columns
            for col in numeric_cols[:5]:
                metrics_data.append([
                    col[:20],
                    f"{data[col].mean():.2f}",
                    f"{data[col].median():.2f}",
                    f"{data[col].std():.2f}",
                    f"{data[col].min():.2f}",
                    f"{data[col].max():.2f}"
                ])
            
            metrics_table = Table(metrics_data, colWidths=[1.8*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            story.append(metrics_table)
        else:
            story.append(Paragraph(self._get_translated_text("no_numeric_data", language), self.content_style))
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_charts_section(self, story, charts, language):
        """Add charts section"""
        story.append(Paragraph(self._get_translated_text("data_visualizations", language), self.heading_style))
        story.append(Spacer(1, 0.2*inch))
        
        for i, (title, fig) in enumerate(charts):
            # Add chart title
            story.append(Paragraph(title, self.styles['Heading3']))
            
            # Convert figure to image
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight', facecolor='white')
            img_buffer.seek(0)
            
            # Add image
            img = Image(img_buffer, width=6.5*inch, height=4.5*inch)
            story.append(KeepTogether([img, Spacer(1, 0.3*inch)]))
            
            # Add page break after every 2 charts
            if (i + 1) % 2 == 0 and i < len(charts) - 1:
                story.append(PageBreak())
            
            plt.close(fig)
    
    def _add_data_quality_section(self, story, data, language):
        """Add data quality section"""
        story.append(Paragraph(self._get_translated_text("data_quality_report", language), self.heading_style))
        
        # Missing values analysis
        missing_data = []
        missing_data.append([
            self._get_translated_text("column", language),
            self._get_translated_text("missing_count", language),
            self._get_translated_text("missing_percentage", language),
            self._get_translated_text("data_type", language)
        ])
        
        for col in data.columns:
            missing_count = data[col].isnull().sum()
            if missing_count > 0:
                missing_data.append([
                    col[:30],
                    str(missing_count),
                    f"{(missing_count / len(data) * 100):.1f}%",
                    str(data[col].dtype)
                ])
        
        if len(missing_data) > 1:
            missing_table = Table(missing_data, colWidths=[2.5*inch, 1.2*inch, 1.5*inch, 1.2*inch])
            missing_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fff5f5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (1, 1), (2, -1), 'CENTER')
            ]))
            story.append(missing_table)
        else:
            perfect_text = self._get_translated_text("perfect_data_quality", language)
            story.append(Paragraph(f"✅ {perfect_text}", self.content_style))
        
        story.append(Spacer(1, 0.3*inch))
    
    def _add_data_sample(self, story, data, language):
        """Add data sample section"""
        story.append(PageBreak())
        story.append(Paragraph(self._get_translated_text("data_sample", language), self.heading_style))
        
        # Get sample data
        sample_data = data.head(10)
        
        # Create table data
        table_data = [list(sample_data.columns)]
        for _, row in sample_data.iterrows():
            row_data = []
            for val in row.values:
                # Truncate long values
                str_val = str(val)
                if len(str_val) > 15:
                    str_val = str_val[:12] + "..."
                row_data.append(str_val)
            table_data.append(row_data)
        
        # Calculate column widths
        n_cols = len(sample_data.columns)
        col_width = 7.0 / n_cols if n_cols > 0 else 1.0
        col_widths = [col_width * inch] * n_cols
        
        sample_table = Table(table_data, colWidths=col_widths)
        sample_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        
        story.append(sample_table)
    
    def _add_footer(self, story, language):
        """Add report footer"""
        story.append(Spacer(1, 0.5*inch))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER
        )
        
        footer_text = self._get_translated_text("footer_text", language)
        story.append(Paragraph(footer_text, footer_style))
    
    def _get_status_indicator(self, is_good):
        """Get status indicator emoji"""
        return "✅" if is_good else "⚠️"
    
    def _generate_enhanced_html(self, data, report_name, language, ai_insights, charts):
        """Generate enhanced HTML report"""
        template = """
        <!DOCTYPE html>
        <html lang="{{ language }}">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{ report_name }}</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f5f7fa;
                }
                
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                
                .header {
                    background: linear-gradient(135deg, #1a73e8 0%, #4285f4 100%);
                    color: white;
                    padding: 60px 40px;
                    text-align: center;
                    border-radius: 12px;
                    margin-bottom: 40px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }
                
                .header h1 {
                    font-size: 3em;
                    font-weight: 300;
                    margin-bottom: 10px;
                }
                
                .header p {
                    font-size: 1.2em;
                    opacity: 0.9;
                }
                
                .metrics-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 25px;
                    margin: 40px 0;
                }
                
                .metric-card {
                    background: white;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                    text-align: center;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }
                
                .metric-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                }
                
                .metric-value {
                    font-size: 2.5em;
                    font-weight: bold;
                    color: #1a73e8;
                    margin: 10px 0;
                }
                
                .metric-label {
                    font-size: 0.95em;
                    color: #666;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                
                .section {
                    background: white;
                    padding: 40px;
                    margin-bottom: 30px;
                    border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                }
                
                .section h2 {
                    color: #1a73e8;
                    font-size: 2em;
                    margin-bottom: 25px;
                    padding-bottom: 15px;
                    border-bottom: 3px solid #e8f0fe;
                }
                
                .ai-insights {
                    background: linear-gradient(135deg, #e8f0fe 0%, #f8f9fa 100%);
                    padding: 30px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #1a73e8;
                }
                
                .ai-insights h3 {
                    color: #1a73e8;
                    margin-bottom: 15px;
                }
                
                .ai-insights p, .ai-insights li {
                    line-height: 1.8;
                    margin-bottom: 10px;
                }
                
                .chart-container {
                    margin: 30px 0;
                    text-align: center;
                }
                
                .chart-container h3 {
                    color: #333;
                    margin-bottom: 20px;
                    font-size: 1.5em;
                }
                
                .chart-container img {
                    max-width: 100%;
                    height: auto;
                    border-radius: 8px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }
                
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                
                th, td {
                    padding: 15px;
                    text-align: left;
                    border-bottom: 1px solid #e0e0e0;
                }
                
                th {
                    background-color: #1a73e8;
                    color: white;
                    font-weight: 500;
                    text-transform: uppercase;
                    font-size: 0.9em;
                    letter-spacing: 0.5px;
                }
                
                tr:hover {
                    background-color: #f8f9fa;
                }
                
                .footer {
                    text-align: center;
                    padding: 40px;
                    color: #666;
                    font-size: 0.95em;
                }
                
                @media print {
                    .section {
                        break-inside: avoid;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{ report_name }}</h1>
                    <p>{{ date_label }}: {{ date }}</p>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">{{ total_rows_label }}</div>
                        <div class="metric-value">{{ total_rows }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">{{ total_columns_label }}</div>
                        <div class="metric-value">{{ total_columns }}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">{{ completeness_label }}</div>
                        <div class="metric-value">{{ completeness }}%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">{{ numeric_features_label }}</div>
                        <div class="metric-value">{{ numeric_features }}</div>
                    </div>
                </div>
                
                {% if ai_insights %}
                <div class="section">
                    <h2>{{ ai_insights_label }}</h2>
                    <div class="ai-insights">
                        {{ ai_insights_html | safe }}
                    </div>
                </div>
                {% endif %}
                
                {% if charts %}
                <div class="section">
                    <h2>{{ visualizations_label }}</h2>
                    {% for title, chart_base64 in charts %}
                    <div class="chart-container">
                        <h3>{{ title }}</h3>
                        <img src="data:image/png;base64,{{ chart_base64 }}" alt="{{ title }}">
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                <div class="footer">
                    <p>{{ footer_text }}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Convert AI insights to HTML
        ai_insights_html = ai_insights.replace('\n', '<br>').replace('**', '<strong>').replace('**', '</strong>')
        
        # Prepare charts for HTML
        html_charts = []
        if charts:
            from visualization.chart_generator import ChartGenerator
            chart_gen = ChartGenerator()
            for title, fig in charts[:6]:  # Limit to 6 charts for HTML
                html_charts.append((title, chart_gen.fig_to_base64(fig)))
        
        # Calculate metrics
        completeness = 100 - (data.isnull().sum().sum() / (len(data) * len(data.columns)) * 100)
        
        from jinja2 import Template
        tmpl = Template(template)
        
        return tmpl.render(
            language=language,
            report_name=report_name,
            date_label=self._get_translated_text("generated_on", language),
            date=datetime.now().strftime('%Y-%m-%d %H:%M'),
            total_rows_label=self._get_translated_text("total_records", language),
            total_rows=f"{len(data):,}",
            total_columns_label=self._get_translated_text("total_features", language),
            total_columns=len(data.columns),
            completeness_label=self._get_translated_text("data_completeness", language),
            completeness=f"{completeness:.1f}",
            numeric_features_label=self._get_translated_text("numeric_features", language),
            numeric_features=len(data.select_dtypes(include=['number']).columns),
            ai_insights_label=self._get_translated_text("ai_analysis", language),
            ai_insights_html=ai_insights_html,
            visualizations_label=self._get_translated_text("data_visualizations", language),
            charts=html_charts,
            footer_text=self._get_translated_text("footer_text", language)
        )
    
    def _get_translated_text(self, key, language):
        """Get translated text for different languages"""
        translations = {
            "en": {
                "report_title": "Data Analysis Report - {name}",
                "generated_on": "Generated on",
                "executive_summary": "Executive Summary",
                "metric": "Metric",
                "value": "Value",
                "status": "Status",
                "total_records": "Total Records",
                "total_features": "Total Features",
                "data_completeness": "Data Completeness",
                "numeric_features": "Numeric Features",
                "categorical_features": "Categorical Features",
                "ai_analysis": "AI-Powered Analysis",
                "key_metrics": "Key Statistical Metrics",
                "variable": "Variable",
                "mean": "Mean",
                "median": "Median",
                "std_dev": "Std Dev",
                "min": "Min",
                "max": "Max",
                "data_visualizations": "Data Visualizations",
                "data_quality_report": "Data Quality Report",
                "column": "Column",
                "missing_count": "Missing Count",
                "missing_percentage": "Missing %",
                "data_type": "Data Type",
                "data_sample": "Data Sample (First 10 Rows)",
                "perfect_data_quality": "Perfect! No missing values found in the dataset.",
                "no_numeric_data": "No numeric data available for statistical analysis.",
                "footer_text": "This report was automatically generated using AI-powered data analysis. Powered by Gemini AI."
            },
            "es": {
                "report_title": "Informe de Análisis de Datos - {name}",
                "generated_on": "Generado el",
                "executive_summary": "Resumen Ejecutivo",
                "metric": "Métrica",
                "value": "Valor",
                "status": "Estado",
                "total_records": "Total de Registros",
                "total_features": "Total de Características",
                "data_completeness": "Integridad de Datos",
                "numeric_features": "Características Numéricas",
                "categorical_features": "Características Categóricas",
                "ai_analysis": "Análisis con IA",
                "key_metrics": "Métricas Estadísticas Clave",
                "variable": "Variable",
                "mean": "Media",
                "median": "Mediana",
                "std_dev": "Desv. Est.",
                "min": "Mín",
                "max": "Máx",
                "data_visualizations": "Visualizaciones de Datos",
                "data_quality_report": "Informe de Calidad de Datos",
                "column": "Columna",
                "missing_count": "Valores Faltantes",
                "missing_percentage": "% Faltante",
                "data_type": "Tipo de Dato",
                "data_sample": "Muestra de Datos (Primeras 10 Filas)",
                "perfect_data_quality": "¡Perfecto! No se encontraron valores faltantes en el conjunto de datos.",
                "no_numeric_data": "No hay datos numéricos disponibles para análisis estadístico.",
                "footer_text": "Este informe fue generado automáticamente usando análisis de datos con IA. Desarrollado con Gemini AI."
            },
            "fr": {
                "report_title": "Rapport d'Analyse de Données - {name}",
                "generated_on": "Généré le",
                "executive_summary": "Résumé Exécutif",
                "metric": "Métrique",
                "value": "Valeur",
                "status": "Statut",
                "total_records": "Total des Enregistrements",
                "total_features": "Total des Caractéristiques",
                "data_completeness": "Complétude des Données",
                "numeric_features": "Caractéristiques Numériques",
                "categorical_features": "Caractéristiques Catégorielles",
                "ai_analysis": "Analyse par IA",
                "key_metrics": "Métriques Statistiques Clés",
                "variable": "Variable",
                "mean": "Moyenne",
                "median": "Médiane",
                "std_dev": "Écart-type",
                "min": "Min",
                "max": "Max",
                "data_visualizations": "Visualisations de Données",
                "data_quality_report": "Rapport de Qualité des Données",
                "column": "Colonne",
                "missing_count": "Valeurs Manquantes",
                "missing_percentage": "% Manquant",
                "data_type": "Type de Donnée",
                "data_sample": "Échantillon de Données (10 Premières Lignes)",
                "perfect_data_quality": "Parfait! Aucune valeur manquante trouvée dans le jeu de données.",
                "no_numeric_data": "Aucune donnée numérique disponible pour l'analyse statistique.",
                "footer_text": "Ce rapport a été généré automatiquement en utilisant l'analyse de données par IA. Alimenté par Gemini AI."
            },
            "de": {
                "report_title": "Datenanalysebericht - {name}",
                "generated_on": "Erstellt am",
                "executive_summary": "Zusammenfassung",
                "metric": "Metrik",
                "value": "Wert",
                "status": "Status",
                "total_records": "Gesamtanzahl Datensätze",
                "total_features": "Gesamtanzahl Merkmale",
                "data_completeness": "Datenvollständigkeit",
                "numeric_features": "Numerische Merkmale",
                "categorical_features": "Kategorische Merkmale",
                "ai_analysis": "KI-gestützte Analyse",
                "key_metrics": "Wichtige statistische Metriken",
                "variable": "Variable",
                "mean": "Mittelwert",
                "median": "Median",
                "std_dev": "Std.-Abw.",
                "min": "Min",
                "max": "Max",
                "data_visualizations": "Datenvisualisierungen",
                "data_quality_report": "Datenqualitätsbericht",
                "column": "Spalte",
                "missing_count": "Fehlende Werte",
                "missing_percentage": "Fehlend %",
                "data_type": "Datentyp",
                "data_sample": "Datenstichprobe (Erste 10 Zeilen)",
                "perfect_data_quality": "Perfekt! Keine fehlenden Werte im Datensatz gefunden.",
                "no_numeric_data": "Keine numerischen Daten für statistische Analyse verfügbar.",
                "footer_text": "Dieser Bericht wurde automatisch mit KI-gestützter Datenanalyse erstellt. Unterstützt von Gemini AI."
            },
            "pt": {
                "report_title": "Relatório de Análise de Dados - {name}",
                "generated_on": "Gerado em",
                "executive_summary": "Resumo Executivo",
                "metric": "Métrica",
                "value": "Valor",
                "status": "Status",
                "total_records": "Total de Registros",
                "total_features": "Total de Características",
                "data_completeness": "Completude dos Dados",
                "numeric_features": "Características Numéricas",
                "categorical_features": "Características Categóricas",
                "ai_analysis": "Análise com IA",
                "key_metrics": "Métricas Estatísticas Principais",
                "variable": "Variável",
                "mean": "Média",
                "median": "Mediana",
                "std_dev": "Desvio Padrão",
                "min": "Mín",
                "max": "Máx",
                "data_visualizations": "Visualizações de Dados",
                "data_quality_report": "Relatório de Qualidade dos Dados",
                "column": "Coluna",
                "missing_count": "Valores Ausentes",
                "missing_percentage": "% Ausente",
                "data_type": "Tipo de Dado",
                "data_sample": "Amostra de Dados (Primeiras 10 Linhas)",
                "perfect_data_quality": "Perfeito! Nenhum valor ausente encontrado no conjunto de dados.",
                "no_numeric_data": "Não há dados numéricos disponíveis para análise estatística.",
                "footer_text": "Este relatório foi gerado automaticamente usando análise de dados com IA. Desenvolvido com Gemini AI."
            },
            "hi": {
                "report_title": "डेटा विश्लेषण रिपोर्ट - {name}",
                "generated_on": "जनरेट किया गया",
                "executive_summary": "कार्यकारी सारांश",
                "metric": "मीट्रिक",
                "value": "मूल्य",
                "status": "स्थिति",
                "total_records": "कुल रिकॉर्ड",
                "total_features": "कुल विशेषताएं",
                "data_completeness": "डेटा पूर्णता",
                "numeric_features": "संख्यात्मक विशेषताएं",
                "categorical_features": "श्रेणीबद्ध विशेषताएं",
                "ai_analysis": "AI-संचालित विश्लेषण",
                "key_metrics": "मुख्य सांख्यिकीय मेट्रिक्स",
                "variable": "चर",
                "mean": "माध्य",
                "median": "मध्यक",
                "std_dev": "मानक विचलन",
                "min": "न्यूनतम",
                "max": "अधिकतम",
                "data_visualizations": "डेटा विज़ुअलाइज़ेशन",
                "data_quality_report": "डेटा गुणवत्ता रिपोर्ट",
                "column": "कॉलम",
                "missing_count": "गुम मान",
                "missing_percentage": "गुम %",
                "data_type": "डेटा प्रकार",
                "data_sample": "डेटा नमूना (पहली 10 पंक्तियाँ)",
                "perfect_data_quality": "बिल्कुल सही! डेटासेट में कोई गुम मान नहीं मिला।",
                "no_numeric_data": "सांख्यिकीय विश्लेषण के लिए कोई संख्यात्मक डेटा उपलब्ध नहीं है।",
                "footer_text": "यह रिपोर्ट AI-संचालित डेटा विश्लेषण का उपयोग करके स्वचालित रूप से तैयार की गई थी। Gemini AI द्वारा संचालित।"
            },
            "zh": {
                "report_title": "数据分析报告 - {name}",
                "generated_on": "生成日期",
                "executive_summary": "执行摘要",
                "metric": "指标",
                "value": "值",
                "status": "状态",
                "total_records": "总记录数",
                "total_features": "总特征数",
                "data_completeness": "数据完整性",
                "numeric_features": "数值特征",
                "categorical_features": "分类特征",
                "ai_analysis": "AI驱动分析",
                "key_metrics": "关键统计指标",
                "variable": "变量",
                "mean": "平均值",
                "median": "中位数",
                "std_dev": "标准差",
                "min": "最小值",
                "max": "最大值",
                "data_visualizations": "数据可视化",
                "data_quality_report": "数据质量报告",
                "column": "列",
                "missing_count": "缺失数量",
                "missing_percentage": "缺失率",
                "data_type": "数据类型",
                "data_sample": "数据样本（前10行）",
                "perfect_data_quality": "完美！数据集中未发现缺失值。",
                "no_numeric_data": "没有可用于统计分析的数值数据。",
                "footer_text": "此报告使用AI驱动的数据分析自动生成。由Gemini AI提供支持。"
            },
            "ja": {
                "report_title": "データ分析レポート - {name}",
                "generated_on": "生成日",
                "executive_summary": "エグゼクティブサマリー",
                "metric": "メトリック",
                "value": "値",
                "status": "ステータス",
                "total_records": "総レコード数",
                "total_features": "総特徴数",
                "data_completeness": "データ完全性",
                "numeric_features": "数値特徴",
                "categorical_features": "カテゴリ特徴",
                "ai_analysis": "AI分析",
                "key_metrics": "主要統計指標",
                "variable": "変数",
                "mean": "平均",
                "median": "中央値",
                "std_dev": "標準偏差",
                "min": "最小",
                "max": "最大",
                "data_visualizations": "データの視覚化",
                "data_quality_report": "データ品質レポート",
                "column": "列",
                "missing_count": "欠損数",
                "missing_percentage": "欠損率",
                "data_type": "データ型",
                "data_sample": "データサンプル（最初の10行）",
                "perfect_data_quality": "完璧です！データセットに欠損値は見つかりませんでした。",
                "no_numeric_data": "統計分析に使用できる数値データがありません。",
                "footer_text": "このレポートはAI駆動のデータ分析を使用して自動的に生成されました。Gemini AIによって提供されています。"
            }
        }
        
        lang_dict = translations.get(language, translations['en'])
        return lang_dict.get(key, translations['en'].get(key, key))