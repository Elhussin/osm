from django.utils import translation

class CustomLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # الأولوية: Header > Cookie > Default
        lang = request.headers.get('Accept-Language') or request.COOKIES.get('language') or 'en'
        translation.activate(lang)
        request.LANGUAGE_CODE = lang

        response = self.get_response(request)

        translation.deactivate()
        return response
