# scripts/delete_db.py
import psycopg2
from psycopg2 import sql

# بيانات الاتصال بمستخدم يملك صلاحيات حذف قاعدة البيانات (غالباً postgres)
DB_NAME_TO_DROP = "optics_tenant"
DB_SUPERUSER_PARAMS = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': '3112',
    'host': 'localhost',
    'port': '5432'
}

try:
    conn = psycopg2.connect(**DB_SUPERUSER_PARAMS)
    conn.autocommit = True
    cursor = conn.cursor()

    # إغلاق الاتصالات النشطة قبل الحذف
    cursor.execute(sql.SQL("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s AND pid <> pg_backend_pid()
    """), [DB_NAME_TO_DROP])

    # حذف قاعدة البيانات
    cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(DB_NAME_TO_DROP)))
    print(f"✅ Database '{DB_NAME_TO_DROP}' deleted successfully.")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if conn:
        cursor.close()
        conn.close()


# python scripts/delete_db.py