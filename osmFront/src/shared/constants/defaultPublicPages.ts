import { DefaultPublicPage } from '@/src/features/pages/types';

export const defaultPublicPages: Record<string, DefaultPublicPage> = {
    about: {
        default_language: 'en',
        translations: [
          {
            language: 'en',
            title: 'About Us',
            content: 'Learn more about our company and values.',
            seo_title: 'About Us - Company Name',
            meta_description: 'Discover our mission and vision.',
            meta_keywords: 'about, company, values',
          },
          {
            language: 'ar',
            title: 'معلومات عنا',
            content: 'تعرف على شركتنا وقيمنا.',
            seo_title: 'معلومات عنا - اسم الشركة',
            meta_description: 'اكتشف مهمتنا ورؤيتنا.',
            meta_keywords: 'معلومات عنا, شركة, قيم',
          },
        ],
        is_published: false,
        slug: 'about'
    },
    contact: {
        default_language: 'en',
        translations: [
          {
            language: 'en',
            title: 'Contact Us',
            content: 'Get in touch with our team.',
            seo_title: 'Contact Us - Company Name',
            meta_description: 'Reach out to us for any inquiries.',
            meta_keywords: 'contact, support, inquiries',
          },
          {
            language: 'ar',
            title: 'اتصل بنا',
            content: 'تواصل مع فريقنا.',
            seo_title: 'اتصل بنا - اسم الشركة',
            meta_description: 'تواصل معنا لأي استفسارات.',
            meta_keywords: 'اتصل بنا, دعم, استفسارات',
          },
        ],
        is_published: false,
        slug: 'contact'
    },
    privacy: {
        default_language: 'en',
        translations: [
          {
            language: 'en',
            title: 'Privacy Policy',
            content: `Learn about our privacy practices.
            
            `,
            seo_title: 'Privacy Policy - Company Name',
            meta_description: 'Understand how we handle your data.',
            meta_keywords: 'privacy, policy, data protection',
          },
          {
            language: 'ar',
            title: 'سياسة الخصوصية',
            content: 'تعرف على ممارسات الخصوصية لدينا.',
            seo_title: 'سياسة الخصوصية - اسم الشركة',
            meta_description: 'افهم كيف نتعامل مع بياناتك.',
            meta_keywords: 'خصوصية, سياسة, حماية البيانات',
          },
        ],
        is_published: false,
        slug: 'privacy'
    },
    terms: {
        default_language: 'en',
        translations: [
          {
            language: 'en',
            title: 'Terms of Service',
            content: 'Review our terms and conditions.',
            seo_title: 'Terms of Service - Company Name',
            meta_description: 'Understand our service terms.',
            meta_keywords: 'terms, service, conditions',
          },
          {
            language: 'ar',
            title: 'شروط الخدمة',
            content: 'راجع شروطنا وأحكامنا.',
            seo_title: 'شروط الخدمة - اسم الشركة',
            meta_description: 'افهم شروط خدمتنا.',
            meta_keywords: 'شروط, خدمة, أحكام',
          },
        ],
        is_published: false,
        slug: 'terms'
    },
    faq: {
        default_language: 'en',
        translations: [
          {
            language: 'en',
            title: 'Frequently Asked Questions',
            content: `Find answers to common questions about our services.
            How do I register?
            Go to the registration page and fill out your details.
            How can I contact support?
            You can use the contact form or email us directly.
            Is there a free trial?
            Yes, we offer a free trial for 30 days.
            `,
            seo_title: 'Frequently Asked Questions - Company Name',
            meta_description: 'Get answers to your questions.',
            meta_keywords: 'faq, questions, support',
          },
          {
            language: 'ar',
            title: 'الأسئلة الشائعة',
            content: `ابحث عن إجابات للأسئلة الشائعة حول خدماتنا.
            كيف يمكنني التسجيل؟
            انتقل إلى صفحة التسجيل وأكمل بياناتك.
            كيف يمكنني الحصول علي مساعدة؟
            يمكنك استخدام نموذج الاتصال أو مراسلتنا مباشرةً عبر البريد الإلكتروني.
            هل يوجد تجربة مجانية؟
            نعم، نقدم نسخة تجريبية مجانية لمدة 30 يومًا.
            `,
            seo_title: 'الأسئلة الشائعة - اسم الشركة',
            meta_description: 'احصل على إجابات لأسئلتك.',
            meta_keywords: 'الأسئلة الشائعة, الأسئلة, الدعم',
          },
        ],
        is_published: false,
        slug: 'faq'
    }
};
