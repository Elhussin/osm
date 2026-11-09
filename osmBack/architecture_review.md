# Architecture & Code Review

## Executive Summary
The codebase follows a standard Django multi-tenancy pattern using `django-tenants`. The foundation is solid, but there are **critical bugs** preventing execution and **security risks** regarding password handling. Additionally, the configuration of the `users` app in both Shared and Tenant contexts requires attention to avoid database inconsistencies.

---

## 🚨 Critical Issues (Must Fix)

### 1. Syntax Error in `PendingTenantRequest`
**File:** `apps/tenants/models.py` (Line 67)
The `save` method attempts to query a model using a string literal, which will raise an `AttributeError`.
```python
# ❌ INCORRECT (Will Crash)
self.plan = "SubscriptionPlan".objects.get(name="trial")

# ✅ CORRECT
from django.apps import apps
SubscriptionPlan = apps.get_model('tenants', 'SubscriptionPlan')
self.plan = SubscriptionPlan.objects.get(name="trial")
# OR if class is in same file and defined above:
self.plan = SubscriptionPlan.objects.get(name="trial")
```

### 2. Security: Raw Password Storage
**File:** `apps/tenants/models.py` & `apps/tenants/serializers.py`
The `PendingTenantRequest` model stores user passwords in **plain text**.
- `RegisterTenantSerializer` passes the raw password to `PendingTenantRequest.objects.create`.
- If the database is compromised, all pending user passwords are leaked.
- **Fix:** Hash the password before saving, or use a temporary token flow without storing the password (ask user to set password upon activation).

### 3. Hardcoded "Trial" Plan
**File:** `apps/tenants/models.py`
The code heavily relies on a plan named "trial" existing in the database.
```python
SubscriptionPlan.objects.get(name="trial")
```
If this plan is renamed or deleted, signups will fail. 
**Recommendation:** Add a `is_default` boolean field to `SubscriptionPlan` or use a const setting, handled clearly in a `get_or_create` logic.

### 4. Ambiguous User App Placement
**File:** `settings/base.py`
`apps.users` is listed in **BOTH** `SHARED_APPS` and `TENANT_APPS`.
- This creates two tables: `public.users_user` and `tenant_schema.users_user`.
- Since `AUTH_USER_MODEL = 'users.User'`, Django may get confused about which table to use depending on context.
- **Recommendation:** 
    - If users are global (login once, access multiple tenants), keep in `SHARED_APPS` only.
    - If users are isolated (separate accounts per tenant), keep in `TENANT_APPS` only.
    - **Current Code implication:** The `User` model has `client` FK. This suggests users belong to a specific tenant. If so, they should be well-defined. If `User` is in `TENANT_APPS`, the `client` FK is redundant (the schema *is* the tenant). If `User` is in `SHARED_APPS`, the `client` FK makes sense.

---

## 🏗 Architecture & Design

### 1. User Model Foreign Keys
**File:** `apps/users/models.py`
```python
role_id = models.ForeignKey("Role", ...)
client = models.ForeignKey('tenants.Client', ...)
```
- **Naming Convention:** In Django models, `ForeignKey` fields should not have `_id` suffix. Django automatically creates the column `role_id_id`.
    - Rename `role_id` -> `role`.
    - Rename `author_id` -> `author` (in `Page` model).
- **Client FK:** As noted above, if `User` is in the tenant schema, linking to `Client` (which is in public) is fine, but usually unnecessary as the user is *inside* that client's data silo. If `User` is public, this design limits a user to exactly one tenant.

### 2. RBAC (Role Based Access Control)
The custom `Role` and `Permission` models are a good start. 
- **Recommendation:** Ensure standard Django `has_perm` checks utilize these custom roles. You might need a custom Authentication Backend to bridge `user.has_perm('app.action')` to your `RolePermission` table.

### 3. Tenant Settings
**File:** `apps/users/models.py`
The `TenantSettings` model seems to mix configuration (SEO, Socials) with Tenant identity.
- **Observation:** This model should definitely reside in the `TENANT_APPS` and be a singleton (one row per tenant).
- **Location:** It is currently in `apps/users`. It might be better placed in `apps/tenants` (if tenant specific but public) or `apps/core` (if inside tenant schema). Given the fields (Business name, etc), it looks like "Tenant Profile" data.

---

## 🔍 Code Quality & Minor Observations

1.  **Typos:**
    - `settings/base.py`: `CURANCY` (should be `CURRENCY`).
    - `apps/tenants/models.py`: `paymant_logger` (should be `payment_logger`).
    - `apps/tenants/models.py`: Docstring "Plane Subscription".

2.  **PendingTenantRequest Logic:**
    - `clean()` validates `schema_name` is alphanumeric. Good.
    - `save()` logic overrides `plan` passed during creation with "trial". This ignores the `plan` stored in `PendingTenantRequest` if it was set during create.

3.  **Serializer Validation:**
    - `CreatePaymentOrderSerializer` validates `client.is_active`. This is good practice.

## ✅ Recommendations Summary
1.  **Fix key bugs** in `apps/tenants/models.py` immediately.
2.  **Review the `apps.users` placement** in `settings.py`. Decide on Shared vs Isolated users.
3.  **Rename model fields** (`role_id` -> `role`) for cleaner code.
4.  **Implement password hashing** for `PendingTenantRequest`.
