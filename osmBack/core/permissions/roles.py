# core/permissions/roles.py
from enum import Enum

class Role(Enum):
    ADMIN = 'admin'  # All permissions
    BRANCH_MANAGER = 'branch_manager'  # Branch permissions
    TECHNICIAN = 'technician'  # Product permissions
    SALESPERSON = 'salesperson'  # Invoice permissions
    ACCOUNTANT = 'accountant'  # Payment permissions
    INVENTORY_MANAGER = 'inventory_manager'  # Inventory permissions
    RECEPTIONIST = 'receptionist'  # Appointment permissions
    CRM = 'crm'  # Customer permissions
    CUSTOMER = 'customer'  # Individual customer permissions
