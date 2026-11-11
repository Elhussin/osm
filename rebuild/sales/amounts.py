"""Exact retail arithmetic. See ADR0020 and zatca/CALCULATION_RULES.md."""
from decimal import Decimal, localcontext, ROUND_HALF_UP, InvalidOperation
from django.core.exceptions import ValidationError
from finance.journal_money import amount, MAX_MONEY
from .tax_codes import treatment

CENT = Decimal("0.01")
UNIT_MAX = Decimal("9999999999.99")
ENGINE_VERSION = "retail-tax-1"


def rounded(value):
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValidationError("الحساب الداخلي يحتاج Decimal محدودًا.")
    with localcontext() as ctx:
        ctx.prec = 50
        try:
            return value.quantize(CENT, rounding=ROUND_HALF_UP)
        except InvalidOperation:
            raise ValidationError("المبلغ خارج سعة الحساب.") from None


def _limit(value):
    if not 0 <= value <= MAX_MONEY:
        raise ValidationError("مجموع المبلغ يتجاوز سعة المعاينة.")
    return value


def _quantity(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 1000000:
        raise ValidationError("الكمية عدد صحيح بين1 و1000000 بوحدة الصنف.")
    return value


def net_line_amount(unit_net, quantity, *, base_quantity=1, allowance="0", charge="0"):
    unit, count, base = amount(unit_net), _quantity(quantity), _quantity(base_quantity)
    with localcontext() as ctx:
        ctx.prec = 50
        return _limit(rounded(unit * count / base) - amount(allowance) + amount(charge))


def discount(base, kind, value):
    with localcontext() as ctx:
        ctx.prec = 50
        return _discount(base, kind, value)


def _discount(base, kind, value):
    base = amount(base)
    value = amount(value)
    if kind == "amount":
        result = value
    elif kind == "percent" and value <= 100:
        result = rounded(base * value / 100)
    else:
        raise ValidationError("الخصم مبلغ أو نسبة لا تتجاوز100%.")
    if result > base:
        raise ValidationError("الخصم يتجاوز المبلغ المتاح.")
    return result


def allocate_cents(value, weights):
    """Largest remainder, with line position as the stable tie breaker."""
    with localcontext() as ctx:
        ctx.prec = 50
        return _allocate_cents(amount(value), [amount(weight) for weight in weights])


def _allocate_cents(value, weights):
    if value > sum(weights):
        raise ValidationError("الخصم يتجاوز المبلغ المتاح.")
    cents = int(value * 100)
    units = [int(weight * 100) for weight in weights]
    total = sum(units)
    if not total:
        if cents:
            raise ValidationError("لا يمكن توزيع الخصم على بنود صفرية.")
        return [Decimal("0.00")] * len(weights)
    parts = [divmod(cents * unit, total) for unit in units]
    result = [part[0] for part in parts]
    for index in sorted(range(len(parts)), key=lambda i: (-parts[i][1], i))[:cents-sum(result)]:
        result[index] += 1
    return [Decimal(value) / 100 for value in result]


def calculate_document(lines, *, document_discount_kind="amount", document_discount_value="0", seller_registered=True):
    if not isinstance(lines, list) or not 1 <= len(lines) <= 40 or type(seller_registered) is not bool:
        raise ValidationError("المعاينة تحتاج1–40 بندًا وحالة تسجيل صريحة.")
    with localcontext() as ctx:
        ctx.prec = 50
        rows = []
        for position, item in enumerate(lines, 1):
            if not isinstance(item, dict) or set(item) != {"quantity", "unit_amount", "price_basis", "tax", "discount_kind", "discount_value"}:
                raise ValidationError("حقول بند الحساب غير معروفة أو ناقصة.")
            count, unit = _quantity(item["quantity"]), amount(item["unit_amount"])
            if unit > UNIT_MAX or not isinstance(item["price_basis"], str) or item["price_basis"] not in {"gross", "catalog_net"}:
                raise ValidationError("سعر الوحدة أو أساسه غير صالح.")
            if seller_registered:
                tax = item["tax"]
                if not isinstance(tax, dict) or set(tax) != {"category", "rate", "reason_code", "reason_text"}:
                    raise ValidationError("لا حساب VAT بتصنيف مجهول.")
                canonical = treatment(tax["category"], tax["reason_code"], tax["reason_text"])
                if canonical != tax:
                    raise ValidationError("المعدل أو السبب لا يطابق التصنيف.")
            else:
                if item["tax"] is not None:
                    raise ValidationError("غير المسجل لا يحمل تصنيف VAT مفترضًا.")
                tax = {"category": None, "rate": "0.00", "reason_code": "", "reason_text": ""}
            rate = Decimal(tax["rate"])
            factor = 1 + rate / 100
            net_unit = unit / factor if item["price_basis"] == "gross" else unit
            base_net = _limit(rounded(net_unit * count))
            original = _limit(unit * count if item["price_basis"] == "gross" else rounded(base_net * factor))
            line_discount = discount(original, item["discount_kind"], item["discount_value"])
            after_line = original - line_discount
            line_net = base_net if not line_discount else rounded(after_line / factor)
            rows.append({"position": position, "quantity": count, "input_unit": unit, "price_basis": item["price_basis"], "tax": tax,
                "net_unit_price": net_unit.quantize(Decimal("0.000000000001"), rounding=ROUND_HALF_UP), "original_gross": original,
                "line_discount_gross": line_discount, "line_allowance_net": base_net-line_net,
                "after_line_discount_gross": after_line, "line_net": line_net})
        total_original = _limit(sum(row["original_gross"] for row in rows))
        remaining = _limit(sum(row["after_line_discount_gross"] for row in rows))
        doc_discount = discount(remaining, document_discount_kind, document_discount_value)
        categories = {row["tax"]["category"] for row in rows}
        if doc_discount and "O" in categories and len(categories) > 1:
            raise ValidationError("خصم المستند لا يخلط O مع فئات أخرى في هذا المسار؛ راجع الفصل بين المعاملات.")
        portions = allocate_cents(doc_discount, [row["after_line_discount_gross"] for row in rows])
        groups = {}
        for row, portion in zip(rows, portions):
            rate = Decimal(row["tax"]["rate"])
            final_gross = row["after_line_discount_gross"] - portion
            final_net = row["line_net"] if not portion else rounded(final_gross / (1 + rate / 100))
            row.update(document_discount_gross=portion, document_allowance_net=row["line_net"]-final_net,
                taxable_net=final_net, requested_gross=final_gross, line_vat=rounded(row["line_net"]*rate/100))
            row["line_with_vat"] = row["line_net"] + row["line_vat"]
            key = (row["tax"]["category"], row["tax"]["rate"])
            if key not in groups:
                groups[key] = {**row["tax"], "taxable": Decimal("0.00"), "tax": Decimal("0.00")}
            group = groups[key]
            if (group["reason_code"], group["reason_text"]) != (row["tax"]["reason_code"], row["tax"]["reason_text"]):
                raise ValidationError("أسباب مختلفة لفئة ومعدل واحد؛ لا يمكن إسقاط أحدها في تجميع المعاينة.")
            group["taxable"] += final_net
        for group in groups.values():
            group["tax"] = rounded(group["taxable"] * Decimal(group["rate"]) / 100)
        line_total = _limit(sum(row["line_net"] for row in rows))
        allowance_total = _limit(sum(row["document_allowance_net"] for row in rows))
        net = _limit(line_total - allowance_total)
        vat = _limit(sum(group["tax"] for group in groups.values()))
        inclusive = _limit(net + vat)
        target = remaining - doc_discount
        rounding = target - inclusive
        if abs(rounding) > CENT:
            raise ValidationError("فرق التقريب يتجاوز هللة واحدة؛ راجع البنود قبل استخدام هذه المعاينة.")
        totals = dict(original_gross=total_original, line_discount_gross=total_original-remaining, document_discount_gross=doc_discount,
            line_net_total=line_total, document_allowance_net=allowance_total, net=net, vat=vat,
            tax_inclusive=inclusive, payable_rounding=rounding, payable=inclusive+rounding)
        def serial(value):
            if isinstance(value, Decimal):
                return format(value, "f") if value.as_tuple().exponent < -2 else format(value, ".2f")
            if isinstance(value, dict):
                return {key: serial(item) for key, item in value.items()}
            if isinstance(value, list):
                return [serial(item) for item in value]
            return value
        return serial({"engine_version": ENGINE_VERSION, "seller_registered": seller_registered, "rows": rows,
            "vat_breakdown": list(groups.values()) if seller_registered else [], "totals": totals})
