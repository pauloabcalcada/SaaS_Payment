from sqlalchemy import create_engine
import streamlit as st
import psycopg2

# Load database credentials from Streamlit secrets
username = st.secrets.db_credentials.username
password = st.secrets.db_credentials.password
host = st.secrets.db_credentials.host
port = st.secrets.db_credentials.port
database = st.secrets.db_credentials.database


# Database configuration for Supabase PostgreSQL using variables
DATABASE_URL = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}?sslmode=require"

# Create a new SQLAlchemy engine instance
engine = create_engine(DATABASE_URL)




