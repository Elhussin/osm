"""Read-only ledger projections. Each numeric report uses one PostgreSQL snapshot."""
from datetime import date
from decimal import Decimal, localcontext
import uuid
import json
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection
from access.authorization import require, visible_branches
from .models import Account, JournalEntry, JournalLine


ZERO = Decimal("0.00")


def report_scope(actor_id, starts_on, ends_on, branch_id=None):
    require(actor_id, "ledger.read")
    try:
        start = date.fromisoformat(str(starts_on))
        end = date.fromisoformat(str(ends_on))
    except (ValueError, TypeError):
        raise ValidationError("حدد تاريخ بداية ونهاية صالحين.") from None
    if start > end:
        raise ValidationError("نهاية المدة تسبق بدايتها.")
    branches = list(visible_branches(actor_id, "ledger.read").values_list("pk", flat=True))
    if branch_id:
        try:
            selected = uuid.UUID(str(branch_id))
        except (ValueError, TypeError, AttributeError):
            raise PermissionDenied from None
        if selected not in branches:
            raise PermissionDenied
        branches = [selected]
    return start, end, branches


def _query(sql, parameters):
    with connection.cursor() as cursor:
        cursor.execute(sql, parameters)
        names = [column[0] for column in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]


def _tables():
    # Only model metadata supplies identifiers; user input is always parameterized.
    return tuple(connection.ops.quote_name(model._meta.db_table) for model in (JournalEntry, JournalLine, Account))


def trial_balance(actor_id, *, starts_on, ends_on, branch_id=None):
    start, end, branches = report_scope(actor_id, starts_on, ends_on, branch_id)
    entries, lines, accounts = _tables()
    records = _query(f"""
        WITH selected AS (
            SELECT * FROM {entries} WHERE branch_id = ANY(%s::uuid[]) AND entry_date <= %s
        ), scoped AS (
            SELECT l.*, e.entry_date FROM {lines} l JOIN selected e ON e.id=l.entry_id
        ), balances AS (
            SELECT a.id, a.code, a.name, a.active, a.normal_side,
                COALESCE(SUM(l.debit-l.credit) FILTER (WHERE l.entry_date < %s),0) AS opening,
                COALESCE(SUM(l.debit) FILTER (WHERE l.entry_date >= %s),0) AS debit,
                COALESCE(SUM(l.credit) FILTER (WHERE l.entry_date >= %s),0) AS credit,
                SUM(l.debit-l.credit) AS closing, COUNT(*) AS activity
            FROM scoped l JOIN {accounts} a ON a.id=l.account_id
            GROUP BY a.id, a.code, a.name, a.active, a.normal_side
        ), heads AS (
            SELECT COUNT(*) AS entry_count, COALESCE(SUM(total_debit),0) AS header_debit,
                COALESCE(SUM(total_credit),0) AS header_credit FROM selected WHERE entry_date >= %s
        ), totals AS (
            SELECT COALESCE(SUM(opening),0) AS opening_net, COALESCE(SUM(debit),0) AS total_debit,
                COALESCE(SUM(credit),0) AS total_credit, COALESCE(SUM(closing),0) AS closing_net,
                COALESCE(SUM(GREATEST(opening,0)),0) AS opening_debit,
                COALESCE(SUM(GREATEST(-opening,0)),0) AS opening_credit,
                COALESCE(SUM(GREATEST(closing,0)),0) AS closing_debit,
                COALESCE(SUM(GREATEST(-closing,0)),0) AS closing_credit FROM balances
        ) SELECT heads.*, totals.*, balances.* FROM heads CROSS JOIN totals
          LEFT JOIN balances ON TRUE ORDER BY balances.code
    """, [branches, end, start, start, start, start])
    summary_keys = ("entry_count", "header_debit", "header_credit", "opening_net", "total_debit", "total_credit", "closing_net", "opening_debit", "opening_credit", "closing_debit", "closing_credit")
    summary = {key: records[0][key] for key in summary_keys}
    with localcontext() as ctx:
        ctx.prec = 60
        summary["debit_difference"] = summary["header_debit"] - summary["total_debit"]
        summary["credit_difference"] = summary["header_credit"] - summary["total_credit"]
        summary["balanced"] = all(summary[key] == ZERO for key in ("opening_net", "closing_net", "debit_difference", "credit_difference")) and summary["total_debit"] == summary["total_credit"]
        rows = []
        for record in records:
            if record["id"] is None:
                continue
            row = {key: value for key, value in record.items() if key not in summary_keys}
            for source in ("opening", "closing"):
                row[source + "_debit"] = max(row[source], ZERO)
                row[source + "_credit"] = max(-row[source], ZERO)
            rows.append(row)
    return {"rows": rows, "summary": summary, "starts_on": start, "ends_on": end}


