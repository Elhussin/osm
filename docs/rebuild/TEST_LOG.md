# سجل الاختبارات

لا توجد نتائج اختبارات للتطبيق الجديد بعد. نتائج فحص خطة العمل تسجل هنا بعد تشغيلها. فشل تشغيل Python المحلي لوحظ في 2026-11-09؛ لم تُشغّل اختبارات Django أو قاعدة البيانات.

## T000 | passed
Task: R00
Date: 2026-11-09
Command: pwsh -NoProfile -File scripts/check-rebuild.ps1

البيئة: Windows / PowerShell، لا يتطلب Python أو PostgreSQL.
النتيجة: exit code 0. نجح فحص الملفات المطلوبة والخطة والتبعيات والتنظيف، ونجحت 9 حالات للمدقق: رفض إنجاز بلا دليل، وتبعية مجهولة، وتبعية غير منجزة، ودورة، ومعرف مكرر، وحالة مجهولة، وغياب نتيجة، وقبول دليل صحيح، ورفض دليل يخص مهمة أخرى.
القيود: هذه اختبارات سير العمل فقط؛ لا تثبت عمل Django أو سلامة وحدات legacy أو جاهزية ERP. المدقق يفحص سجل الأدلة ولا يشغّل اختبارات التطبيق نيابة عن منفذ المهمة.

## T001 | passed
Task: R01
Date: 2026-11-09
Command: pwsh -NoProfile -File scripts/check-discovery.ps1

البيئة: Windows / PowerShell / Git، دون تشغيل النظام القديم أو قاعدة بياناته.
النتيجة: exit code 0. تطابق الحصر مع 781 ملف legacy متتبع موجود؛ اكتمال 10 مواصفات قبول وربطها بمصادر موجودة وanchors فعلية؛ نجاح 6 اختبارات حدود تصنيف تشمل الأسرار والترحيل والبيانات والسكربتات التشغيلية. ولّد الحصر أولًا باستخدام -RefreshInventory ثم تحقق منه بالأمر أعلاه دون إعادة توليد.
القيود: هذه اختبارات اتساق الحصر والمواصفات، وليست تنفيذًا لسيناريوهات ERP. أسئلة الأجهزة وoffline ومصدر التأمين ما زالت مفتوحة ومربوطة بالمراحل المعنية. PDM غير ظاهر في PATH؛ لم نعتبر وجود lock نجاحًا في التشغيل. تحقق origin محليًا فقط؛ لا اتصال أو تعديل للمستودع البعيد.

## T002 | passed
Task: R00
Date: 2026-11-09
Command: pwsh -NoProfile -File scripts/check-rebuild.ps1

بعد إغلاق R01 كشف فحص المدقق أن عينة النجاح المصطنعة تستبدل سجل الأدلة بالكامل، فتفقد دليل T001. عُدلت العينة لتضيف سجلها المصطنع إلى السجل الحقيقي دون تعديل الملفات. أعيد التشغيل: exit code 0، ونجحت جميع حالات الرفض والقبول التسع مع وجود مهمتين مكتملتين. لم يتغير شرط وجود دليل نجاح لكل مهمة. أعيد تشغيل check-discovery.ps1 دون refresh ونجح أيضًا.

## T003 | passed
Task: R01
Date: 2026-11-09
Command: pwsh -NoProfile -File scripts/check-discovery.ps1

بعد إدراج إجابات المستخدم ونطاق وصيل: exit code 0؛ بقي الحصر مطابقًا لـ781 ملفًا، ونجح تحقق 10 مواصفات قبول ومصادرها، بما فيها S08/S09 المنقولان إلى INSURANCE_WORKFLOW.md. نجحت اختبارات حدود التصنيف الستة، وcheck-rebuild.ps1 وحالاته التسع، وgit diff --check.
الحدود: تحقق توثيق ومواصفات فقط؛ لا اتصال بوصيل ولا اختبار وظيفي للأهلية أو الموافقات أو المطالبات. الأجهزة مؤجلة والنسخة الأولى متصلة بالإنترنت.

