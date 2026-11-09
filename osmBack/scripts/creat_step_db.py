import psycopg2
from psycopg2 import sql

# Admin connection (Postgres superuser)
admin_params = {
    'dbname': 'optics_tenant',
    'user': 'taha',
    'password': '3112',
    'host': 'localhost',
    'port': '5432'
}

# Database name and user to create and grant privileges to
target_db = 'optics_tenant'
target_user = 'taha'
target_password = '3112'  # ضع كلمة المرور التي تريدها

try:
    # Connect to default postgres DB
    conn = psycopg2.connect(**admin_params)
    conn.autocommit = True
    cursor = conn.cursor()

    # 🧑‍💻 Create user if not exists
    cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (target_user,))
    if not cursor.fetchone():
        cursor.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(target_user)),
            [target_password]
        )
        print(f"✅ User '{target_user}' created successfully.")
    else:
        print(f"ℹ️ User '{target_user}' already exis ts.")

    # 🛠️ Create database if not exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
    if not cursor.fetchone():
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target_db)))
        print(f"✅ Database '{target_db}' created successfully.")
    else:
        print(f"ℹ️ Database '{target_db}' already exists.")

    cursor.close()
    conn.close()

    # 🎯 Connect to the new DB and grant privileges
    db_conn = psycopg2.connect(
        dbname=target_db,
        user='postgres',
        password='3112',
        host='localhost',
        port='5432'
    )
    db_conn.autocommit = True
    db_cursor = db_conn.cursor()

    db_cursor.execute(f"GRANT ALL PRIVILEGES ON SCHEMA public TO {target_user};")
    db_cursor.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {target_user};")
    db_cursor.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {target_user};")
    db_cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {target_user};")
    db_cursor.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {target_user};")


    print(f"✅ Privileges granted to user '{target_user}' on DB '{target_db}'.")

except Exception as e:
    print(f"❌ Error: {e}")

finally:
    if 'db_cursor' in locals():
        db_cursor.close()
    if 'db_conn' in locals():
        db_conn.close()