def account_ledger(actor_id, *, account_code, starts_on, ends_on, branch_id=None, page=1):
    start, end, branches = report_scope(actor_id, starts_on, ends_on, branch_id)
    account = Account.objects.filter(code=str(account_code).strip().upper(), is_group=False).first()
    if account is None:
        raise ValidationError("رمز حساب الترحيل غير متاح.")
    try:
        requested_page = max(1, min(int(page), 1000000000))
    except (ValueError, TypeError):
        requested_page = 1
    entries, lines, _ = _tables()
    records = _query(f"""
        WITH scoped AS (
            SELECT l.id, l.position, l.debit, l.credit, l.description AS line_description,
                l.account_snapshot, e.id AS entry_id, e.number, e.entry_date, e.reference,
                e.description, e.reverses_id
            FROM {lines} l JOIN {entries} e ON e.id=l.entry_id
            WHERE e.branch_id = ANY(%s::uuid[]) AND e.entry_date <= %s AND l.account_id=%s
        ), meta AS (
            SELECT COALESCE(SUM(debit-credit) FILTER (WHERE entry_date < %s),0) AS opening,
                COALESCE(SUM(debit) FILTER (WHERE entry_date >= %s),0) AS total_debit,
                COALESCE(SUM(credit) FILTER (WHERE entry_date >= %s),0) AS total_credit,
                COALESCE(SUM(debit-credit),0) AS closing,
                COUNT(*) FILTER (WHERE entry_date >= %s) AS movement_count FROM scoped
        ), movement AS (
            SELECT scoped.*, ROW_NUMBER() OVER w AS row_number,
                SUM(debit-credit) OVER w AS running_change
            FROM scoped WHERE entry_date >= %s
            WINDOW w AS (ORDER BY entry_date, number, position ROWS UNBOUNDED PRECEDING)
        ), bounds AS (
            SELECT meta.*, GREATEST(1, (movement_count+19)/20) AS pages FROM meta
        ) SELECT bounds.*, movement.* FROM bounds LEFT JOIN movement ON
            movement.row_number > (LEAST(%s, pages)-1)*20 AND
            movement.row_number <= LEAST(%s, pages)*20 ORDER BY movement.row_number
    """, [branches, end, account.pk, start, start, start, start, start, requested_page, requested_page])
    keys = ("opening", "total_debit", "total_credit", "closing", "movement_count", "pages")
    summary = {key: records[0][key] for key in keys}
    rows = []
    with localcontext() as ctx:
        ctx.prec = 60
        for record in records:
            if record["id"] is not None:
                if isinstance(record["account_snapshot"], str):
                    record["account_snapshot"] = json.loads(record["account_snapshot"])
                record["balance"] = summary["opening"] + record["running_change"]
                record["display_number"] = f'JE-{record["number"]:08d}'
                rows.append(record)
    return {"account": account, "rows": rows, "summary": summary, "page_number": min(requested_page, summary["pages"]), "starts_on": start, "ends_on": end}
