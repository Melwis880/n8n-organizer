# PROGRESS - n8n_organizer_tool (n8n workflow kütüphanesini bilgi tabanına çeviren araç)

Amaç: Mevcut ~900 satırlık hattı test edilmiş, izlenebilir, İngilizce bir public repo olarak
yayınlamak (kanıt #2). Kararlar: DECISIONS.md.

Durum: [ ] yapılacak, [x] bitti

## Faz 0 - Kurulum
- [x] `git init`, `.gitignore` (`.env*`, `output/`, `logs/`, `input/`, `__pycache__/`, `.venv/`, `*.egg-info/`)
- [x] Paket düzeni: `src/*.py` -> `src/n8n_organizer/`, göreli importlar, `pyproject.toml` (PyYAML==6.0.3, komut `n8n-organizer`)
- [x] CLI: `build --input --output [--log-dir] [--debug]`; `search` -> `NotImplementedError`
- [x] Test altyapısı: `unittest`, `tests/`, `tests/fixtures/`
- [x] `roadmap.md` kaldırılır (başka repodan kopya; Meriç onayıyla); `agent.md` -> `docs/SPEC.md` (Meriç onayıyla)
- [x] PROGRESS.md, DECISIONS.md, CLAUDE.md yerinde (2026-10-02; commit e-postası repo-yerel noreply)
Bitti sayılır: `python -m n8n_organizer --help` iki alt komutu gösteriyor, `python -m unittest discover -s tests` hatasız.
Not: kurulum `pip install -e .`; `--log-dir`/`--debug` bayrakları var, trace Faz 1'de bağlanacak.
**Faz 0 tamam (2026-10-02): 2 test geçiyor; taşınan kod tam veride eski sonucu birebir verdi (2.072 / 2.037 tekil / 35 tekrar / 5 hata).**

## Faz 1 - Trace ve senaryolar
- [x] JSONL trace (`run_id` + `seq`, olay türleri DECISIONS'taki gibi), `--debug` ile stderr
- [x] `tests/SCENARIOS.md` ve her biri için otomatik test:
      1. Normal klasör: workflow'lar kategorilere yazılır
      2. Boş klasör: çökmeden boş özet
      3. Bozuk JSON: atlanır, neden trace'te
      4. Workflow olmayan JSON (liste, `nodes`'suz sözlük): "workflow değil" sayılır, hata değil
      5. 10 MB üstü dosya: atlanır
      6. Sembolik bağ: izlenmez
      7. UTF-8 olmayan dosya: atlanır; BOM'lu dosya okunur
      8. Birebir aynı iki dosya: biri kalır (ham hash)
      9. Sadece id/konum/credentials farklı iki workflow: biri kalır (normalize hash)
      10. Adında `:`, satır sonu, tırnak, kontrol karakteri olan workflow: YAML ve başlık bozulmaz
      11. `...Trigger` tipli düğüm tetikleyici sayılır
      12. Sticky Note ölçümlere girmez
      13. Credentials, parametre, URL ve sticky note metni çıktıda yok
      14. Aynı girdi iki kez: çıktılar birebir aynı
      15. Çıktı klasörü girdinin içinde ya da aynı: çalışmaz, net mesaj
      16. Kelime sınırı aşılınca ikinci dosya açılır
      17. `source_file` göreli, yerel yol yok
      18. Trace'te workflow içeriği yok; her dosya için beklenen olay zinciri var
      19. `search` -> net "henüz yok" hatası
Bitti sayılır: tüm senaryolar testte geçiyor; kasıtlı bozmaların hepsi yakalanıyor; bir çalıştırmanın trace'i beklenen yolu gösteriyor.
Not: senaryolar 20-23 sonradan eklendi (kenar sayımı, sıralı dosya düzeni, eşitlik kuralı, metin temizliği).
**Faz 1 tamam (2026-10-02): 41 test geçiyor; 32 kasıtlı bozmanın 31'i yakalandı, kalan 1'i eşdeğer (skor sözlüğü zaten kategori sırasıyla kuruluyor). Bozmalar 3 eksik test ve 1 ölü kod (backtick kaçışı: JSON satırları çit kapatamaz) buldu, düzeltildi.**

## Faz 2 - Düzeltmeler ve İngilizce çıktı
- [x] Workflow olmayan JSON ayrımı, tetikleyici tespiti, iki adımlı tekrar tespiti, sıralı işleme
- [x] Yeni kategori adları; tüm çıktı metni İngilizce (`CLIENT_PROBLEM_MAP`, açıklamalar, başlıklar)
- [x] Güvenlik kuralları: boyut sınırı, sembolik bağ, UTF-8, çıktı klasörü kontrolü, göreli `source_file`, ad temizliği
Bitti sayılır: tüm test takımı geçiyor; her değişiklikten sonra tüm takım yeniden çalıştı.
Ek düzeltmeler: kapanmayan ```` ```json ```` çiti (ilk workflow'dan sonra her şey kod bloğundaydı), `enricher` `httpsrequest` yazım hatası, `connection_count` artık gerçek kenar sayısı, `traceback` yerine trace + özet. Çıktı klasörü boş olmalı (DECISIONS, Meriç onayı bekliyor).
Tam veri (2026-10-02, ~6 sn): 2.077 dosya, 2.066 workflow, 2.034 tekil, 32 tekrar (1 birebir, 31 normalize), 11 "workflow değil" (package.json, tsconfig, API listeleri), 0 hata. İki çalıştırma birebir aynı. Eski sonuçla fark: eskiden 6 workflow-olmayan dosya boş workflow sayılıyordu (2.072 -> 2.066; tekrarların 3'ü bunlardı).
**Faz 2 tamam (2026-10-02).**

## Faz 3 - Gerçek veri
- [x] Tam Zie619 koleksiyonunda çalıştır (eski: 2.072 dosya, 2.037 tekil, 35 tekrar, 5 "hata"); farkları açıkla
      Bulgu (2026-10-02): güncel koleksiyon bozuk. `f293c236` ("ok") binlerce kopuk `stopAndError` ekledi, `3c0a92c4` ("ssd (#10)") LangChain düğümlerini `noOp`'a çevirdi (adlar kaldı: 320 "OpenAI Chat Model", 180 "AI Agent") ve bağlantıları kırdı (2.123 HTTP Request kopuk). Son temiz sürüm `ae8cf6dc` (2025-09-29): 3.959 LangChain düğümü, 241 kopuk düğüm. Meriç kararı: araç bu sürümle çalışır, `input/zie619-ae8cf6dc/` (git archive, git dışı).
      Temiz veride: 2.057 dosya, 2.047 workflow, 1.973 tekil, 74 birebir tekrar (hepsi aynı klasörde farklı numarayla), 10 workflow değil, 0 hata. Farklı `PYTHONHASHSEED` ile iki çalıştırma birebir aynı.
- [x] Trace'i ve her kategoriden 5 workflow'u elle oku; yanlış sınıflandırma oranını yaz
      Örneklem A (tohum 42, 3x8, ayar için kullanıldı): 16/24 doğru, 2 sinyalsiz; 6 hatanın 5'i LLM adımlı workflow'un HTTP/Sheets/IF tekrarlarıyla başka kategoriye düşmesi. -> LLM adımı kuralı + sinyalsiz için `none` güveni (Meriç kararı). A üzerinde 21/22 (iyimser: ayar örneklemi).
      Örneklem B (tohum 2026, 3x8, bağımsız): sinyalli 20'nin 14'ü doğru (%70); AI_Content 7/8, Data 3/4 (+4 sinyalsiz), Orchestration 4/8. Kalan hatalar: Slack/Telegram düğümü AI puanı veriyor; IF/Merge gibi genel akış düğümleri Orchestration'a çekiyor; çoğu servis düğümünün (Drive, Spotify, QuickBooks, Todoist) Data ağırlığı yok. Dağılım: 796 AI / 810 Data / 367 Orchestration; güven: 1.456 high, 131 medium, 74 low, 312 none.
- [x] Orchestration/Data sınırı için puanlama turu (Meriç "evet", 2026-10-02): mesajlaşma kanalları AI puanı vermez; IF/Switch/Merge/Wait ve dal bonusu puan vermez, Orchestration sinyali webhook/hata/alt workflow; ağırlıksız servis düğümü tip başına Data +2. `linkedin` anahtarı gerçek tip `linkedIn` ile hiç eşleşmiyordu (kaldırıldı).
      Örneklem C (tohum 777, 3x8 sinyalli, bağımsız): 24/24. B'deki 6 hatanın 5'i düzeldi; kalan: AI'a HTTP ile giden workflow (Midjourney) kural tabanlı görülemez - README'de sınır olarak yazılacak. Dağılım: 1.106 Data / 793 AI / 148 Orchestration; güven: 1.906 high, 50 medium, 39 low, 52 none (önce 312). 52 test; yeni koda 9 bozma: 7 yakalandı, 1 ölü koşul (tetikleyici kontrolü) kaldırıldı, 1 liste içeriği.
- [x] Teklif Hazırlayıcı `AGENT.md`'deki çıktı yolunu yeni dosya adlarına güncelle (Meriç onayıyla)
      2026-10-02 (Meriç "evet"): çıktı `output/zie619-ae8cf6dc/` altına üretildi (eski Türkçe `output/*.md` yerinde duruyor, silme ayrı onay); AGENT.md'deki arşiv satırı temiz sürüme ve yeni çıktıya bakıyor. Aynı yolları anlatan skill dosyaları ve context.md için öneri Meriç onayı bekliyor.
Bitti sayılır: gerçek veride hata yok, sayılar ve elle kontrol sonucu PROGRESS'te.
**Faz 3 tamam (2026-10-02).**

## Faz 4 - Dokümantasyon
- [x] İngilizce README: ne ve neden, kurulum, kullanım, kategoriler ve puanlama nasıl açıklanır, çıktı formatı, sınırlar
- [x] LICENSE (MIT); `examples/` 3-5 Zie619 workflow'unun çıktısı + `examples/NOTICE` (MIT atfı)
      4 workflow, her kategoriden bir `high` + bir `none` örneği (Splitout/1564, Filter/1667, Error/0456, Manual/0943); sadece çıktı, workflow JSON'u repoda yok. İki üretim birebir aynı.
- [x] CASE_STUDY.md (İngilizce): Hangi sorunu çözüyor? Nasıl çalışıyor? Somut sonucu ne? (sadece ölçülen sayılar)
      Tekil sayılar (1.973): 1.080 Data / 746 AI / 147 Orchestration; güven 1.838 high, 48 medium, 37 low, 50 none (Ek 2'den önce; güncel sayılar aşağıda). Çalışma ~10 sn (i7-1255U).
- [x] CI: `.github/workflows/test.yml` (Python 3.10-3.13)
      Yerelde 3.12 ve 3.13'te 52 test geçti; 3.11+ özelliği yok (grep). GitHub'da gerçek koşu Faz 5'te doğrulanacak. `pyproject` build alt sınırı `setuptools>=77` (SPDX `license = "MIT"` için); wheel'de LICENSE ve `License-Expression: MIT` var.
Bitti sayılır: projeyi bilmeyen biri README ile 5 dakikada `build` çalıştırabiliyor.
Doğrulama (2026-10-02): temiz kopya + yeni venv'de README adımları birebir izlendi: kurulum, klon, `git archive`, `build` toplam 108 sn; çıktı `output/zie619-ae8cf6dc/` ile birebir aynı.
**Faz 4 tamam (2026-10-02).**
Ek (2026-10-03, Meriç "evet"): Faz 4'te bulunan 4 küçük çıktı kusuru düzeltildi, `analysis_version` 2.1.0 (DECISIONS). Tam veride sınıflandırma (kategori, ikincil, güven, puanlar) 2.047 workflow'da birebir aynı, karmaşıklık aynı; servis listesi boş profil 447 -> 75, `agentic_ai` 719 -> 362, `ai_generation` 585 -> 723, `name: ""` 968 -> 0. Farklı `PYTHONHASHSEED` ile iki çalıştırma birebir aynı. 62 test (senaryo 30-33); 13 bozmanın 12'si yakalandı, kalan 1'i eksik testi gösterdi (eklendi). `examples/` yeniden üretildi.
Ek 2 (2026-10-03, Meriç "evet"): 9 yardımcı/demo düğüm tipi çekirdek listeye alındı (DECISIONS). 2.047 workflow'un 13'ü (12 tekil) değişti, hepsi elle okundu: 10 demo/rehber (TOTP, quickstart, Read PDF, demo veri döngüleri) `high` -> `none` (doğru); 1591 Data -> Orchestration (doğru: n8n bağımlılık grafiğini webhook'tan sunuyor); 0499 ikincil Data düştü (doğru); 0260 (kazıyıp webhook'tan RSS sunan) Orchestration'da kaldı, güveni medium -> high - Data daha doğru olurdu, eski tartışmalı karar. Yeni sayılar (tekil): 1.079 Data / 746 AI / 148 Orchestration; güven 1.830 high, 47 medium, 37 low, 59 none; 741.408 kelime. `examples/` değişmedi. 63 test; 2 bozma yakalandı.
Ek 3 (2026-10-03, Meriç "evet"): audit öncesi kontrol iki bulgu çıkardı. (1) `vectorStore` ağırlık anahtarı gerçek tiplerle (`vectorStoreQdrant`...) hiç eşleşmiyordu -> önek eşleşmesi (`NODE_PREFIX_WEIGHTS`), senaryo 34, 3 test; 4 bozmanın 4'ü yakalandı. Tam veride 1.973 profilde kategori/ikincil/güven/etiket/servis/karmaşıklık birebir aynı, özet aynı; sadece puan ve gerekçe satırları değişti; 741.857 kelime. `analysis_version` 2.1.1. (2) CASE_STUDY test sayısı 62 -> 66 (bozma sayımı 54/50 + Ek 2'deki 2 + bu 4 = 60/56). `examples/` ve `output/zie619-ae8cf6dc/` yeniden üretildi.

## Faz 5 - Yayın
- [x] Temiz oturumda `security-audit` -> `security.md`
      2026-10-03: risk Medium; sır yok, geçmiş ve commit e-postaları temiz, `input/` `output/` `logs/` git dışı. 4 Medium (UTF-8 olmayan dosya adı çalıştırmayı çökertiyor; `summary.txt`'ye mutlak yol sızıyor; adlarda Markdown/HTML enjeksiyonu; aşağı akış LLM'e prompt injection), 6 Low. Düzeltme yapılmadı.
- [ ] Temiz oturumda `optimize` -> `OPTIMIZATIONS.md`
- [x] Önemli bulguları düzelt, tüm testleri yeniden çalıştır
      2026-10-03 (Meriç "evet", `optimize`'dan önce): security.md'deki 10 bulgunun hepsi düzeltildi ya da azaltıldı (her birinde durum notu var). Metadata ```` ```yaml ```` bloğunda (Meriç seçimi), SHA-256, "untrusted data" notu, Markdown kaçışı, `unsafe_file_name` / `not_regular_file`, `O_NOFOLLOW`, `open("x")`, yolsuz hata satırı, tip/ad doğrulama, ince kayıtlar. `analysis_version` 2.2.0. 80 test (senaryo 35-43); 20 bozmanın 18'i yakalandı, 1'i eksik test (eklendi), 1'i eşdeğer. Tam veride 1.973 profilde sınıflandırma alanları ve yerleşim birebir aynı, `summary.txt` aynı, iki çalıştırma birebir aynı, ~11 sn; 741.917 kelime (`wc -w`). `examples/` yeniden üretildi (HEAD ile üretim yönteminin eski örnekleri birebir verdiği doğrulandı). `output/zie619-ae8cf6dc/` silinip 2.2.0 ile yeniden üretildi (Meriç "evet"); doğrulanan çalıştırmayla birebir aynı. `security.md` yerelde kalır, `.gitignore`'da (Meriç kararı: public repoda güvenlik zaafiyeti ayrıntısı olmasın).
- [x] Commit e-postası GitHub noreply (repo-yerel `user.email`, ilk commit'ten önce)
      2026-10-03 security-audit'te doğrulandı: 8 commit'in hepsinde yazar ve committer noreply.
- [ ] GitHub repo adı kararı (Meriç), `v0.1.0` etiketi
- [ ] Sadece Meriç'in açık "evet"inden sonra: GitHub reposu ve gönderim; CI'ın geçtiğini doğrula
- [ ] Kanıt listesine ekleme sorusu (context.md "Public proof"), Meriç "evet" derse
Bitti sayılır: public repo README ve çalışan CI ile yayında.
