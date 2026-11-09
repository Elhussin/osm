from django.utils.timezone import now
from django.http import JsonResponse
from django.urls import reverse
from apps.tenants.models import Client

class PlanValidationMiddleware:
    """
    يتحقق من صلاحية الخطة (نشطة / انتهت) لكل تينانت
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = getattr(request, "tenant", None)

        if tenant and tenant.schema_name != "public":
            # استثناء بعض المسارات (مثل الدفع أو تسجيل الدخول)
            # exempt_paths = [
            #     reverse("tenants:upgrade"),
            #     reverse("users:login"),
            #     reverse("users:logout"),
            # ]
            # if any(request.path.startswith(path) for path in exempt_paths):
            #     return self.get_response(request)

            # نقرأ بيانات الخطة من public schema
            try:
                client = Client.objects.get(schema_name=tenant.schema_name)
            except Client.DoesNotExist:
                return JsonResponse({"error": "Tenant not found."}, status=404)

            # تحقق من حالة التفعيل
            if not client.is_active:
                return JsonResponse({"error": "Your account is inactive."}, status=403)

            # تحقق من انتهاء الخطة
            if client.is_plan_expired:
                return JsonResponse({"error": "Your subscription plan has expired."}, status=403)

        return self.get_response(request)