## T004 | passed
Task: R01
Date: 2026-11-09
Command: & 'C:/Users/Hussam/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' scripts/check_waseel_docs.py

ثم الأمر بنفس المفسر: scripts/test_waseel_docs.py. البيئة: Windows مع Python المرفق بتبعيات التطبيق؛ السكربتان يعتمدان على مكتبة Python القياسية فقط. ولّد الحصر أولًا باستخدام --refresh، ثم أعيد فحصه دون إعادة توليد.

النتيجة: exit code 0؛ تطابق بصمات وبنية 9 ملفات مصدر و17 طلب Postman و18 ورقة و5 أمثلة JSON. نجحت 7 اختبارات: حجب القيم الخاصة، التمييز بين null/zero/false/empty، حجب الاعتماد وقيم query ومعرف المزود، رفض مضيف غير مراجع، وسم JSON غير الصالح، تحقق Vision وحالات partial/pended/Error من المصادر، وتحقق أن الأصول مستبعدة وغير متتبعة في Git.

نجح check-discovery.ps1 (781 ملفًا و10 مواصفات و6 حدود تصنيف)، وcheck-rebuild.ps1 وحالاته التسع. كشف diff --check اختلاف نهايات الأسطر في .gitignore؛ وحد الملف إلى LF وأعيد الفحص بنجاح. لا حذف أو تعديل لمواد وصيل الأصلية، ولا اتصال بالشبكة أو اختبار صلاحية قيم الدخول، ولا إثبات اتصال أو امتثال أو إنجاز R12/R13.

## T005 | passed
Task: R02
Date: 2026-11-09
Command: & 'C:/Users/Hussam/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' -m unittest discover -s rebuild/tests -v

البيئة: Windows / Python المرفق بتبعيات التطبيق، مكتبة قياسية فقط؛ دون Django أو قاعدة بيانات. القرار استند لإجابة المستخدم: كل حساب يتبع شركة واحدة فقط.

النتيجة: exit code 0، نجح 44 اختبارًا (P01–P40 وأربعة اختبارات سجل وسياسة). شملت رفض اختلاف شركة المستخدم أو المورد أو المنحة، وفروع غير مخولة أو معطلة، وإلغاء منحة، ونقل مخزون يحتاج الفرعين، وفصل صلاحية تكوين وصيل عن إرسال طلباته، ورفض الأفعال والأدوار المجهولة، واستقلال التقييم المتعاقب. أعيد التشغيل دون -v ونجح أيضًا.

نجح check-discovery.ps1 وcheck-rebuild.ps1 وgit diff --check. نجح تحقق حصر وصيل دون refresh ولم تتغير مصادره. لم تتغير ملفات legacy ولا حصرها، ولا حذف إضافي. أضيف تجاهل cache Python الجديد فقط.

المخرجات: ADR 0003 وACCESS_MODEL.md وACCESS_VERIFICATION.md وaccess-matrix.json والسياسة في rebuild/access/policy.py. حُسم Q06، والتالي R03. حدود الإثبات: R02 مرحلة تصميم وسياسة مجردة مكتملة؛ I01–I20 اختبارات قاعدة/HTTP وتشغيل ما زالت planned لمراحلها. لم تُنشأ migrations أو جداول أو مسارات مصادقة، ولا يُستدل من هذه النتيجة على تحقق عزل PostgreSQL والجلسات فعليًا.

## T006 | failed
Task: R03
Date: 2026-11-09
Command: pwsh -NoProfile -File rebuild/pdm.ps1 run test

