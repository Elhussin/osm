# core/utils/options_builder.py

def build_choices_from_queryset(queryset, label_field="name", value_field="id"):
    """
    يبني خيارات من أي Queryset على شكل [{"label": ..., "value": ...}]
    """
    return [
        {
            "label": getattr(obj, label_field),
            "value": getattr(obj, value_field)
        }
        for obj in queryset
    ]

def build_choices_from_list(choices):
    """
    يبني خيارات من قائمة choices [(value, label), ...]
    """
    return [
        {"label": label, "value": value}
        for value, label in choices
    ]
