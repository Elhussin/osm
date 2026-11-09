# تشغيل نسخة إعادة البناء

آخر تحديث: 2026-11-09. هذا أساس تقني؛ لا واجهات بيع أو دخول مستخدمين بعد. لا تستخدم docker-compose.yml القديم أو أوامر reset القديمة.

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

## قواعد الاتصال
OSM_REBUILD_DB_MODE افتراضيًا runtime. أوامر migrate-shared/manage-migration/migrations-check/test/configure-runtime تضبط migration صراحة. `pdm run manage-migration <command>` مخصص للمطور/النشر فقط، ولا يوضع في خدمة الويب. `pdm run dev` وverify-runtime يستخدمان runtime. بعد إضافة مخططات في R04، تُحدّث منح runtime بواسطة configure-runtime ضمن provisioning الموثق.

في الإنتاج لا تضع بيانات المالك مع بيئة الويب، ولا تفعّل DEBUG أو runserver. لم يجهز نشر الإنتاج في R03. لا تُنفذ أوامر حذف volumes لتنظيف الكود؛ هذه بيانات تطوير دائمة. إيقاف قاعدة التطوير فقط: `docker compose --env-file .env -f compose.yaml stop db` من rebuild/.

## التحقق المستمر
- `pdm run test`: 9 اختبارات أساس حاليًا؛ اختبار PostgreSQL واحد يتضمن ستة فحوص للمخططات وكلمات المرور والجلسات والتوجيه واستعادة السياق.
- `pdm run test-policy`: 44 اختبار سياسة مجردة؛ لا يعوض اختبارات قاعدة البيانات.
- نجح `.github/workflows/rebuild.yml` فعليًا على GitHub للـcommit 67a30e0: [تشغيل R03](https://github.com/Elhussin/osm/actions/runs/42575805281). يستمر التشغيل على كل تعديل مطابق لمسارات workflow.
- تغييرات اعتماديات: عبر PDM فقط، لا تعديل lock يدويًا. لا تستخدم ملف requirements القديم.
- نتائج هذه الجلسة وحدودها في TEST_LOG.md. R04 سيضيف خدمات provisioning والأدوار والفروع ومنع التصعيد وروابط الدعوات والاسترداد.
