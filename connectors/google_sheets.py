import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re
import json
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class GoogleSheetsConnector:
    def __init__(self, credentials_dict: Dict[str, Any]):
        """Initialize with credentials dictionary"""
        self.creds_dict = credentials_dict
        self.client = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Define scopes
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive.readonly'
                ]
                
                # Create credentials from dict
                creds = Credentials.from_service_account_info(
                    self.creds_dict,
                    scopes=scopes
                )
                
                # Authorize client
                self.client = gspread.authorize(creds)
                logger.info("Successfully authenticated with Google Sheets")
                return
                
            except Exception as e:
                logger.error(f"Authentication attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise Exception(f"Failed to authenticate after {max_retries} attempts: {str(e)}")
    
    def extract_sheet_id(self, url: str) -> str:
        """Extract sheet ID from URL"""
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'^([a-zA-Z0-9-_]+)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Invalid Google Sheets URL")
    
    def connect(self, sheet_url: str, worksheet_name: Optional[str] = None) -> pd.DataFrame:
        """Connect to sheet and return data with error handling"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Extract sheet ID
                sheet_id = self.extract_sheet_id(sheet_url)
                logger.info(f"Connecting to sheet ID: {sheet_id}")
                
                # Open spreadsheet
                spreadsheet = self.client.open_by_key(sheet_id)
                
                # Get worksheet
                if worksheet_name:
                    worksheet = spreadsheet.worksheet(worksheet_name)
                else:
                    worksheet = spreadsheet.sheet1
                
                # Get all data
                data = worksheet.get_all_values()
                
                if not data:
                    return pd.DataFrame()
                
                # Create DataFrame
                headers = data[0]
                rows = data[1:]
                
                # Clean headers
                headers = [h if h else f"Column_{i}" for i, h in enumerate(headers)]
                
                df = pd.DataFrame(rows, columns=headers)
                
                # Clean data types
                df = self._clean_data(df)
                
                logger.info(f"Successfully loaded {len(df)} rows")
                return df
                
            except gspread.exceptions.APIError as e:
                if "403" in str(e) or "PERMISSION_DENIED" in str(e):
                    raise Exception(
                        f"Permission denied. Please share your Google Sheet with: {self.creds_dict.get('client_email')}"
                    )
                elif "429" in str(e):  # Rate limit
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                raise
            except Exception as e:
                if attempt < max_retries - 1 and "503" in str(e):  # Service unavailable
                    logger.warning(f"Service unavailable, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise Exception(f"Connection error: {str(e)}")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and convert data types"""
        # Remove empty columns/rows
        df = df.loc[:, (df != '').any(axis=0)]
        df = df[(df != '').any(axis=1)]
        
        # Convert numeric columns
        for col in df.columns:
            try:
                # Try to convert to numeric
                numeric_data = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
                if numeric_data.notna().sum() > len(df) * 0.5:
                    df[col] = numeric_data
            except:
                pass
        
        return df