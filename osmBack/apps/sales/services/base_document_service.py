
def calculate_document_totals(document):
    items = document.items.all()
    document.subtotal = sum(item.total_price for item in items)
    document.tax_amount = document.subtotal * document.tax_rate
    document.total_amount = document.subtotal + document.tax_amount - document.discount_amount
    document.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])
