
USER_RELATED_FIELDS = [
    "role_id__name",
    "email",
    "phone",
    "username",
    "first_name",
    "last_name",
]
# # 👇 أسماء مخصصة لبعض الحقول
USER_FIELD_LABELS = {
    "role_id__name": "Role",
    "email": "Email",
    "phone": "Phone",
    "username": "Username",
    "first_name": "First Name",
    "last_name": "Last Name",

}


USER_FILTER_FIELDS = {
    "role_id__name": ["icontains"],
    "email": ["icontains"],
    "phone": ["icontains"],
    "username": ["icontains"],
    "first_name": ["icontains"],
    "last_name": ["icontains"],
}

