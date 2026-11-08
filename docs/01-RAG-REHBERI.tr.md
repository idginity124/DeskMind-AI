# 1. Ders — RAG sistemini sıfırdan anlamak

## 1) Problemi neden çözüyoruz?

Bir LLM, eğitim sırasında öğrendiği genel bilgilere cevap verebilir. Fakat senin bilgisayarındaki bir notu otomatik olarak bilmez. Ayrıca yanlış veya uydurma bilgiler verebilir. Bu yüzden önce **notların içinden ilgili kanıtı bulup**, ardından modele vermek istiyoruz.

**RAG = Retrieval-Augmented Generation** (bilgi getirme destekli metin üretimi):
1. **Retrieval**: soru ile ilgili belge parçalarını bul.
2. **Augmentation**: bulunan parçaları soruya eklenecek bağlam olarak hazırla.
3. **Generation**: LLM bu bağlama dayanarak yanıt oluştursun.

DeskMind'de LLM isteğe bağlıdır; ilk iki adım tek başına da incelenebilir.

## 2) Chunking nedir?

Büyük belgeler modele bir kerede gönderilmez. `read_chunks` metni küçük bölümlere (**chunk**) ayırır. Komşu iki chunk arasında bazı kelimeler tekrarlanır (**overlap**). Böylece bir bilgi sınırda ikiye bölünse bile belli miktarda bağlam korunur.

Örnek: `A B C D E F G`, chunk boyutu 4, overlap 1:
- `A B C D`
- `D E F G`

Bu uygulamadaki 70 kelimelik bölme başlangıç amaçlıdır. Daha ileri sürümde token temelli ve başlık farkındalıklı bölme yapacağız.

## 3) Embedding neden gerekli?

"Olay müdahalesinin aşamaları" ile "incident response workflow" kelime olarak çok farklıdır. Klasik kelime eşleştirme kaçırabilir.

**Embedding**: bir metni model yardımıyla sabit uzunlukta bir sayı listesine dönüştürmektir. Örneğin gösterim amaçlı `[0.2, -0.1, 0.8]` gibi. Gerçek modelimiz çok daha fazla boyut kullanır. Benzer anlamlı metinlerin vektörlerinin birbirine yakın olması hedeflenir.

Model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 boyut, çok dilli). Model seçimi performans garantisi değil; deneyle ölçeceğiz.

## 4) Cosine similarity nedir?

Vektörlerin yönleri ne kadar benzer diye bakar:

`cosine(a,b) = (a·b) / (||a|| ||b||)`

Bu değer genellikle -1 ile 1 arasındadır; **% başarı ya da olasılık değildir**. Qdrant'ta en yakın vektörleri bulup en ilgili 3 parçayı döndürüyoruz (`top_k=3`).

## 5) Vector database neden kullanılır?

Bir notu indekslemek demek: metin parçasını, vektörünü ve kaynak dosya adını birlikte saklamak demektir. **Qdrant local mode**, ek veritabanı sunucusu açmadan disk üzerinde bunu yapar. Farklı cihazlarda, büyüyen koleksiyonlarda ayrı Qdrant sunucusuna geçilebilir.

`semantic.py index` komutu bu veritabanını kurar. `semantic.py ask` sorunun vektörünü üretir ve en yakın parçaları getirir.

## 6) Ollama ve LLM'nin görevi nedir?

Ollama yerel bir LLM çalıştırmamızı sağlar. Bulunan parçalar `make_prompt` ile modele gönderilir. **Prompt** modele verilen talimat ve bağlam metnidir. `generate_ollama` Ollama'nın yerel API'sini çağırır.

> Belge içinde zararlı veya yanıltıcı komutlar bulunabilir. Prompt içinde "kaynaklar güvenilmiyor" demek tek başına güvenlik garantisi değildir.

## 7) FastAPI nedir?

FastAPI bir Python web API çatısıdır. Tarayıcı `POST /api/ask` ile soruyu iletir, backend JSON cevap döndürür. Tek sayfalık UI bu verileri gösterir. `127.0.0.1`, uygulamanın sadece kendi bilgisayarında erişilebilir olması için kullanılır.

## 8) İlk deneme ve beklenti

1. `python semantic.py index --docs examples/docs`
2. `python semantic.py ask "Olay müdahalesinde ilk aşama nedir?"`
3. Sonuçtaki `source`, `text` ve `score` alanlarına bak.
4. `--ollama-model` eklediğinde nasıl farklı bir yanıt üretildiğini kıyasla.
5. Doğrudan kaynakta cevap olmayan bir soru sor. Modelin gereksiz bir cevap üretip üretmediğini not al.

## 9) Sonraki deney

En az 10 soru hazırlayacağız. Her soru için doğru kaynağı elle işaretleyeceğiz (**ground truth**). Sistem ilk 3 parça içinde doğru kaynağı kaç kez döndürmüş, **Recall@3** ile ölçeceğiz. Sonra daha güçlü embedding modeli ve **reranker** karşılaştıracağız.

## 10) GitHub'a ne koyuyoruz?

Çalışır kod, kurulum, örnek veri, test ve ölçülmüş sonuçları koyuyoruz. Ölçmediğimiz şeyi başarı olarak göstermiyoruz. Özel dosyaları, API anahtarlarını, telifli müşteri verilerini paylaşmıyoruz.
