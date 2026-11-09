# إعادة بناء نظام البصريات ERP

هذه النسخة مخصصة لإعادة البناء. المرجع المعتمد هو [خطة إعادة البناء](docs/rebuild/README.md).

- `rebuild/`: التطبيق الجديد، مستقل في الإعدادات والبيانات والتشغيل.
- `osmBack/` و`osmFront/`: مرجع مؤقت لاستخراج قواعد العمل، وليسا التطبيق الجديد.
- `docs/rebuild/`: الخطة والقرارات والحالة ومعايير القبول وسجل الاختبارات والحذف.
- `scripts/check-rebuild.ps1`: فحص اتساق خطة العمل وأدلة الإنجاز.

ابدأ كل جلسة بقراءة الخطة و`AGENTS.md`. لا تشغّل Docker Compose القديم لإعداد البيئة الجديدة؛ إعداداته تشير إلى النظام المرجعي. لا تستخدم بيانات أو أسرار النظام الأصلي.

فحص توثيق إعادة البناء (لا يحتاج Python أو قاعدة بيانات):

```powershell
pwsh -NoProfile -File scripts/check-rebuild.ps1
```

فحص حصر النظام المرجعي:

```powershell
pwsh -NoProfile -File scripts/check-discovery.ps1
```

أضيف أساس Django وPostgreSQL مستقل واجتاز R03 محليًا وعلى GitHub Actions. القرار المعتمد: كل حساب يتبع شركة واحدة فقط، ولكل شركة مخططها ومستخدموها وجلساتها. المستودع الجديد https://github.com/Elhussin/osm.git؛ العمل على فرع codex/r03-foundation دون دمجه في main. راجع [دليل التشغيل](docs/rebuild/RUNBOOK.md).

اكتملت R04: خدمات إنشاء الشركات والأعضاء والفروع والتعيينات والتدقيق، ودخول HTML أولي وروابط دعوة/reset مقيدة بالشركة. نجح 33 اختبار Django/PostgreSQL و44 سياسة محليًا وعلى CI؛ تصميم ERP وشاشات الإدارة المتكاملة R05. التفاصيل والحدود في docs/rebuild/decisions/0005-access-services.md.

اختبارات السياسة بمفسر Python صالح من جذر المستودع:

```powershell
python -m unittest discover -s rebuild/tests -v
```

يستخدم الإصدار الجديد PDM لإدارة اعتماديات Python وتشغيل أوامر المشروع. راجع قرار `docs/rebuild/decisions/0002-pdm-and-configuration.md` لفصل إدارة الاعتماديات عن إعدادات التطبيق.

اكتملت R05: واجهة إدارة عربية RTL عبر Django/HTMX، ودعوات واستعادة مع سجل SMTP في الخلفية عند إعداده. نجحت 97 حالة فريدة محليًا وعلى [CI](https://github.com/Elhussin/osm/actions/runs/42635412157). التالي R06 للعملاء والفحوص والوصفات؛ تفاصيل البريد وحدوده في [ADR 0006](docs/rebuild/decisions/0006-workspace-and-mail.md).

اكتملت R06: العملاء والفحوص والوصفات بإصدارات محفوظة وصورة فحص اختيارية خاصة. نجحت118 حالة فريدة محليًا وعلى [CI](https://github.com/Elhussin/osm/actions/runs/42648591494). التالي R07 للمنتجات والمتغيرات والتسعير؛ التفاصيل في [ADR 0007](docs/rebuild/decisions/0007-clinical-records-and-images.md).

اكتملت R07: دليل منتجات ومتغيرات بصريات ووحدات بيع ثابتة وقواعد سعر حسب العميل والفرع والقناة والكمية والتاريخ. نجحت143 حالة فريدة محليًا وعلى [CI](https://github.com/Elhussin/osm/actions/runs/42654940007). التالي R08 للمخزون والحجز والتحويل والجرد؛ التفاصيل في [ADR 0008](docs/rebuild/decisions/0008-catalog-and-pricing.md).

اكتملت R08-M01: عرض وإدخال مخزون العدسات بمصفوفة SPH/CYL مفصولة بالعائلة والوحدة، مع لصق ومعاينة وإضافة بلا تكرار وعكس محفوظ. نجحت166 حالة فريدة محليًا وعلى [CI](https://github.com/Elhussin/osm/actions/runs/42673309187/attempts/2). R08 ككل مستمرة؛ التالي R08-M02 للحجز والصرف. التفاصيل في [ADR 0009](docs/rebuild/decisions/0009-stock-lens-matrices.md).

اكتملت R08-M02: حجز وصرف وتحرير جزئي وإلغاء المتبقي وعكس صرف محفوظ، مع منع التكرار وتجاوز المتاح. نجحت182 حالة فريدة محليًا وعلى [CI](https://github.com/Elhussin/osm/actions/runs/42681586976). R08 مستمرة؛ التالي R08-M03 للتحويل والجرد ثم M04 للتتبع. التفاصيل في [ADR 0010](docs/rebuild/decisions/0010-stock-reservations.md).
