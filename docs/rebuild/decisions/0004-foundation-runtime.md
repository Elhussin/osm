# ADR 0004: أساس التشغيل والاعتماديات R03

التاريخ: 2026-11-09. الحالة: منفذ ومختبر محليًا؛ تشغيل GitHub Actions البعيد لم يحدث بعد.

## الإصدارات المختبرة
Python 3.12.14، PDM 2.29.7، Django 5.2.19، django-tenants 3.14.0، psycopg/psycopg-binary 3.3.8، python-dotenv 1.2.4. الاعتماديات المباشرة أربع فقط، وإجمالي الحزم المثبتة من lock تسع. ملف pdm.lock مولد فعليًا بواسطة PDM وليس يدويًا. يثبت المشروع سلسلة Python 3.12، وتثبت CI نسخة PDM نفسها؛ تحديث الاعتماديات يتطلب تحديث lock وإعادة الاختبارات.

اختير Django 5.2 LTS بعد التحقق من [جدول الدعم الرسمي](https://www.djangoproject.com/download/) في 2026-11-09، وليس نسخ 5.2.6 القديمة. جرى التحقق من حزم [PDM](https://pypi.org/project/pdm/) و[django-tenants](https://pypi.org/project/django-tenants/) وتثبيتها فعليًا؛ توافقها المثبت هنا حدود الاختبارات الحالية فقط.

## إدارة البيئة
PDM أداة محلية داخل rebuild/.tools/pdm، وبيئة التطبيق rebuild/.venv. لم تُعدّل ملفات runtime المرفقة بالتطبيق أو Python العام. ملف rebuild/.pdm-python خاص بالجهاز ومستبعد. wrapper pdm.ps1 يختار PDM المحلي أو الموجود في PATH، ويضع cache/temp داخل .tools لتجنب مشكلة صلاحيات مجلد temp الافتراضي في هذه الجلسة.

الإعدادات تقرأ متغيرات OSM_REBUILD_* فقط، وملف rebuild/.env المحدد صراحة دون البحث في المجلدات الأعلى، مع أولوية متغيرات العملية. السكربت init_local.py أنشأ أسرارًا جديدة عشوائية ورفض الكتابة فوق ملف قائم. لا نسخ من ملفات البيئة القديمة.

## قاعدة البيانات والصلاحيات
- PostgreSQL 16 في مشروع Compose اسمه optics-rebuild وحاوية optics-rebuild-db-1، وربط loopback فقط 127.0.0.1:55432. وحدة التخزين optics-rebuild_rebuild_postgres مستقلة عن المشروع القديم وبقية التطبيقات.
- قاعدة التطوير optics_rebuild_dev، والاختبارات test_optics_rebuild_dev؛ ترفض الإعدادات اسم قاعدة لا يبدأ optics_rebuild_. اختبارات المخططات ترفض قاعدة ليست test_optics_rebuild_*.
- وضع الاتصال الافتراضي runtime يستخدم optics_rebuild_runtime وكلمة مرور مستقلة. وضع migration صريح عبر OSM_REBUILD_DB_MODE في أوامر PDM المختصة. ليس runtime superuser ولا CREATEDB/CREATEROLE ولا CREATE schema/table، ولا كتابة في دليل الشركات.
- حاوية التطوير تستخدم مالك PostgreSQL لأعمال الإنشاء/الاختبار؛ هذه ليست سياسة صلاحيات نشر إنتاج نهائية. أسرار المالك لا تحقن في خدمة الإنتاج؛ يدخل فقط سر runtime. .env المحلي للتطوير فقط.
- أمر configure_runtime_role يمنح قراءة public directory وجدول تاريخ الترحيل التقني، وDML على جداول الشركات الموجودة دون كتابة تاريخ migrations؛ يعاد بعد إنشاء مخطط جديد. تنفيذ provisioning الكامل والمالكين والأدوار R04. لا auto_create_schema على حفظ Company.

## الترحيل والنطاق
0001_initial جديدان لـdirectory وidentity. جداول Company/Domain في public، وUser/Auth/Session في كل مخطط شركة. قد يطبع migrate السطر auth...OK في public لأن router يسجل سجل التنفيذ؛ الاختبار يفحص pg_tables فعلًا ولا يستنتج وجود الجداول من رسائل migrate.

health/live لا يقرأ قاعدة أو جلسة. health/ready يختبر SELECT 1 بحساب runtime، ويعيد 503 منقحًا عند تعذر الاتصال. لا يعني ready جاهزية وحدة مبيعات أو تكامل تأمين. بقية المسارات تتطلب نطاق شركة مسجلًا وحالة ready دون fallback؛ لا واجهة دخول أو ERP بعد.

## CI وحدود الإنجاز
أضيف .github/workflows/rebuild.yml: PostgreSQL جديدة، وتثبيت من lock وفحص تغييرات migrations والترحيل وقيود runtime واختبارات الأساس والسياسة. نجحت أوامرها المكافئة محليًا على Windows؛ لم تُدفع التغييرات أو يشغّل GitHub Actions. لذلك شرط CI أخضر في R03 ما زال مفتوحًا، ولا تُغلق المرحلة قبل أول تشغيل ناجح أو قرار صريح بتغيير بوابتها.
