from django.db import migrations


def install(apps, schema_editor):
    schema = schema_editor.connection.schema_name.replace('"', '""')
    schema_editor.execute(f'''
    CREATE FUNCTION "{schema}".sales_validate_order() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog AS $$
    DECLARE h record; r record; q record; e record;
    BEGIN
      IF TG_OP = 'UPDATE' AND (NEW.branch_id, NEW.customer_id, NEW.shift_id, NEW.created_by_id, NEW.created_at)
         IS DISTINCT FROM (OLD.branch_id, OLD.customer_id, OLD.shift_id, OLD.created_by_id, OLD.created_at) THEN
        RAISE EXCEPTION 'order identity is immutable' USING ERRCODE='23514';
      END IF;
      IF TG_OP = 'UPDATE' AND OLD.current_revision_id IS NOT NULL THEN
        IF NEW.version <> OLD.version + 1 OR OLD.state='cancelled' OR
           (OLD.state='confirmed' AND (NEW.state<>'cancelled' OR NEW.current_revision_id<>OLD.current_revision_id OR NEW.confirmed_quote_id IS DISTINCT FROM OLD.confirmed_quote_id)) OR
           (OLD.state='draft' AND NEW.state='confirmed' AND NEW.current_revision_id<>OLD.current_revision_id) THEN
          RAISE EXCEPTION 'invalid order transition' USING ERRCODE='23514';
        END IF;
      END IF;
      SELECT * INTO h FROM "{schema}".sales_saleorder WHERE id=NEW.id;
      SELECT * INTO r FROM "{schema}".sales_orderrevision WHERE id=h.current_revision_id;
      SELECT * INTO q FROM "{schema}".sales_taxquote WHERE id=r.quote_id;
      SELECT * INTO e FROM "{schema}".sales_orderevent WHERE order_id=h.id ORDER BY version DESC LIMIT 1;
      IF r.id IS NULL OR r.order_id <> h.id OR r.version > h.version OR
         q.branch_id <> h.branch_id OR q.customer_id IS DISTINCT FROM h.customer_id OR
         NOT EXISTS (SELECT 1 FROM "{schema}".sales_cashshift WHERE id=h.shift_id AND branch_id=h.branch_id) OR
         e.id IS NULL OR e.version <> h.version OR
         (h.state='draft' AND r.version<>h.version) OR
         (SELECT count(*) FROM "{schema}".sales_orderevent WHERE order_id=h.id) <> h.version OR
         h.state <> (CASE e.kind WHEN 'saved' THEN 'draft' WHEN 'confirmed' THEN 'confirmed' ELSE 'cancelled' END) THEN
        RAISE EXCEPTION 'order snapshot or event mismatch' USING ERRCODE='23514';
      END IF;
      IF h.confirmed_quote_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM "{schema}".sales_taxquote WHERE id=h.confirmed_quote_id AND branch_id=h.branch_id AND customer_id=h.customer_id
      ) THEN RAISE EXCEPTION 'confirmed quote scope mismatch' USING ERRCODE='23514'; END IF;
      IF h.state='confirmed' AND
         (SELECT count(*) FROM "{schema}".sales_orderhold WHERE revision_id=r.id) <>
         (SELECT count(*) FROM jsonb_array_elements(q.payload->'sources') src
          JOIN "{schema}".catalog_variant v ON v.id=(src->'catalog'->>'variant_id')::uuid
          JOIN "{schema}".catalog_product p ON p.id=v.product_id
          WHERE p.kind IN ('frame','stock_lens','accessory','contact_lens','device')) THEN
        RAISE EXCEPTION 'order stock holds are incomplete' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE CONSTRAINT TRIGGER sales_order_complete AFTER INSERT OR UPDATE ON "{schema}".sales_saleorder
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION "{schema}".sales_validate_order();
    CREATE FUNCTION "{schema}".sales_validate_order_hold() RETURNS trigger
    LANGUAGE plpgsql SET search_path = pg_catalog AS $$
    DECLARE h record; r record; s record; q record;
    BEGIN
      SELECT * INTO r FROM "{schema}".sales_orderrevision WHERE id=NEW.revision_id;
      SELECT * INTO h FROM "{schema}".sales_saleorder WHERE id=r.order_id;
      SELECT * INTO q FROM "{schema}".sales_taxquote WHERE id=r.quote_id;
      SELECT * INTO s FROM "{schema}".inventory_stockreservation WHERE id=NEW.reservation_id;
      IF h.confirmed_quote_id IS NULL OR h.current_revision_id<>r.id OR s.branch_id<>h.branch_id OR
         s.variant_id IS DISTINCT FROM (q.payload->'sources'->(NEW.position-1)->'catalog'->>'variant_id')::uuid OR
         s.quantity IS DISTINCT FROM (q.payload->'rows'->(NEW.position-1)->>'quantity')::bigint OR
         s.position_id IS DISTINCT FROM (r.positions->>(NEW.position-1))::uuid THEN
        RAISE EXCEPTION 'order hold scope mismatch' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $$;
    CREATE CONSTRAINT TRIGGER sales_order_hold_scope AFTER INSERT ON "{schema}".sales_orderhold
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION "{schema}".sales_validate_order_hold();
    ''')


def uninstall(apps, schema_editor):
    schema = schema_editor.connection.schema_name.replace('"', '""')
    schema_editor.execute(f'DROP TRIGGER sales_order_complete ON "{schema}".sales_saleorder; DROP TRIGGER sales_order_hold_scope ON "{schema}".sales_orderhold; DROP FUNCTION "{schema}".sales_validate_order(); DROP FUNCTION "{schema}".sales_validate_order_hold();')


class Migration(migrations.Migration):
    dependencies = [("sales", "0005_orderrevision_saleorder_orderrevision_order_and_more")]
    operations = [migrations.RunPython(install, uninstall)]
