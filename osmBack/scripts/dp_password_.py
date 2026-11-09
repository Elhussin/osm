import psycopg2
from psycopg2 import sql

# معلومات الاتصال
host = "localhost"  # أو عنوان السيرفر
port = "5432"
admin_user = "postgres"
admin_password = "admin1234"  # كلمة مرور المستخدم الإداري
new_password = "3112"

try:
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(
        dbname="postgres",
        user=admin_user,
        password=admin_password,
        host=host,
        port=port
    )
    conn.autocommit = True  # ضروري لتغيير كلمة المرور

    # إنشاء كيرسر
    cur = conn.cursor()

    # تنفيذ أمر تغيير كلمة المرور
    cur.execute(sql.SQL("ALTER USER {} WITH PASSWORD %s").format(sql.Identifier(admin_user)), [new_password])
    print(f" Pasword change '{admin_user}' Sucss.")

    # إغلاق الاتصال
    cur.close()
    conn.close()

except Exception as e:
    print("Error :v", e)
