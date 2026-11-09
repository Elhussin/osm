from psycopg import sql


def grant_tenant_runtime(cursor, schema, role):
    """Used by provisioning and tested with an independently restricted DB role."""
    schema_id, role_id = sql.Identifier(schema), sql.Identifier(role)
    cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(schema_id, role_id))
    cursor.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {} TO {}").format(schema_id, role_id))
    cursor.execute(sql.SQL("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {} TO {}").format(schema_id, role_id))
    cursor.execute(sql.SQL("REVOKE INSERT, UPDATE, DELETE ON TABLE {}.django_migrations FROM {}").format(schema_id, role_id))
    cursor.execute("SELECT to_regclass(%s)", [schema + ".access_auditevent"])
    if cursor.fetchone()[0]:
        cursor.execute(sql.SQL("REVOKE UPDATE, DELETE ON TABLE {}.access_auditevent FROM {}").format(schema_id, role_id))
    for table in ("clinical_prescriptionrevision", "clinical_examimage"):
        cursor.execute("SELECT to_regclass(%s)", [schema + "." + table])
        if cursor.fetchone()[0]:
            cursor.execute(sql.SQL("REVOKE UPDATE, DELETE ON TABLE {}.{} FROM {}").format(schema_id, sql.Identifier(table), role_id))
