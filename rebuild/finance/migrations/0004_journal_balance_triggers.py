from django.db import migrations


def install(apps, schema_editor):
    schema = schema_editor.quote_name(schema_editor.connection.schema_name)
    schema_editor.execute(f"""
CREATE FUNCTION {schema}.finance_validate_journal() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog AS $body$
DECLARE targets uuid[]; target uuid; item record;
BEGIN
    IF TG_TABLE_NAME = 'finance_journalentry' THEN
        targets := ARRAY[NEW.id];
    ELSIF TG_OP = 'INSERT' THEN
        targets := ARRAY[NEW.entry_id];
    ELSIF TG_OP = 'DELETE' THEN
        targets := ARRAY[OLD.entry_id];
    ELSE
        targets := ARRAY[OLD.entry_id, NEW.entry_id];
    END IF;
    FOR target IN SELECT DISTINCT unnest(targets) LOOP
        SELECT e.*, d.branch_id AS draft_branch, d.state AS draft_state,
            r.draft_id AS revision_draft, r.period_id AS revision_period,
            r.entry_date AS revision_date, r.total_debit AS revision_debit, r.total_credit AS revision_credit,
            p.starts_on, p.ends_on, p.state AS period_state,
            original.branch_id AS original_branch, original.reverses_id AS original_reverses,
            original.total_debit AS original_debit, original.total_credit AS original_credit,
            sums.line_count, sums.debit_sum, sums.credit_sum,
            EXISTS(SELECT 1 FROM {schema}.finance_journaloperation op WHERE op.entry_id=e.id AND
                ((e.revision_id IS NOT NULL AND op.kind='journal_posted' AND op.draft_id=e.draft_id)
                 OR (e.reverses_id IS NOT NULL AND op.kind='journal_reversed' AND op.draft_id IS NULL))) AS recorded
        INTO item FROM {schema}.finance_journalentry e
        LEFT JOIN {schema}.finance_journaldraft d ON d.id=e.draft_id
        LEFT JOIN {schema}.finance_journalrevision r ON r.id=e.revision_id
        LEFT JOIN {schema}.finance_accountingperiod p ON p.id=e.period_id
        LEFT JOIN {schema}.finance_journalentry original ON original.id=e.reverses_id
        LEFT JOIN LATERAL (
            SELECT count(*) AS line_count, coalesce(sum(l.debit),0) AS debit_sum,
                coalesce(sum(l.credit),0) AS credit_sum
            FROM {schema}.finance_journalline l WHERE l.entry_id=e.id
        ) sums ON true WHERE e.id=target;
        IF NOT FOUND THEN CONTINUE; END IF;
        IF item.line_count NOT BETWEEN 2 AND 40 OR item.debit_sum<>item.total_debit
            OR item.credit_sum<>item.total_credit OR item.debit_sum<>item.credit_sum
            OR NOT item.recorded OR item.period_state='void'
            OR item.entry_date<item.starts_on OR item.entry_date>item.ends_on THEN
            RAISE EXCEPTION 'Journal is incomplete or unbalanced' USING ERRCODE='23514';
        END IF;
        IF item.revision_id IS NOT NULL AND
            (item.draft_id IS DISTINCT FROM item.revision_draft OR item.branch_id IS DISTINCT FROM item.draft_branch
             OR item.draft_state IS DISTINCT FROM 'posted' OR item.period_id IS DISTINCT FROM item.revision_period
             OR item.entry_date IS DISTINCT FROM item.revision_date OR item.total_debit IS DISTINCT FROM item.revision_debit
             OR item.total_credit IS DISTINCT FROM item.revision_credit) THEN
            RAISE EXCEPTION 'Journal revision source mismatch' USING ERRCODE='23514';
        END IF;
        IF item.reverses_id IS NOT NULL AND
            (item.branch_id IS DISTINCT FROM item.original_branch OR item.original_reverses IS NOT NULL
             OR item.total_debit IS DISTINCT FROM item.original_credit OR item.total_credit IS DISTINCT FROM item.original_debit) THEN
            RAISE EXCEPTION 'Journal reversal source mismatch' USING ERRCODE='23514';
        END IF;
    END LOOP;
    RETURN NULL;
END $body$;
REVOKE ALL ON FUNCTION {schema}.finance_validate_journal() FROM PUBLIC;
CREATE CONSTRAINT TRIGGER finance_journal_header_balance AFTER INSERT OR UPDATE
ON {schema}.finance_journalentry DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION {schema}.finance_validate_journal();
CREATE CONSTRAINT TRIGGER finance_journal_line_balance AFTER INSERT OR UPDATE OR DELETE
ON {schema}.finance_journalline DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
EXECUTE FUNCTION {schema}.finance_validate_journal();
CREATE FUNCTION {schema}.finance_guard_period_void() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog AS $guard$
BEGIN
    IF OLD.state='void' AND NEW.state<>'void' THEN
        RAISE EXCEPTION 'Voided period is terminal' USING ERRCODE='23514';
    END IF;
    IF NEW.state='void' AND (EXISTS(SELECT 1 FROM {schema}.finance_journalrevision WHERE period_id=NEW.id)
        OR EXISTS(SELECT 1 FROM {schema}.finance_journalentry WHERE period_id=NEW.id)) THEN
        RAISE EXCEPTION 'Used period cannot be voided' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $guard$;
REVOKE ALL ON FUNCTION {schema}.finance_guard_period_void() FROM PUBLIC;
CREATE TRIGGER finance_period_usage_guard BEFORE UPDATE OF state ON {schema}.finance_accountingperiod
FOR EACH ROW EXECUTE FUNCTION {schema}.finance_guard_period_void();
CREATE FUNCTION {schema}.finance_guard_draft_state() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = pg_catalog AS $draft$
BEGIN
    IF TG_OP='INSERT' THEN
        IF NEW.state<>'draft' OR NEW.version<>1 THEN
            RAISE EXCEPTION 'Draft must start at version one' USING ERRCODE='23514';
        END IF;
        RETURN NEW;
    END IF;
    IF OLD.state<>'draft' OR NEW.version<>OLD.version+1 THEN
        RAISE EXCEPTION 'Terminal draft or invalid version transition' USING ERRCODE='23514';
    END IF;
    IF NEW.branch_id IS DISTINCT FROM OLD.branch_id THEN
        RAISE EXCEPTION 'Draft branch is immutable' USING ERRCODE='23514';
    END IF;
    IF (NEW.state='posted' AND NOT EXISTS(SELECT 1 FROM {schema}.finance_journalentry WHERE draft_id=NEW.id))
       OR (NEW.state='cancelled' AND EXISTS(SELECT 1 FROM {schema}.finance_journalentry WHERE draft_id=NEW.id)) THEN
        RAISE EXCEPTION 'Draft publication state mismatch' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $draft$;
REVOKE ALL ON FUNCTION {schema}.finance_guard_draft_state() FROM PUBLIC;
CREATE TRIGGER finance_draft_state_guard BEFORE INSERT OR UPDATE ON {schema}.finance_journaldraft
FOR EACH ROW EXECUTE FUNCTION {schema}.finance_guard_draft_state();
""")


def uninstall(apps, schema_editor):
    schema = schema_editor.quote_name(schema_editor.connection.schema_name)
    schema_editor.execute(f"""
DROP TRIGGER IF EXISTS finance_journal_line_balance ON {schema}.finance_journalline;
DROP TRIGGER IF EXISTS finance_journal_header_balance ON {schema}.finance_journalentry;
DROP FUNCTION IF EXISTS {schema}.finance_validate_journal();
DROP TRIGGER IF EXISTS finance_period_usage_guard ON {schema}.finance_accountingperiod;
DROP FUNCTION IF EXISTS {schema}.finance_guard_period_void();
DROP TRIGGER IF EXISTS finance_draft_state_guard ON {schema}.finance_journaldraft;
DROP FUNCTION IF EXISTS {schema}.finance_guard_draft_state();
""")


class Migration(migrations.Migration):
    dependencies = [("finance", "0003_journalcounter_journaldraft_journalentry_journalline_and_more")]
    operations = [migrations.RunPython(install, uninstall)]
