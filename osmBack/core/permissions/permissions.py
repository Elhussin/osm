# core/permissions/permissions.py
from .roles import Role

ROLE_PERMISSIONS = {
    Role.ADMIN: '__all__',

    Role.BRANCH_MANAGER: [
        'view_branch',
        'manage_employees',
        'view_sales',
    ],
    Role.TECHNICIAN: [
        'create_prescription',
        'edit_prescription',
        'view_customer',
    ],
    Role.SALESPERSON: [
        'create_invoice',
        'view_products',
        'create_order',
    ],
    Role.ACCOUNTANT: [
        'view_invoice',
        'manage_payments',
        'view_reports',
    ],
    Role.INVENTORY_MANAGER: [
        'view_inventory',
        'edit_inventory',
        'stock_transfer',
    ],
    Role.RECEPTIONIST: [
        'create_appointment',
        'view_customer',
    ],
    Role.CRM: [
        'view_customer',
        'follow_up',
    ],
    Role.CUSTOMER: [
        'view_customer',
    ],
}
