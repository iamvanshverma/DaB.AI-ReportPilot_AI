import pandas as pd
from sqlalchemy import create_engine
import urllib.parse

class SQLDatabaseConnector:
    def connect(self, db_type, host, port, database, username, password, table_name=None, custom_query=None):
        """Connect to SQL database and return data as DataFrame"""
        try:
            # Create connection string
            if db_type == "postgresql":
                connection_string = f"postgresql://{username}:{urllib.parse.quote_plus(password)}@{host}:{port}/{database}"
            elif db_type == "mysql":
                connection_string = f"mysql+pymysql://{username}:{urllib.parse.quote_plus(password)}@{host}:{port}/{database}"
            elif db_type == "mssql":
                connection_string = f"mssql+pyodbc://{username}:{urllib.parse.quote_plus(password)}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
            else:
                raise ValueError(f"Unsupported database type: {db_type}")
            
            engine = create_engine(connection_string)
            
            # Execute query or fetch table
            if custom_query:
                df = pd.read_sql_query(custom_query, engine)
            elif table_name:
                df = pd.read_sql_table(table_name, engine)
            else:
                raise ValueError("Either table_name or custom_query must be provided")
            
            engine.dispose()
            return df
            
        except Exception as e:
            raise Exception(f"Failed to connect to {db_type}: {str(e)}")