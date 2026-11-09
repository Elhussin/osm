from django.utils import timezone

def generate_serial_number(model, prefix, field_name='number', with_date=True):
    today_str = timezone.now().strftime('%Y%m%d') if with_date else ''
    serial_prefix = f"{prefix}-{today_str}" if with_date else prefix

    # جلب آخر رقم يبدأ بنفس البادئة
    filter_kwargs = {f"{field_name}__startswith": serial_prefix}
    last_obj = model.objects.filter(**filter_kwargs).order_by(f"-{field_name}").first()

    if last_obj:
        last_number_str = getattr(last_obj, field_name, '0')
        try:
            last_serial = int(last_number_str.split('-')[-1])
        except (ValueError, IndexError):
            last_serial = 0
    else:
        last_serial = 0

    new_serial = f"{serial_prefix}-{last_serial + 1:04d}"
    return new_serial



