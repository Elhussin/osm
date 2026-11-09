from django.db import connection
from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "alive"})


def database_ready():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        return cursor.fetchone() == (1,)


def ready(request):
    try:
        if not database_ready():
            raise RuntimeError("Readiness query failed")
    except Exception:
        # Do not expose connection settings or raw exceptions to callers.
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})
