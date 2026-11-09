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

بعد التشغيل `pdm run dev` افتح http://tenant-a.localhost:8100/auth/login/ ثم /account/. لا توجد شركة أو كلمة مرور افتراضية جاهزة. تتوفر واجهة الإدارة العربية في R05. توجد خدمات create_member/invite_member/assign_role/transfer_ownership داخلية وليست endpoints CRUD عامة. لا تضبط is_superuser لمنح صلاحية ERP.

روابط الدعوة/reset تصدر من مسؤول مخول وتستهلك في شركة واحدة فقط؛ قناة SMTP اختيارية وفق الإعداد التالي. لا تنسخ الرموز في المحادثة أو logs. راجع ADR 0006 لتفاصيل سجل الانتظار.

## قواعد الاتصال
OSM_REBUILD_DB_MODE افتراضيًا runtime. أوامر migrate-shared/manage-migration/migrations-check/test/configure-runtime تضبط migration صراحة. `pdm run manage-migration <command>` مخصص للمطور/النشر فقط، ولا يوضع في خدمة الويب. `pdm run dev` وverify-runtime يستخدمان runtime. بعد إضافة مخططات في R04، تُحدّث منح runtime بواسطة configure-runtime ضمن provisioning الموثق.

في الإنتاج لا تضع بيانات المالك مع بيئة الويب، ولا تفعّل DEBUG أو runserver. لم يجهز نشر الإنتاج في R03. لا تُنفذ أوامر حذف volumes لتنظيف الكود؛ هذه بيانات تطوير دائمة. إيقاف قاعدة التطوير فقط: `docker compose --env-file .env -f compose.yaml stop db` من rebuild/.

