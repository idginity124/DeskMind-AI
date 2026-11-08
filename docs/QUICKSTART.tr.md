# DeskMind AI — Türkçe hızlı başlangıç

Bu proje yerel belgelerde anlam tabanlı arama yapar. İsteğe bağlı olarak Ollama'daki bir LLM ile yanıt oluşturabilir.

## CachyOS / Fish

```fish
cd ~/Downloads/-DeskMind-AI
bash scripts/setup-linux.sh
bash scripts/run-local.sh
```

Tarayıcıda `http://127.0.0.1:8000` adresini aç.

1. **Demo:** İlk açılışta `Örnek belgeleri hazırla` düğmesine bas. İndeksleme bitince soru sor.
2. **Kütüphanem:** PDF/TXT/Markdown yükle. Belgeler `.deskmind/workspaces/personal/documents` altında kalır.
3. Soru sor. Kaynakları ve benzerlik skorlarını kontrol et.
4. `ollama pull qwen2.5:3b` kurduysan model alanına `qwen2.5:3b` yaz; aksi takdirde alanı boş bırak.

> **Önemli:** `uvicorn` komutunda `127.0.0.1` adresini kullan. Bu sürümde giriş sistemi yoktur; ağdaki herkese açık hâle getirme.

## Kavram sözlüğü

| Terim | Açıklaması |
| --- | --- |
| Embedding | Metni vektör (sayısal temsil) olarak kodlama |
| Indexing | Bu vektörleri aramaya hazır saklama |
| Chunk | Metin parçası; büyük dosyayı küçük birimlere ayırır |
| Retrieval | Soruyla en alakalı belge parçalarını bulma |
| Generation | LLM ile bulunan belgelere dayalı yanıt oluşturma |
| RAG | Retrieval + Generation sistemini bağlamla birleştirme |
| Grounding | Yanıtı kaynak metinlerle temellendirme |
| Test double | Gerçek model yerine testte kontrollü sahte bileşen kullanma |

## Bilinen kısıtlamalar

PDF'nin taranmış görüntü olması durumunda OCR olmadığı için yükleme reddedilir. Her dosya en fazla 8 MB; PDF en fazla 100 sayfa olabilir. Yükleme/silme işlemi şu an tüm kişisel kütüphaneyi yeniden indeksler. İnternet yalnızca ilk embedding modeli indirmesinde gerekir; yerel Ollama kullanırsan belgeler üçüncü taraf API'lerine gönderilmez. Ancak model cevapları hâlâ hata yapabilir; referans pasajları her zaman kontrol et.

## Kodları GitHub'a yükleme

Bu sürümün GitHub'da ayrı bir `-DeskMind-AI` deposu olarak yayımlanması önerilir. Ayrıntılı adımlar için [Yayın rehberine](PUBLISH.md) bak. `.venv`, `.deskmind` veya kendi özel PDF dosyalarını Git'e ekleme.

## Kalite ölçümü

Demo indeksi oluşturduktan sonra `python benchmark.py --top-k 3` çalıştır. Recall@K, MRR ve ortalama sorgu süresi değerlerini göreceksin. Örnek kümesi çok küçük olduğu için bu sayılar gerçek dünyadaki genel başarıyı göstermez.
