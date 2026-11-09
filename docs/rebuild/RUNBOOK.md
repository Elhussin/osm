# تشغيل نسخة إعادة البناء

آخر تحديث: 2026-11-09. يوجد الآن دخول HTML وحساب شركة أوليان وخدمات إدارة الهوية؛ لا واجهات بيع بعد. لا تستخدم docker-compose.yml القديم أو أوامر reset القديمة.

## المتطلبات
Python 3.12 وPDM 2.29.7، وDocker Desktop يعمل بوضع Linux containers. نفذت هذه الجلسة بيئة Windows محلية باستخدام Python المرفق بتبعيات التطبيق؛ هذا المسار شخصي وليس شرطًا على أجهزة المطورين.

من جذر المشروع:

```powershell
cd rebuild
pdm use -f python
pdm lock --check
pdm sync --clean
python scripts/init_local.py
docker compose --env-file .env -f compose.yaml up -d --wait db
pdm run migrate-shared
pdm run configure-runtime
pdm run verify-runtime
pdm run check
pdm run migrations-check
pdm run test
pdm run test-policy
pdm run dev
```

في هذا الجهاز يمكن استخدام `pwsh -NoProfile -File rebuild/pdm.ps1 run check` من الجذر، وبقية أوامر PDM بنفس الطريقة. الـwrapper يستخدم PDM الذي ثُبت في .tools؛ لا يثبت الحزم تلقائيًا. `init_local.py` ينفذ مرة واحدة؛ إذا وجد .env يتوقف دون تعديل. لا تعرض محتوى الملف أو تضفه إلى Git. لا تغير كلمة مرور قاعدة موجودة في .env وتتوقع تغييرها داخل volume تلقائيًا.

الجلسة الحالية أنشأت قاعدة التطوير وrole runtime؛ لم تنشئ شركات تطوير أو مستخدمين تجريبيين فيها. شركتا الاختبار والمستخدمون الصناعيون أنشئوا فقط في قاعدة الاختبار التي دمرها Django بعد الاختبارات.

## فحوص الصحة
خادم التطوير على http://127.0.0.1:8100. `/health/live/` يعيد alive دون قاعدة، و`/health/ready/` يعيد ready عند اتصال القاعدة أو 503 منقحًا. تتحقق ALLOWED_HOSTS حتى في probes؛ لا تستخدمهما كدليل تفعيل ERP.

## إنشاء شركة وأول مالك — R04
طبّق الترحيلات الجديدة أولًا: `pdm run migrate-all` ثم `pdm run configure-runtime` لتحديث منح الشركات الموجودة. لإنشاء شركة استخدم أمر deployment فقط، بمفتاح UUID ثابت تحفظه لإعادة المحاولة:

```powershell
pdm run manage-migration provision_company --name "شركة تجريبية" --domain tenant-a.localhost --owner owner --operation-key <UUID>
```

استبدل <UUID> بمعرف تولده مرة واحدة؛ الأمر يطلب كلمة مرور المالك عبر getpass ولا يقبلها في arguments. أضف النطاق إلى OSM_REBUILD_ALLOWED_HOSTS المحلي قبل زيارته. ينشأ schema داخلي ومالك ودور owner وفرع MAIN، ويحدث منح runtime قبل إعلان ready. إذا فشل الإنشاء لا تحذف schema؛ أصلح السبب وأعد الأمر بنفس مفتاح العملية والنطاق واسم المالك. لا تعاد كلمة مرور مالك جاهز بمجرد إعادة الأمر.

بعد التشغيل `pdm run dev` افتح http://tenant-a.localhost:8100/auth/login/ ثم /account/. لا توجد شركة أو كلمة مرور افتراضية جاهزة. شاشات الدخول الحالية أولية؛ شاشات الإدارة الموسعة R05. توجد خدمات create_member/invite_member/assign_role/transfer_ownership داخلية وليست endpoints CRUD عامة. لا تضبط is_superuser لمنح صلاحية ERP.

روابط الدعوة/reset تصدر من مسؤول مخول وتستهلك في شركة واحدة فقط؛ لا قناة إرسال بريد تلقائي مفعلة. لا تنسخ الرموز في المحادثة أو logs. خيارات التسليم ستجهز ضمن تجربة R05.

## قواعد الاتصال
OSM_REBUILD_DB_MODE افتراضيًا runtime. أوامر migrate-shared/manage-migration/migrations-check/test/configure-runtime تضبط migration صراحة. `pdm run manage-migration <command>` مخصص للمطور/النشر فقط، ولا يوضع في خدمة الويب. `pdm run dev` وverify-runtime يستخدمان runtime. بعد إضافة مخططات في R04، تُحدّث منح runtime بواسطة configure-runtime ضمن provisioning الموثق.

في الإنتاج لا تضع بيانات المالك مع بيئة الويب، ولا تفعّل DEBUG أو runserver. لم يجهز نشر الإنتاج في R03. لا تُنفذ أوامر حذف volumes لتنظيف الكود؛ هذه بيانات تطوير دائمة. إيقاف قاعدة التطوير فقط: `docker compose --env-file .env -f compose.yaml stop db` من rebuild/.

## التحقق المستمر
- `pdm run test`: 33 اختبار Django/PostgreSQL حاليًا تشمل أساس R03 وعزل R04 وHTTP والروابط والتزامن وقيود التدقيق.
- `pdm run test-policy`: 44 اختبار سياسة مجردة؛ لا يعوض اختبارات قاعدة البيانات.
- نجح `.github/workflows/rebuild.yml` فعليًا على GitHub للـcommit 67a30e0: [تشغيل R03](https://github.com/Elhussin/osm/actions/runs/42575805281). يستمر التشغيل على كل تعديل مطابق لمسارات workflow.
- نجح كذلك [تشغيل R04](https://github.com/Elhussin/osm/actions/runs/42594132931) للـcommit 74553dc، شاملاً اختبارات الهوية والصلاحيات الجديدة. الواجهة المتكاملة وتجربة إدارة الأعضاء R05.
- تغييرات اعتماديات: عبر PDM فقط، لا تعديل lock يدويًا. لا تستخدم ملف requirements القديم.
- نتائج هذه الجلسة وحدودها في TEST_LOG.md. R04 سيضيف خدمات provisioning والأدوار والفروع ومنع التصعيد وروابط الدعوات والاسترداد.
