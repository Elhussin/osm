from django.utils.translation import get_language
from django.conf import settings
from .models import Page

def get_page_content(page):
    lang = get_language()  # مثل "ar" أو "en"
    return page.translations.filter(language=lang).first() or \
           page.translations.filter(language=settings.MODELTRANSLATION_DEFAULT_LANGUAGE).first()