أول تشغيل PostgreSQL: نجحت فحوص المخططات والمصادقة والجلسات، لكن فشل tearDownClass لاختبار health لأن patch استهدف connection proxy وأفسد غلاف منع الاتصال الخاص بـSimpleTestCase (AttributeError: function has no attribute wrapped). عزل فحص الجاهزية في database_ready وتعديل mock لاستهدافه أصلح الاختبار دون إضعاف حظر قاعدة البيانات في SimpleTestCase. لا تُحسب هذه المحاولة نجاحًا.

## T007 | passed
Task: R03
Date: 2026-11-09
Command: pwsh -NoProfile -File rebuild/pdm.ps1 run test

البيئة: Windows، Python3.12.14/PDM2.29.7، حاوية PostgreSQL16 جديدة optics-rebuild-db-1 على 127.0.0.1:55432. Django5.2.19 وdjango-tenants3.14.0 وpsycopg3.3.8 من pdm.lock جديد. اكتمل التثبيت الأول على .venv فارغة، ونجح lock --check وsync --clean اللاحقان.

النتيجة: exit code 0، 9 اختبارات أساس؛ اختبار TransactionTestCase واحد يتضمن ستة فحوص فعلية (pg_tables لـpublic وشركتين، نفس اسم الدخول بكلمتي مرور مستقلتين، فصل session store، رفض نطاق مجهول، استعادة schema_context بعد استثناء، ورفض شركة معلقة). دمر Django test_optics_rebuild_dev بعد الانتهاء. اختبارات الإعداد تمنع fallback إلى DB_* القديمة وترفض اسم قاعدة خارج optics_rebuild_* وتثبت اختيار runtime افتراضيًا. اختبارات health تثبت liveness دون قاعدة و503 منقحًا عند الخطأ ورفض host غير مسموح.

فحوص أخرى ناجحة:
- pdm run check وmigrations-check: لا مشاكل ولا تغييرات ترحيل غير مولدة.
- pdm run migrate-shared: ترحيل جديد على optics_rebuild_dev فقط.
- pdm run configure-runtime ثم verify-runtime: دور runtime يقرأ الدليل ويُرفض CREATE schema/table وUPDATE الدليل، دون طباعة كلمات المرور.
- pdm run test-policy: 44 اختبارًا ناجحًا بعد تثبيت البيئة الجديدة.
- تشغيل pdm run dev --noreload بحساب runtime، ثم Invoke-RestMethod على /health/live/ و/health/ready/: HTTP ناجح وalive/ready فعليًا.
- نجحت فحوص الخطة والحصر وgit diff --check وفحص تجاهل أسرار وأدوات البيئة. أُوقف خادم التطوير بعد اختبار HTTP؛ بقيت حاوية قاعدة التطوير الجديدة متاحة دون تغيير الحاويات الأخرى.

القيود: لا login UI أو أدوار/فروع مخزنة أو provisioning إنتاج كامل بعد. اختبارات المخططات لا تغطي كامل I01–I20. أضيفت .github/workflows/rebuild.yml لكن لم تدفع التغييرات أو يشغل GitHub Actions؛ شرط CI الأخضر ما زال مفتوحًا، ولذلك R03 لم تُغلق. لا SQLite ولا اتصال بقواعد أو بيانات legacy أو وصيل ضمن هذه الاختبارات.

## T008 | passed
Task: R03
Date: 2026-11-09
Command: GET https://api.github.com/repos/Elhussin/osm/actions/runs/42575805281/jobs

أذن المستخدم صراحة بالـcommit والدفع في هذه الجلسة. أُنشئ الفرع codex/r03-foundation ودفع commit 67a30e0299f73bead0d9bd5a430d907e1b2efac3 إلى Elhussin/osm. راجعنا 72 ملفًا مجهزًا: لا بيئات خاصة أو ملفات وصيل خام أو قيم أسرار .env الجديدة. أضيف .gitattributes لتوحيد نهايات الأسطر في ملفات البناء والتوثيق والاختبارات، ونجح diff --cached --check بعد ذلك.

