from copy import deepcopy
from decimal import Decimal, localcontext
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from sales.amounts import calculate_document, net_line_amount, rounded, allocate_cents, discount
from sales.tax_codes import treatment


def line(price="115", **changes):
    return dict(quantity=1, unit_amount=price, price_basis="gross", tax=treatment("S"), discount_kind="amount", discount_value="0") | changes


class RetailAmountsTests(SimpleTestCase):
    def test_official_net_line_examples_and_half_up(self):
        self.assertEqual(net_line_amount("400", 10, base_quantity=2), Decimal("2000"))
        self.assertEqual(net_line_amount("100", 10, allowance="100", charge="25"), Decimal("925"))
        self.assertEqual(rounded(Decimal("123.4949")), Decimal("123.49"))
        self.assertEqual(rounded(Decimal("123.4951")), Decimal("123.50"))

    def test_final_price_and_explicit_net_catalog_conversion(self):
        gross = calculate_document([line()])
        net = calculate_document([line("100", price_basis="catalog_net")])
        self.assertEqual(gross["totals"], net["totals"])
        self.assertEqual((gross["totals"]["net"], gross["totals"]["vat"], gross["totals"]["payable"]), ("100.00", "15.00", "115.00"))

    def test_line_then_order_discount_and_immutable_inputs(self):
        rows = [line(quantity=2, discount_kind="percent", discount_value="10"), line("230")]
        original = deepcopy(rows)
        result = calculate_document(rows, document_discount_kind="percent", document_discount_value="10")
        self.assertEqual(rows, original)
        totals = result["totals"]
        self.assertEqual((totals["original_gross"], totals["line_discount_gross"], totals["document_discount_gross"], totals["payable"]), ("460.00", "23.00", "43.70", "393.30"))
        self.assertEqual((totals["net"], totals["vat"]), ("342.00", "51.30"))
        self.assertEqual([r["document_discount_gross"] for r in result["rows"]], ["20.70", "23.00"])

    def test_largest_remainder_conserves_cents_and_ties_by_position(self):
        self.assertEqual(allocate_cents(Decimal("0.02"), [Decimal("1")] * 3), [Decimal(".01"), Decimal(".01"), Decimal("0")])
        self.assertEqual(allocate_cents(Decimal("0"), [Decimal("0")] * 2), [Decimal("0")] * 2)
        with self.assertRaises(ValidationError):
            allocate_cents(Decimal(".01"), [Decimal("0")])

    def test_group_tax_is_not_sum_of_rounded_line_taxes(self):
        result = calculate_document([line("0.03", price_basis="catalog_net")] * 2)
        self.assertEqual([r["line_vat"] for r in result["rows"]], ["0.00", "0.00"])
        self.assertEqual(result["totals"]["vat"], "0.01")
        self.assertEqual(result["totals"]["payable_rounding"], "-0.01")

    def test_explicit_rounding_and_unsupported_basket_rejected(self):
        result = calculate_document([line("0.04")])
        self.assertEqual((result["totals"]["net"], result["totals"]["vat"], result["totals"]["payable_rounding"]), ("0.03", "0.00", "0.01"))
        with self.assertRaises(ValidationError):
            calculate_document([line("0.04")] * 20)

    def test_tax_categories_and_order_allowance_breakdown(self):
        result = calculate_document([line(), line("100", tax=treatment("Z", "VATEX-SA-32"))], document_discount_value="21.50")
        self.assertEqual([(g["category"], g["taxable"], g["tax"]) for g in result["vat_breakdown"]], [("S", "90.00", "13.50"), ("Z", "90.00", "0.00")])
        self.assertEqual(result["totals"]["payable"], "193.50")
        exempt = calculate_document([line("100", tax=treatment("E", "VATEX-SA-29"))])
        self.assertEqual(exempt["totals"]["vat"], "0.00")
        outside = line("100", tax=treatment("O", "VATEX-SA-OOS", "Synthetic outside-scope basis"))
        self.assertEqual(calculate_document([outside])["totals"]["payable"], "100.00")
        with self.assertRaises(ValidationError):
            calculate_document([outside, line()], document_discount_value="1")
        with self.assertRaises(ValidationError):
            calculate_document([outside, line("1", tax=treatment("O", "VATEX-SA-OOS", "Different basis"))])

    def test_registration_and_classification_never_inferred(self):
        result = calculate_document([line(tax=None)], seller_registered=False)
        self.assertEqual((result["totals"]["vat"], result["vat_breakdown"], result["rows"][0]["tax"]["category"]), ("0.00", [], None))
        for rows, registered in (([line(tax=None)], True), ([line()], False)):
            with self.assertRaises(ValidationError):
                calculate_document(rows, seller_registered=registered)
        for args in (("S", "VATEX-SA-29"), ("Z", "VATEX-SA-29"), ("O", "VATEX-SA-O"), ("Z", "VATEX-SA-HEA"), ("Z", "VATEX-SA-EDU"), ("Z", "VATEX-SA-MLTRY")):
            with self.assertRaises(ValidationError):
                treatment(*args)

    def test_zero_full_discount_and_input_boundaries(self):
        for row in (line("0"), line(discount_kind="percent", discount_value="100")):
            self.assertEqual(calculate_document([row])["totals"]["payable"], "0.00")
        for value in (True, 1.1, "NaN", "Infinity", "-1", "1.001", "1e2", "10000000000"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                calculate_document([line(value)])
        for value in (True, "1", 0, -1, 1000001):
            with self.assertRaises(ValidationError):
                calculate_document([line(quantity=value)])
        for rows in ([], [line()] * 41, None, [{"quantity": 1}]):
            with self.assertRaises(ValidationError):
                calculate_document(rows)
        for change in ({"discount_value": "116"}, {"discount_kind": "percent", "discount_value": "100.01"}, {"tax": treatment("S") | {"rate": "5.00"}}):
            with self.assertRaises(ValidationError):
                calculate_document([line(**change)])

    def test_context_precision_and_rounding_cannot_change_results(self):
        expected = calculate_document([line("9999999999.99", quantity=1000000)])
        with localcontext() as ctx:
            ctx.prec = 6
            self.assertEqual(calculate_document([line("9999999999.99", quantity=1000000)]), expected)
            self.assertEqual(discount("123456789.00", "percent", "10"), Decimal("12345678.90"))
            self.assertEqual(sum(allocate_cents("100.00", ["200.00", "300.00"])), Decimal("100"))
        with self.assertRaises(ValidationError):
            calculate_document([line("9999999999.99", quantity=1000000)] * 2)
