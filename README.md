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

أضيف أساس Django وPostgreSQL مستقل واجتاز R03 محليًا وعلى GitHub Actions، مع 9 اختبارات أساس و44 اختبار سياسة. لا واجهات ERP أو دخول بعد. القرار المعتمد: كل حساب يتبع شركة واحدة فقط، ولكل شركة مخططها ومستخدموها وجلساتها. المستودع الجديد https://github.com/Elhussin/osm.git؛ دفع الفرع codex/r03-foundation بإذن المستخدم دون دمجه في main. راجع [دليل التشغيل](docs/rebuild/RUNBOOK.md).

اختبارات السياسة بمفسر Python صالح من جذر المستودع:

```powershell
python -m unittest discover -s rebuild/tests -v
```

يستخدم الإصدار الجديد PDM لإدارة اعتماديات Python وتشغيل أوامر المشروع. راجع قرار `docs/rebuild/decisions/0002-pdm-and-configuration.md` لفصل إدارة الاعتماديات عن إعدادات التطبيق.
