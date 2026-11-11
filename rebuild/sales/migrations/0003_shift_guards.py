from django.db import migrations


def install(apps, schema_editor):
    q = schema_editor.quote_name
    schema = q(schema_editor.connection.schema_name)
    shifts, events, registers = (f"{schema}.{q(name)}" for name in ("sales_cashshift", "sales_shiftevent", "sales_cashregister"))
    guard, validate, register_guard = (f"{schema}.{q(name)}" for name in ("sales_guard_shift", "sales_validate_shift_event", "sales_guard_register_active"))
    schema_editor.execute(f"""
    CREATE FUNCTION {guard}() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $body$
    DECLARE r record;
    BEGIN
      IF TG_OP='INSERT' THEN
        SELECT * INTO r FROM {registers} WHERE id=NEW.register_id;
        IF NOT FOUND OR NOT r.active OR r.branch_id<>NEW.branch_id OR NEW.state<>'open' OR NEW.version<>1
          OR NEW.custodian_id<>NEW.created_by_id OR NEW.pending_to_id IS NOT NULL THEN
          RAISE EXCEPTION 'Invalid initial shift' USING ERRCODE='23514';
        END IF;
      ELSE
        IF OLD.state='closed' OR NEW.version<>OLD.version+1 OR
          ROW(NEW.register_id,NEW.branch_id,NEW.register_snapshot,NEW.currency,NEW.opening_cash,NEW.created_by_id,NEW.opened_at)
          IS DISTINCT FROM ROW(OLD.register_id,OLD.branch_id,OLD.register_snapshot,OLD.currency,OLD.opening_cash,OLD.created_by_id,OLD.opened_at) THEN
          RAISE EXCEPTION 'Shift identity or terminal state is immutable' USING ERRCODE='23514';
        END IF;
        IF OLD.state='review' THEN
          IF NEW.state<>'closed' OR ROW(NEW.custodian_id,NEW.expected_cash,NEW.counted_cash,NEW.difference)
            IS DISTINCT FROM ROW(OLD.custodian_id,OLD.expected_cash,OLD.counted_cash,OLD.difference) THEN
            RAISE EXCEPTION 'Count snapshot is immutable' USING ERRCODE='23514';
          END IF;
        ELSIF NEW.state IN ('review','closed') THEN
          IF OLD.pending_to_id IS NOT NULL OR NEW.custodian_id<>OLD.custodian_id THEN
            RAISE EXCEPTION 'Pending handover prevents counting' USING ERRCODE='23514';
          END IF;
        ELSE
          IF NOT ((OLD.pending_to_id IS NULL AND NEW.pending_to_id IS NOT NULL AND NEW.custodian_id=OLD.custodian_id)
            OR (OLD.pending_to_id IS NOT NULL AND NEW.pending_to_id IS NULL AND NEW.custodian_id IN (OLD.custodian_id,OLD.pending_to_id))) THEN
            RAISE EXCEPTION 'Invalid custody transition' USING ERRCODE='23514';
          END IF;
        END IF;
      END IF;
      RETURN NEW;
    END $body$;
    CREATE TRIGGER sales_shift_guard BEFORE INSERT OR UPDATE ON {shifts} FOR EACH ROW EXECUTE FUNCTION {guard}();

    CREATE FUNCTION {validate}() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $body$
    DECLARE s record; e record;
    BEGIN
      IF TG_TABLE_NAME='sales_cashshift' THEN
        s := NEW;
        SELECT * INTO e FROM {events} WHERE shift_id=s.id AND version=s.version;
        IF NOT FOUND THEN RAISE EXCEPTION 'Shift version requires an event' USING ERRCODE='23514'; END IF;
      ELSE
        e := NEW;
        SELECT * INTO s FROM {shifts} WHERE id=e.shift_id;
        IF NOT FOUND OR e.version>s.version THEN RAISE EXCEPTION 'Event requires shift version' USING ERRCODE='23514'; END IF;
        IF e.version<s.version THEN RETURN NEW; END IF;
      END IF;
      IF e.after->>'id' IS DISTINCT FROM s.id::text OR e.after->>'version' IS DISTINCT FROM s.version::text
        OR e.after->>'state' IS DISTINCT FROM s.state OR e.after->>'custodian_id' IS DISTINCT FROM s.custodian_id::text
        OR e.after->>'register_id' IS DISTINCT FROM s.register_id::text OR e.after->>'branch_id' IS DISTINCT FROM s.branch_id::text
        OR e.after->>'pending_to_id' IS DISTINCT FROM s.pending_to_id::text
        OR (e.after->>'opening_cash')::numeric IS DISTINCT FROM s.opening_cash
        OR (e.after->>'pending_cash')::numeric IS DISTINCT FROM s.pending_cash
        OR (e.after->>'expected_cash')::numeric IS DISTINCT FROM s.expected_cash
        OR (e.after->>'counted_cash')::numeric IS DISTINCT FROM s.counted_cash
        OR (e.after->>'difference')::numeric IS DISTINCT FROM s.difference THEN
        RAISE EXCEPTION 'Shift event snapshot mismatch' USING ERRCODE='23514';
      END IF;
      IF (s.version=1 AND e.kind<>'opened') OR
         (s.state='review' AND e.kind<>'count_submitted') OR
         (s.state='closed' AND NOT ((s.difference=0 AND e.kind='count_submitted') OR (s.difference<>0 AND e.kind='variance_approved'))) OR
         (s.state='open' AND s.version>1 AND NOT ((s.pending_to_id IS NOT NULL AND e.kind='handover_requested') OR
           (s.pending_to_id IS NULL AND e.kind IN ('handover_accepted','handover_cancelled','handover_rejected')))) THEN
        RAISE EXCEPTION 'Invalid shift event kind' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $body$;
    CREATE CONSTRAINT TRIGGER sales_shift_head_event AFTER INSERT OR UPDATE ON {shifts}
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION {validate}();
    CREATE CONSTRAINT TRIGGER sales_shift_event_head AFTER INSERT ON {events}
      DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION {validate}();

    CREATE FUNCTION {register_guard}() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $body$
    BEGIN
      IF OLD.active AND NOT NEW.active AND EXISTS (SELECT 1 FROM {shifts} WHERE register_id=OLD.id AND state IN ('open','review')) THEN
        RAISE EXCEPTION 'Unclosed shift prevents register disabling' USING ERRCODE='23514';
      END IF;
      RETURN NEW;
    END $body$;
    CREATE TRIGGER sales_register_shift_guard BEFORE UPDATE OF active ON {registers}
      FOR EACH ROW EXECUTE FUNCTION {register_guard}();
    REVOKE ALL ON FUNCTION {guard}() FROM PUBLIC;
    REVOKE ALL ON FUNCTION {validate}() FROM PUBLIC;
    REVOKE ALL ON FUNCTION {register_guard}() FROM PUBLIC;
    """)


def uninstall(apps, schema_editor):
    q = schema_editor.quote_name
    schema = q(schema_editor.connection.schema_name)
    for trigger, table in (("sales_register_shift_guard", "sales_cashregister"), ("sales_shift_head_event", "sales_cashshift"), ("sales_shift_event_head", "sales_shiftevent"), ("sales_shift_guard", "sales_cashshift")):
        schema_editor.execute(f"DROP TRIGGER {q(trigger)} ON {schema}.{q(table)}")
    for function in ("sales_guard_shift", "sales_validate_shift_event", "sales_guard_register_active"):
        schema_editor.execute(f"DROP FUNCTION {schema}.{q(function)}()")


class Migration(migrations.Migration):
    dependencies = [("sales", "0002_cashshift_shiftevent_and_more")]
    operations = [migrations.RunPython(install, uninstall)]
