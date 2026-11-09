from contextvars import ContextVar

# Per request/task only; never a tenant selector or source of authorization.
audit_request_id = ContextVar("audit_request_id", default=None)
