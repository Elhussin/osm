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
