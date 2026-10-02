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
- LLM adımı kuralı: workflow'da herhangi bir LangChain düğümü (`@n8n/n8n-nodes-langchain.*`) ya da tipinde `openai` geçen bir düğüm varsa ana kategori AI_Content, güven `high`; ikincil kategori puanlardan gelir - elle kontrolde 6 hatanın 5'i, tekrar eden HTTP/Sheets/IF düğümlerinin LLM adımını geçmesiydi; kural örneklemde doğruluğu 16/24'ten 21/22'ye çıkardı (Meriç kararı, 2026-10-02).
- Mesajlaşma kanalları (Slack, Telegram, Twitter, LinkedIn) AI puanı vermez; servis sayılır - AI değil kanal; "Zendesk-to-slack" AI'a düşüyordu (Meriç kararı, 2026-10-02).
- Genel akış düğümleri (IF, Switch, Merge, Wait) ve "2+ dal" bonusu puan vermez; Orchestration sinyalleri: webhook, respondToWebhook, errorTrigger, executeWorkflow, executeWorkflowTrigger, stopAndError - senkron işler dal düğümleri yüzünden Orchestration'a düşüyordu (Meriç kararı, 2026-10-02).
- Ağırlığı olmayan her `n8n-nodes-base.*` servis düğümü (çekirdek liste `CORE_NODE_TYPES` dışı) tip başına bir kez Data_Integration +2 - Drive, Spotify, QuickBooks gibi senkron düğümlerinin hiç Data sinyali yoktu (Meriç kararı, 2026-10-02).
- Hiç puan almayan workflow Data_Integration'a düşer ama güveni `none` olur ve gerekçe satırı bunu söyler - kategori ve dosya adları değişmesin, okuyan bunun tahmin olmadığını görsün (Meriç kararı, 2026-10-02).
- Çıktı biçimi değiştiği için `analysis_version` 2.0.0 (Claude, 2026-10-02).

## Güvenlik ve erişim
- Ağ erişimi yok; araç hiçbir JSON içeriğini çalıştırmaz, sadece veri olarak okur.
- Sadece `--input` altını okur; sembolik bağlar izlenmez ve atlanır - girdi klasörünün dışına çıkılmasın.
- 10 MB'tan büyük JSON atlanır (trace'e neden yazılır) - bozuk ya da kötü niyetli dev dosya belleği doldurmasın.
- Metin UTF-8 (BOM'lu da) okunur; çözülemeyen dosya atlanır - eski `errors="ignore"` veriyi sessizce bozuyordu.
- Sadece `--output` altına yazar; çıktı klasörü girdi klasörünün içindeyse ya da aynıysa çalışmaz - bir sonraki taramada kendi çıktısını okumasın.
- Çıktı klasörü boş olmalı ya da henüz olmamalı; doluysa araç çalışmaz, hiçbir dosyayı silmez ya da üzerine yazmaz - eski parçalı dosyalar (`2-...md`) yeni çıktıya karışmasın ve araç kullanıcı dosyasını silmesin (Meriç kararı, 2026-10-02).
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

## Veri kaynağı
- Araç, Zie619/n8n-workflows koleksiyonunun `ae8cf6dc` (2025-09-29) sürümüyle çalıştırılır; `git archive` ile `input/zie619-ae8cf6dc/` altına çıkarılır (git'e girmez, n8n-workflows reposuna dokunulmaz) - sonraki commit'ler koleksiyonu bozdu: `f293c236` ("ok") binlerce kopuk `stopAndError` düğümü ekledi (8.791 kopuk), `3c0a92c4` ("ssd (#10)") LangChain düğümlerini `noOp`'a çevirdi ve bağlantıları kırdı. Kanıt: trace ve tip sayımları (PROGRESS Faz 3) (Meriç kararı, 2026-10-02).
- Koleksiyonun MIT lisansı `75cb1e57` (2025-11-03) ile eklendi; aynı workflow'lar lisanslı sürümde de var, atıf bu lisansa yapılır.
