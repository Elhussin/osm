from django.urls import path
from .views import live, ready
from identity import views as identity
from workspace import views as workspace
from clinical import views as clinical
from catalog import views as catalog
from inventory import views as inventory
from inventory import reservation_views, operation_views, label_views, tracking_views
from finance import views as finance
from finance import setup_views as accounting
from finance import journal_views as journals
from finance import report_views as reports
from sales import views as sales

urlpatterns = [
    path("sales/registers/", sales.registers, name="sales-registers"),
    path("sales/registers/new/", sales.register_new, name="sales-register-new"),
    path("sales/registers/<uuid:register_id>/", sales.register_detail, name="sales-register"),
    path("finance/reports/trial-balance/", reports.trial, name="finance-trial-balance"),
    path("finance/reports/ledger/", reports.ledger, name="finance-ledger"),
    path("finance/journals/", journals.journal_list, name="journal-drafts"),
    path("finance/journals/new/", journals.draft_edit, name="journal-new"),
    path("finance/journals/<uuid:draft_id>/", journals.draft_detail, name="journal-draft"),
    path("finance/journals/<uuid:draft_id>/edit/", journals.draft_edit, name="journal-edit"),
    path("finance/journals/<uuid:draft_id>/revisions/<int:version>/", journals.revision_detail, name="journal-revision"),
    path("finance/entries/", journals.entries, name="journal-entries"),
    path("finance/entries/<uuid:entry_id>/", journals.entry_detail, name="journal-entry"),
    path("finance/entries/<uuid:entry_id>/reverse/", journals.entry_reverse, name="journal-reverse"),
    path("finance/accounts/", accounting.accounts, name="finance-accounts"),
    path("finance/accounts/new/", accounting.account_new, name="finance-account-new"),
    path("finance/accounts/<uuid:account_id>/", accounting.account_detail, name="finance-account"),
    path("finance/periods/", accounting.periods, name="finance-periods"),
    path("finance/periods/new/", accounting.period_new, name="finance-period-new"),
    path("finance/periods/<uuid:period_id>/", accounting.period_detail, name="finance-period"),
    path("account/fiscal/", finance.fiscal_setup, name="fiscal-setup"),
    path("inventory/", tracking_views.home, name="inventory-home"),
    path("inventory/receiving/", tracking_views.receiving_catalog, name="stock-receiving-catalog"),
    path("inventory/receiving/<uuid:variant_id>/", tracking_views.receiving, name="stock-receive"),
    path("inventory/positions/", tracking_views.positions, name="stock-positions"),
    path("inventory/positions/<uuid:position_id>/<str:action>/", tracking_views.position_action, name="stock-position-action"),
    path("inventory/trace/", tracking_views.trace, name="stock-trace"),
    path("catalog/variants/<uuid:variant_id>/labels/", label_views.labels, name="variant-labels"),
    path("inventory/operations/", operation_views.operation_list, name="stock-operations"),
    path("inventory/operations/new/<int:balance_id>/<str:kind>/", operation_views.operation_new, name="stock-operation-new"),
    path("inventory/operations/<uuid:operation_id>/", operation_views.operation_detail, name="stock-operation"),
    path("inventory/reservations/", reservation_views.reservations, name="stock-reservations"),
    path("inventory/reservations/<uuid:reservation_id>/", reservation_views.reservation_detail, name="stock-reservation"),
    path("inventory/lenses/", inventory.lens_products, name="inventory-lenses"),
    path("inventory/lenses/<uuid:product_id>/", inventory.lens_matrix, name="lens-matrix"),
    path("inventory/receipts/confirm/", inventory.confirm_receipt, name="matrix-confirm"),
    path("inventory/receipts/<uuid:receipt_id>/", inventory.receipt_detail, name="stock-receipt"),
    path("catalog/", catalog.products, name="catalog-products"),
    path("catalog/new/", catalog.product_new, name="product-new"),
    path("catalog/products/<uuid:product_id>/", catalog.product_detail, name="product-detail"),
    path("catalog/products/<uuid:product_id>/edit/", catalog.product_edit, name="product-edit"),
    path("catalog/products/<uuid:product_id>/variants/new/", catalog.variant_new, name="variant-new"),
    path("catalog/variants/<uuid:variant_id>/", catalog.variant_detail, name="variant-detail"),
    path("catalog/variants/<uuid:variant_id>/edit/", catalog.variant_edit, name="variant-edit"),
    path("catalog/variants/<uuid:variant_id>/prices/new/", catalog.rule_new, name="price-rule-new"),
    path("catalog/prices/<uuid:rule_id>/disable/", catalog.rule_disable, name="price-rule-disable"),
    path("catalog/variants/<uuid:variant_id>/quote/", catalog.price_preview, name="price-preview"),
    path("customers/", clinical.customers, name="customers"),
    path("customers/new/", clinical.customer_new, name="customer-new"),
    path("customers/<uuid:customer_id>/", clinical.customer_detail, name="customer-detail"),
    path("customers/<uuid:customer_id>/edit/", clinical.customer_edit, name="customer-edit"),
    path("customers/<uuid:customer_id>/share/", clinical.customer_share, name="customer-share"),
    path("customers/<uuid:customer_id>/prescriptions/new/", clinical.prescription_new, name="prescription-new"),
    path("prescriptions/<uuid:prescription_id>/correct/", clinical.prescription_correct, name="prescription-correct"),
    path("prescriptions/<uuid:prescription_id>/v/<int:version>/", clinical.prescription_detail, name="prescription-detail"),
    path("prescriptions/<uuid:prescription_id>/v/<int:version>/image/", clinical.exam_image, name="exam-image"),
    path("health/live/", live), path("health/ready/", ready),
    path("auth/login/", identity.sign_in, name="login"),
    path("auth/logout/", identity.sign_out, name="logout"),
    path("auth/recovery/", identity.recovery, name="recovery"),
    path("auth/link/<str:purpose>/", identity.password_link, name="password-link"),
    path("", workspace.overview),
    path("account/", workspace.overview, name="account-home"),
    path("account/branches/", workspace.branches, name="account-branches"),
    path("account/branches/new/", workspace.branch_form, name="branch-new"),
    path("account/branches/<uuid:branch_id>/", workspace.branch_form, name="branch-edit"),
    path("account/branches/<uuid:branch_id>/state/", workspace.branch_state, name="branch-state"),
    path("account/branch/", identity.switch_branch, name="switch-branch"),
    path("account/audit/", workspace.events, name="account-audit"),
    path("account/members/", workspace.members, name="members"),
    path("account/members/invite/", workspace.invite, name="invite-member"),
    path("account/members/<uuid:member_id>/", workspace.member_detail, name="member-detail"),
    path("account/members/<uuid:member_id>/state/", workspace.member_state, name="member-state"),
    path("account/members/<uuid:member_id>/roles/", workspace.member_role, name="member-role"),
    path("account/members/<uuid:member_id>/roles/<int:assignment_id>/revoke/", workspace.revoke_assignment, name="revoke-assignment"),
    path("account/members/<uuid:member_id>/access/", workspace.member_branch_access, name="member-access"),
    path("account/members/<uuid:member_id>/send/<str:purpose>/", workspace.resend_link, name="resend-link"),
    path("account/roles/", workspace.roles, name="roles"),
    path("account/ownership/", workspace.ownership, name="ownership"),
]

handler403 = workspace.error_page
handler400 = lambda request, exception: workspace.error_page(request, exception, status=400)
handler404 = lambda request, exception: workspace.error_page(request, exception, status=404)
handler500 = lambda request: workspace.error_page(request, status=500)