الدليل البعيد: https://github.com/Elhussin/osm/actions/runs/42575805281 — status completed / conclusion success، وjob foundation وجميع خطواته success. شمل Ubuntu/PostgreSQL16، تثبيت PDM2.29.7، تثبيت من lock دون تحديثه، check/migrations-check/migrate-shared/configure-runtime/verify-runtime، واختبارات Django والسياسة وفحوص الخطة والحصر. قُرئ الدليل عبر GitHub REST باستخدام مصادقة Git القائمة دون عرض الاعتماد.

بهذا اكتملت بوابة R03 وأصبحت المهمة التالية R04. لا دمج في main، ولا نشر إنتاج أو استخدام بيانات legacy. بيانات CI صناعية. هذا الدليل لا يثبت متطلبات R04 التي لم تنفذ بعد.

## T009 | passed
Task: R04
Date: 2026-11-09
Command: pwsh -NoProfile -File rebuild/pdm.ps1 run test

البيئة: PostgreSQL16 المستقل وtest_optics_rebuild_dev، Django5.2.19 وPython3.12/PDM2.29.7. النتيجة: 33 اختبارًا ناجحًا خلال 143.818 ثانية. تشمل 9 اختبارات الأساس السابقة و24 حالة R04 لعمليات الإنشاء واستئنافه، جلسات وكلمات مرور مستقلة، CSRF وأعلام cookie، صلاحيات فروع وتعيينات حية، تعطيل حساب/فرع، عدم تجاوز superuser، قيود DB، دعوة/reset أحاديا الاستخدام ومقيدان بالشركة والغرض والوقت، إلغاء session بعد تغيير كلمة المرور، ملكية متزامنة، طلبات شركتين متزامنة، task context، provider scope، وaudit منقح غير قابل للتعديل والحذف لدور DB محدود.

أعيدت أربع حالات HTTP مستهدفة بعد تحويل الفروع والتدقيق إلى HTML بدل JSON ونجحت. وأعيدت ثلاث حالات بعد إضافة منح وصول فرع للمحاسب دون منحه صلاحيات كاشير، وخدمة تعطيل الفرع، وتأكيد SQLSTATE=42501 في منع تعديل/حذف audit؛ نجحت الحالات الثلاث. لا تُضاف هذه الإعادات إلى عدد الحالات الفريدة (33).

أثناء المراجعة صُحح تمييز تفويض دور شركة يحتوي أفعالًا فرعية عن تفويض عملية على مستند فرع؛ الاختبار الجديد يثبت منح accountant من المالك واستعادة المالك لكلمة مروره دون السماح لـcompany_admin برفع نفسه أو إعادة كلمة مرور المالك. قوالب الأدوار ثابتة؛ لا محرر أدوار مخصص غير مختبر.

نجح test-policy (44 اختبارًا إضافيًا؛ إجمالي فريد 77)، وcheck وmigrations-check وlock --check وconfigure-runtime/verify-runtime وcheck-discovery وdiff --check. طُبقت ترحيلات التطوير الجديدة دون إنشاء شركة أو كلمة مرور افتراضية في قاعدة التطوير. البيانات الصناعية والمخططات أنشئت في قاعدة الاختبار التي دمرت بعد كل تشغيل. اختبارات التزامن استخدمت اتصالات PostgreSQL منفصلة؛ لم يستخدم SQLite.

الحدود: الشاشات HTML أولية، دون اختبار بصري بمتصفح؛ تصميم وتجربة إدارة المستخدمين وتسليم الدعوات وإعداد البريد R05. لا قناة بريد فعلية أو queue أو اتصال وصيل. اختبارات الوحدات المالية/المخزون والتصدير تستكمل في مراحلها. R04 ينتظر CI على التغييرات الجديدة قبل إغلاق سجل هذه الجلسة؛ لا نستخدم نجاح CI القديم كدليل على الكود الجديد.
