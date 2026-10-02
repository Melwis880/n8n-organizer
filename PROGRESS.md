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
- [ ] Tam Zie619 koleksiyonunda çalıştır (eski: 2.072 dosya, 2.037 tekil, 35 tekrar, 5 "hata"); farkları açıkla
- [ ] Trace'i ve her kategoriden 5 workflow'u elle oku; yanlış sınıflandırma oranını yaz
- [ ] Teklif Hazırlayıcı `AGENT.md`'deki çıktı yolunu yeni dosya adlarına güncelle (Meriç onayıyla)
Bitti sayılır: gerçek veride hata yok, sayılar ve elle kontrol sonucu PROGRESS'te.

## Faz 4 - Dokümantasyon
- [ ] İngilizce README: ne ve neden, kurulum, kullanım, kategoriler ve puanlama nasıl açıklanır, çıktı formatı, sınırlar
- [ ] LICENSE (MIT); `examples/` 3-5 Zie619 workflow'unun çıktısı + `examples/NOTICE` (MIT atfı)
- [ ] CASE_STUDY.md (İngilizce): Hangi sorunu çözüyor? Nasıl çalışıyor? Somut sonucu ne? (sadece ölçülen sayılar)
- [ ] CI: `.github/workflows/test.yml` (Python 3.10-3.13)
Bitti sayılır: projeyi bilmeyen biri README ile 5 dakikada `build` çalıştırabiliyor.

## Faz 5 - Yayın
- [ ] Temiz oturumda `security-audit` -> `security.md`
- [ ] Temiz oturumda `optimize` -> `OPTIMIZATIONS.md`
- [ ] Önemli bulguları düzelt, tüm testleri yeniden çalıştır
- [ ] Commit e-postası GitHub noreply (repo-yerel `user.email`, ilk commit'ten önce)
- [ ] GitHub repo adı kararı (Meriç), `v0.1.0` etiketi
- [ ] Sadece Meriç'in açık "evet"inden sonra: GitHub reposu ve gönderim; CI'ın geçtiğini doğrula
- [ ] Kanıt listesine ekleme sorusu (context.md "Public proof"), Meriç "evet" derse
Bitti sayılır: public repo README ve çalışan CI ile yayında.
