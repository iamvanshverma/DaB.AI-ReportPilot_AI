import requests
import pandas as pd

class AirtableConnector:
    def __init__(self):
        self.base_url = "https://api.airtable.com/v0"
    
    def connect(self, base_id, table_name, api_key):
        """Connect to Airtable and return data as DataFrame"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}/{base_id}/{table_name}"
            
            # Fetch all records
            all_records = []
            offset = None
            
            while True:
                params = {}
                if offset:
                    params['offset'] = offset
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code != 200:
                    raise Exception(f"Airtable API error: {response.text}")
                
                data = response.json()
                all_records.extend(data.get('records', []))
                
                offset = data.get('offset')
                if not offset:
                    break
            
            # Convert to DataFrame
            if all_records:
                df_data = []
                for record in all_records:
                    row = record['fields'].copy()
                    row['_id'] = record['id']
                    df_data.append(row)
                
                return pd.DataFrame(df_data)
            else:
                return pd.DataFrame()
            
        except Exception as e:
            raise Exception(f"Failed to connect to Airtable: {str(e)}")