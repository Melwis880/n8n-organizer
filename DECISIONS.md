# DECISIONS - n8n_organizer_tool

Her satır: karar - neden. Bir karar değişecekse önce Meriç'e sorulur, sessizce değişmez.

## Amaç ve kapsam
- Araç, bir klasördeki n8n workflow JSON'larını kurallara dayalı, açıklanabilir puanlarla sınıflandırıp kategori başına NotebookLM'e uygun Markdown bilgi tabanı üretir - müşteri işini kapsamlarken desen bulmak için (Teklif Hazırlayıcı da bu çıktıyı okur).
- v1'de LLM, embedding ya da ağ erişimi yok - sonuç tekrarlanabilir ve ücretsiz olmalı (agent.md Non-Goals).
- Herkese açık repo, kanıt #2 (context.md "Public proof"); README, CLAUDE.md ve tüm çıktı metni İngilizce - global pazar.

## Teknoloji
- Python >= 3.10, paket düzeni `src/n8n_organizer/` + `pyproject.toml`, komut `n8n-organizer` ve `python -m n8n_organizer` - flx ile aynı düzen, `pip install -e .` ile kurulur.
- Tek bağımlılık PyYAML, sürüm sabit (`PyYAML==6.0.3`); sadece `yaml.safe_dump` kullanılır - workflow adları gibi güvenilmeyen metni doğru kaçırır; elle YAML yazmak kaçış hatalarına açık (Meriç kararı, 2026-10-02). Başka bağımlılık eklenmez.
- Test: standart `unittest`, ağ yok, uydurma workflow JSON'ları `tests/fixtures/` altında.
- CLI: `argparse` alt komutları: `build` (mevcut hat), `search` (yer tutucu, `NotImplementedError`) - arama indeksi ileride gelecek (Meriç kararı, 2026-10-02).

## Veri akışı
- `build --input DIR --output DIR`: tara -> yükle -> workflow mu kontrol et -> normalize et -> ölç ve puanla -> tekrarları ele -> kategori dosyalarını ve `summary.txt`'yi yaz.
- Dosyalar sıralı yol düzeninde işlenir - aynı girdi her çalıştırmada birebir aynı çıktıyı verir (deterministik kural).
- Workflow tanımı: kökü sözlük olan ve `nodes` listesi taşıyan JSON. Değilse "workflow değil, atlandı" diye sayılır, hata sayılmaz (eski 5 "hata" bunlardı).
- Tekrar tespiti iki adımlı: önce ham hash (birebir aynı dosya), sonra normalize hash (id, konum, credentials, webhookId farkı yok sayılır); ilk görülen (yol sırasına göre) kalır, tekrar kaydı trace'e "kime ait" bilgisiyle yazılır - agent.md Kural 2.
- Tetikleyici tespiti: sabit listeye ek olarak tipi `Trigger` ile biten her düğüm - eski kod `telegramTrigger` gibi tipleri kaçırıyordu.
- Sticky Note düğümleri ölçümlere (düğüm sayısı, karmaşıklık) girmez - bunlar yorum, iş adımı değil.
- Kategoriler: `Data_Integration`, `AI_Content`, `Orchestration_Reliability`; çıktı dosyası `<n>-<Category>.md` - "SEO" ve "Security" adları yanlış konumlandırıyordu (Meriç kararı, 2026-10-02).
- Kategori dosyası kelime sınırı 450.000; aşınca `2-<Category>.md` açılır - NotebookLM kaynak sınırı.
- `connection_count` gerçek kenar sayısıdır (tüm çıkış türleri: `main`, `ai_*`); eski kod çıkış yuvası sayıyordu - AI workflow'larının bağlantıları `ai_languageModel` gibi türlerde (Claude düzeltmesi, 2026-10-02).
- Kategori eşitliğinde sabit sıra kazanır: Data_Integration, AI_Content, Orchestration_Reliability; hiçbir sinyal yoksa Data_Integration + `low` güven - deterministik kural (Claude, 2026-10-02).
- Çıktı biçimi değiştiği için `analysis_version` 2.0.0 (Claude, 2026-10-02).

## Güvenlik ve erişim
- Ağ erişimi yok; araç hiçbir JSON içeriğini çalıştırmaz, sadece veri olarak okur.
- Sadece `--input` altını okur; sembolik bağlar izlenmez ve atlanır - girdi klasörünün dışına çıkılmasın.
- 10 MB'tan büyük JSON atlanır (trace'e neden yazılır) - bozuk ya da kötü niyetli dev dosya belleği doldurmasın.
- Metin UTF-8 (BOM'lu da) okunur; çözülemeyen dosya atlanır - eski `errors="ignore"` veriyi sessizce bozuyordu.
- Sadece `--output` altına yazar; çıktı klasörü girdi klasörünün içindeyse ya da aynıysa çalışmaz - bir sonraki taramada kendi çıktısını okumasın.
- Çıktı klasörü boş olmalı ya da henüz olmamalı; doluysa araç çalışmaz, hiçbir dosyayı silmez ya da üzerine yazmaz - eski parçalı dosyalar (`2-...md`) yeni çıktıya karışmasın ve araç kullanıcı dosyasını silmesin (Claude önerisi, 2026-10-02; Meriç onayı bekliyor).
- Çıktıya sadece düğüm adı ve tipi, servis adları, ölçümler, hash'ler girer; parametreler, credentials, sticky note metni ve URL'ler asla girmez - agent.md Kural 4, workflow'larda gömülü anahtar olabilir.
- `source_file` girdi köküne göre göreli yazılır - makinedeki yerel yollar çıktıya sızmasın.
- Workflow adları güvenilmeyen metin: YAML'a `safe_dump` ile, Markdown başlıklarına kontrol karakterleri ve satır sonları temizlenerek yazılır.
- Sır yok: araç anahtar kullanmaz; yine de `.gitignore` `.env*` kapsar.

## İzlenebilirlik
- Her çalıştırma `--log-dir` (varsayılan `./logs`) altına `YYYY-MM-DD.jsonl` trace yazar: `run_id` + `seq`; her dosya için bulundu / yüklendi / atlandı (neden) / puanlandı (puanlar) / tekrar (kime ait) / yazıldı (hangi dosya). Workflow içeriği trace'e girmez, sadece yol, ad, hash ve sayılar.
- `--debug` aynı trace satırlarını stderr'e de basar.
- `traceback` ekrana basılmaz; hata trace'e ve `summary.txt`'ye nedeniyle yazılır.

## Repo içeriği
- Testler uydurma JSON'larla; `examples/` altında Zie619 koleksiyonundan 3-5 workflow'un gerçek çıktısı, MIT atfıyla (`examples/NOTICE`) (Meriç kararı, 2026-10-02).
- Tam çıktı (`output/`), `logs/`, `input/` git'e girmez.
- Lisans MIT.
