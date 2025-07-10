from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import pickle
import os
import uuid
import logging

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.jobs_dir = "scheduled_jobs"
        os.makedirs(self.jobs_dir, exist_ok=True)
    
    def schedule_job(self, job_config, schedule_params, initial_data):
        """Schedule a new job"""
        try:
            job_id = str(uuid.uuid4())[:8]
            
            # Save job config
            job_file = os.path.join(self.jobs_dir, f"{job_id}.pkl")
            with open(job_file, 'wb') as f:
                pickle.dump({
                    'config': job_config,
                    'schedule': schedule_params,
                    'data': initial_data.to_dict() if initial_data is not None else None
                }, f)
            
            # Create trigger
            frequency = schedule_params['frequency']
            
            if frequency == 'hourly':
                trigger = IntervalTrigger(hours=1)
            elif frequency == 'daily':
                trigger = CronTrigger(
                    hour=schedule_params.get('hour', 9),
                    minute=schedule_params.get('minute', 0)
                )
            elif frequency == 'weekly':
                trigger = CronTrigger(
                    day_of_week=schedule_params.get('day', 'mon'),
                    hour=schedule_params.get('hour', 9),
                    minute=schedule_params.get('minute', 0)
                )
            
            # Add job
            self.scheduler.add_job(
                func=self._execute_job,
                trigger=trigger,
                args=[job_id],
                id=job_id
            )
            
            logger.info(f"Job scheduled: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to schedule job: {str(e)}")
            return None
    
    def _execute_job(self, job_id):
        """Execute a scheduled job"""
        try:
            # Load job config
            job_file = os.path.join(self.jobs_dir, f"{job_id}.pkl")
            with open(job_file, 'rb') as f:
                job_data = pickle.load(f)
            
            config = job_data['config']
            
            # Refresh data if needed
            if config.get('auto_refresh'):
                from connectors.google_sheets import GoogleSheetsConnector
                connector = GoogleSheetsConnector(config['creds'])
                data = connector.connect(config['sheet_url'])
            else:
                import pandas as pd
                data = pd.DataFrame(job_data['data'])
            
            # Generate report
            from analysis.ai_analyzer import AIAnalyzer
            from visualization.chart_generator import ChartGenerator
            from reporting.report_generator import ReportGenerator
            from utils.email_sender import EmailSender
            
            # Analyze
            ai = AIAnalyzer()
            insights = ai.analyze_data_comprehensive(data)
            
            # Generate charts
            chart_gen = ChartGenerator()
            charts = chart_gen.generate_all_charts(data) if config.get('include_charts') else []
            
            # Create report
            report_gen = ReportGenerator()
            report_content = report_gen.generate_multilingual_report(
                data=data,
                language=config['language'],
                report_name=config['job_name'],
                include_charts=config.get('include_charts', True),
                include_raw_data=False,
                ai_insights=insights,
                charts=charts
            )
            
            # Send email
            email_sender = EmailSender()
            email_sender.send_report(
                recipient_email=config['recipient'],
                report_content=report_content,
                report_name=config['job_name'],
                language=config['language']
            )
            
            logger.info(f"Job {job_id} executed successfully")
            
        except Exception as e:
            logger.error(f"Job execution failed: {str(e)}")
    
    def get_all_jobs(self):
        """Get all scheduled jobs"""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            job_file = os.path.join(self.jobs_dir, f"{job.id}.pkl")
            if os.path.exists(job_file):
                with open(job_file, 'rb') as f:
                    job_data = pickle.load(f)
                
                jobs.append({
                    'id': job.id,
                    'config': job_data['config'],
                    'schedule': job_data['schedule'],
                    'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M') if job.next_run_time else 'N/A'
                })
        
        return jobs
    
    def run_job_now(self, job_id):
        """Run job immediately"""
        self._execute_job(job_id)
    
    def delete_job(self, job_id):
        """Delete a job"""
        try:
            self.scheduler.remove_job(job_id)
            job_file = os.path.join(self.jobs_dir, f"{job_id}.pkl")
            if os.path.exists(job_file):
                os.remove(job_file)
            return True
        except:
            return False