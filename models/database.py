from sqlalchemy import create_engine


# # Database configuration
# DATABASE_URL = (
#     "mssql+pyodbc://fish-storm-app-server-admin:m67A$nxUGYc4n8my@fish-storm-app-server.database.windows.net:1433/fish-storm-app-database"
#     "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=900"
# )

# # Create a new SQLAlchemy engine instance
# engine = create_engine(DATABASE_URL)


# Database configuration
DATABASE_URL = "sqlite:///local_database.db"  # SQLite database file

# Create a new SQLAlchemy engine instance
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