## التحقق المستمر
- `pdm run test`: 89 اختبار Django/PostgreSQL ومخططات حاليًا تشمل أساس R03 وعزل R04 وHTTP والروابط والتزامن وقيود التدقيق.
- `pdm run test-policy`: 44 اختبار سياسة مجردة؛ لا يعوض اختبارات قاعدة البيانات.
- نجح `.github/workflows/rebuild.yml` فعليًا على GitHub للـcommit 67a30e0: [تشغيل R03](https://github.com/Elhussin/osm/actions/runs/42575805281). يستمر التشغيل على كل تعديل مطابق لمسارات workflow.
- نجح كذلك [تشغيل R04](https://github.com/Elhussin/osm/actions/runs/42594132931) للـcommit 74553dc، شاملاً اختبارات الهوية والصلاحيات الجديدة. أضيفت اختبارات واجهة R05 إلى المسار نفسه.
- تغييرات اعتماديات: عبر PDM فقط، لا تعديل lock يدويًا. لا تستخدم ملف requirements القديم.
- نتائج هذه الجلسة وحدودها في TEST_LOG.md. تتوفر خدمات provisioning والأدوار والفروع وروابط الدعوات والاسترداد؛ وحدات الأعمال R06 وما بعدها.

## واجهة R05 وSMTP
بعد أي ترحيل جديد: `pdm run migrate-all` ثم `pdm run configure-runtime`. سجل البريد الجديد داخل مخططات الشركات فقط. لا بيانات دخول افتراضية؛ أنشئ شركة صناعية بالأمر أعلاه ثم افتح /account/ على نطاقها.

في rebuild/.env المحلي فقط اضبط OSM_REBUILD_INVITE_DELIVERY=smtp وOSM_REBUILD_SMTP_HOST/PORT/USER/PASSWORD/FROM وOSM_REBUILD_SMTP_TLS=true (STARTTLS؛ الافتراضي port587). لا تدعم هذه الإعدادات SSL الضمني على 465؛ اختر endpoint STARTTLS من مزودك. لا تضع الأسرار في أمر shell أو Git أو المحادثة. بقاء manual يعني تسليم الرابط الآمن يدويًا وعدم إرسال بريد.

شغّل `pdm run mail-worker --limit 20` دوريًا، مثل كل دقيقة عبر مشغل خدمات/جدولة موثوق، بنفس إعداد runtime للويب. الأمر دفعة واحدة ثم ينتهي، وليس daemon أو scheduler مضمّنًا. لا يحتاج بيانات مستخدم DB migration. يعالج حدًا لكل شركة ready دون إخراج مستلمين أو رموز. عند عدم تشغيله تبقى الرسالة queued؛ الواجهة لا تدّعي إرسالها. المهلة10ثوانٍ، حجز دقيقتين، خمس محاولات مع backoff. عند فشل نهائي أو انتهاء الرابط أصدر رابطًا جديدًا من صفحة العضو. لا يوجد في هذه المرحلة لوحة مراقبة outbox كاملة أو ضمان SMTP exactly-once. لم تختبر خدمة SMTP حقيقية؛ الاختبارات تستخدم locmem ومحاكاة فشل.

اختبارات المتصفح الاختيارية محليًا:
```powershell
# من جذر المستودع بعد تثبيت مجموعة browser بواسطة PDM
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Resolve-Path rebuild/.tools).Path 'browsers'
pwsh -NoProfile -File rebuild/pdm.ps1 run python -m playwright install chromium --only-shell
pwsh -NoProfile -File rebuild/pdm.ps1 run test-browser
```
Chromium معزول، والصور الصناعية في rebuild/.tools/ui-artifacts مستبعدة. CI يثبت Chromium ومكتبات النظام قبل الاختبارات. لا تستخدم بيانات حقيقية أو تتبع شبكة يحتوي رموز الدعوات. للخادم الإنتاجي اجمع staticfiles عبر `pdm run manage-migration collectstatic --noinput` وخدمها من إعداد نشر مستقل؛ runserver محلي فقط.

## R06 — العملاء وصور الفحص
طبّق `pdm run migrate-all` ثم `pdm run configure-runtime` بعد التحديث، لكل مخططات الشركات. يضيف clinical جداول العملاء والروابط والوصفات والإصدارات والصور؛ سحب UPDATE/DELETE من revision/image يحتاج configure-runtime للشركات القائمة، ويحدث تلقائيًا للشركات الجديدة. لا تستخدم حساب migration للويب.

بعد الدخول اختر «العملاء والفحوص»: أضف عميلًا في فرع مسموح، ثم سجل فحصًا بمختص مخول. الكاشير يدير بيانات العميل دون قراءة وصفاته وصوره. مشاركة العميل للفرع من المالك لا تكشف تاريخ الفرع الآخر. التصحيح ينشئ إصدارًا جديدًا مع سبب؛ اختيار «بدون صورة» لا يحذف صورة الإصدار القديم.

الصورة اختيارية JPEG/PNG حتى5MiB و16MP وبُعد6000؛ صورة واحدة لكل إصدار. لا HEIC/PDF/SVG ولا OCR. PostgreSQL يحفظ PNG المعاد ترميزها داخل مخطط الشركة؛ لا إعداد MEDIA_URL عام، ولا مجلد صور مرضى داخل static. النسخ الاحتياطي يجب أن يشمل جداول clinical، وتُقاس سعة الصور والنسخ والاستعادة في R14. تشغيل الإنتاج يحتاج حد request body6MiB ومهلة وموارد workers في reverse proxy؛ upload handler داخل Django لا يغني عن ذلك خصوصًا تحت ASGI.

اختبارات clinical داخل `pdm run test`، وثلاث حالات متصفح إضافية داخل `pdm run test-browser`. الصور الصناعية المحلية clinical-exam-*.png تحت .tools/ui-artifacts. القياسات وحدود الإدخال وسياسة التاريخ وقيود مرحلة R10 في ADR 0007؛ لا تستخدم صورة وحدها كلقطة قياسات لطلب بيع.

## R07 — الكتالوج والأسعار
بعد التحديث: `pdm run migrate-all` ثم `pdm run configure-runtime` لجميع الشركات الموجودة. منح الأعمدة تقيد تحديث هوية المتغير وقاعدة السعر، ولا يكفي تشغيل migration دون تحديث المنح. الشركة الجديدة تحصل عليها ضمن provisioning. استمر بالويب بحساب runtime.

من المالك افتح «دليل المنتجات» وأضف منتجًا ثم متغيرًا بمواصفاته ووحدة بيعه وسعره الأساسي. يحتاج مستخدم الفرع دور catalog_reader صريحًا لقراءة الدليل بجانب دوره التشغيلي؛ لا يمنح هذا الدور إدارة الأسعار أو قراءة بيانات العملاء. القوالب الحالية تمنح catalog.manage للمالك فقط.

الأسعار SAR قبل الضريبة؛ اختيار «زوج» يعني سعر الزوج وعدد الأزواج، واللاصقة سعر العلبة مع عدد محتوياتها، دون تفكيك أو تحويل ضمني. قواعد العميل مرتبطة بفرع، والكمية صحيحة بوحدة المتغير. بعد اختيار فرع في نموذج القاعدة أو المعاينة اضغط «تحديث خيارات العملاء» إن أردت اختيار عميل؛ يعمل دون JavaScript ولا يحفظ القاعدة. السعر صفر مسموح ولا يعاد إلى الأساسي. لإنهاء قاعدة أوقفها ثم أضف البديل، ولا تعدل محتواها أو تحذفها.

راجع ADR 0008 لأولوية السعر وحدود التقريب والتواريخ ومعنى اللقطة. المعاينة تحتاج صلاحية الفرع ولا تنشئ طلبًا أو حركة أو اعتماد جملة/ائتمان. قواعد الضريبة والمالية في R09/R10 والجملة في R11، والمخزون R08. صور QA الصناعية catalog-*.png تحت rebuild/.tools/ui-artifacts؛ اختبارات الكتالوج ضمن test وثلاث حالات جديدة ضمن test-browser.
