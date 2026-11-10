from psycopg import sql


def grant_tenant_runtime(cursor, schema, role):
    """Used by provisioning and tested with an independently restricted DB role."""
    schema_id, role_id = sql.Identifier(schema), sql.Identifier(role)
    cursor.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(schema_id, role_id))
    cursor.execute(sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {} TO {}").format(schema_id, role_id))
    cursor.execute(sql.SQL("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {} TO {}").format(schema_id, role_id))
    for function in ("finance_validate_journal", "finance_guard_period_void", "finance_guard_draft_state"):
        cursor.execute("SELECT to_regprocedure(%s)", [schema + "." + function + "()"])
        if cursor.fetchone()[0]:
            cursor.execute(sql.SQL("GRANT EXECUTE ON FUNCTION {}.{}() TO {}").format(schema_id, sql.Identifier(function), role_id))
    cursor.execute(sql.SQL("REVOKE INSERT, UPDATE, DELETE ON TABLE {}.django_migrations FROM {}").format(schema_id, role_id))
    cursor.execute("SELECT to_regclass(%s)", [schema + ".access_auditevent"])
    if cursor.fetchone()[0]:
        cursor.execute(sql.SQL("REVOKE UPDATE, DELETE ON TABLE {}.access_auditevent FROM {}").format(schema_id, role_id))
    for table in ("clinical_prescriptionrevision", "clinical_examimage", "inventory_stockreceipt", "inventory_stockmovement", "inventory_reservationevent", "inventory_stockoperation", "inventory_stocklot", "finance_fiscalprofilerevision", "finance_setupoperation", "finance_journalrevision", "finance_journalentry", "finance_journalline", "finance_journaloperation"):
        cursor.execute("SELECT to_regclass(%s)", [schema + "." + table])
        if cursor.fetchone()[0]:
            cursor.execute(sql.SQL("REVOKE UPDATE, DELETE ON TABLE {}.{} FROM {}").format(schema_id, sql.Identifier(table), role_id))
    cursor.execute("SELECT to_regclass(%s)", [schema + ".inventory_stockbalance"])
    if cursor.fetchone()[0]:
        cursor.execute(sql.SQL("REVOKE DELETE ON TABLE {}.inventory_stockbalance FROM {}").format(schema_id, role_id))
    for table, columns in {"finance_journaldraft": ("state", "version"), "finance_journalcounter": ("next_number",), "finance_account": ("name", "active", "version"), "finance_accountingperiod": ("state", "version"), "inventory_stockposition": ("on_hand", "reserved", "version", "branch_id"), "inventory_stockreservation": ("held", "issued", "released", "cancelled", "version"), "catalog_product": ("name", "brand", "model", "active", "version"), "catalog_variant": ("base_price", "active", "version"), "catalog_pricerule": ("active",)}.items():
        cursor.execute("SELECT to_regclass(%s)", [schema + "." + table])
        if cursor.fetchone()[0]:
            cursor.execute(sql.SQL("REVOKE UPDATE, DELETE ON TABLE {}.{} FROM {}").format(schema_id, sql.Identifier(table), role_id))
            cursor.execute(sql.SQL("GRANT UPDATE ({}) ON TABLE {}.{} TO {}").format(sql.SQL(", ").join(map(sql.Identifier, columns)), schema_id, sql.Identifier(table), role_id))
