import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from decouple import config

# Configuration
ADMIN_DB_PARAMS = {
    'dbname': config('ADMIN_DB_NAME', default='postgres'),
    'user': config('ADMIN_DB_USER', default='postgres'),
    'password': config('ADMIN_DB_PASSWORD', default='3112'),
    'host': config('DB_HOST', default='localhost'),
    'port': config('DB_PORT', default='5432')
}

TARGET_DB = config('DB_NAME', default='optics_tenant')
TARGET_USER = config('DB_USER', default='taha')
TARGET_PASSWORD = config('DB_PASSWORD', default='3112')

def get_admin_connection():
    conn = psycopg2.connect(**ADMIN_DB_PARAMS)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn

def create_user_if_not_exists():
    try:
        conn = get_admin_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (TARGET_USER,))
        if not cursor.fetchone():
            print(f"Creating user {TARGET_USER}...")
            cursor.execute(sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(TARGET_USER)), (TARGET_PASSWORD,))
        else:
            print(f"User {TARGET_USER} already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating user: {e}")

def create_db_if_not_exists():
    try:
        conn = get_admin_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (TARGET_DB,))
        if not cursor.fetchone():
            print(f"Creating database {TARGET_DB}...")
            cursor.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(TARGET_DB),
                sql.Identifier(TARGET_USER)
            ))
        else:
            print(f"Database {TARGET_DB} already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")

def grant_privileges():
    try:
        # Connect to the TARGET database to grant schema permissions
        # Note: We connect as postgres (superuser) to grant permissions to taha
        conn_params = ADMIN_DB_PARAMS.copy()
        conn_params['dbname'] = TARGET_DB
        
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print(f"Granting permissions on {TARGET_DB} to {TARGET_USER}...")
        
        # Grant public schema usage
        cursor.execute(f"GRANT ALL ON SCHEMA public TO {TARGET_USER}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {TARGET_USER}")
        cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {TARGET_USER}")
        
        # Ensure future tables are accessible
        cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {TARGET_USER}")
        
        print("Permissions granted successfully.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error granting permissions: {e}")

if __name__ == "__main__":
    create_user_if_not_exists()
    create_db_if_not_exists()
    grant_privileges()
