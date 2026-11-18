# Wordle Entropy Solver

Projede hem Tkinter masaüstü oyunu hem de tarayıcıda çalışan yerel Wordle sürümü bulunur. Web sürümündeki AI tahmini, projedeki Shannon entropy stratejisini kullanır; hesaplama tarayıcıdaki Web Worker'da yapılır ve dış API kullanılmaz.

## Yerel web sitesini çalıştırma

```powershell
python server.py
```

Sunucu `http://127.0.0.1:8766` adresinde açılır ve varsayılan tarayıcıda siteyi gösterir. Durdurmak için sunucu penceresinde `Ctrl+C` kullan.

## Render'da ücretsiz yayımlama

Web oyunu sadece HTML, CSS, JavaScript, Web Worker ve iki statik kelime dosyasından oluşur. Bu nedenle Render'da uykuya geçen bir Python web servisi yerine ücretsiz statik site olarak yayımlanır. `render.yaml`, Render Blueprint ayarlarını içerir; build sırasında yalnızca web sitesi dosyalarını `dist/` klasörüne kopyalar. Masaüstü uygulaması, PDF raporlar ve simülasyon kodu yayımlanmaz.

1. Değişiklikleri mevcut `origin` GitHub deposuna commit edip push et. Örnek komutlar:

   ```powershell
   git add .
   git commit -m "Prepare Wordle web app for Render"
   git push origin HEAD
   ```

2. Render Dashboard'da **New → Blueprint** seçip GitHub deposunu bağla. Render kökteki `render.yaml` dosyasını bulup `wordle-entropy-ai` statik sitesini yapılandırır.
3. Blueprint değişikliklerini onaylayıp dağıtımı başlat. Render siteye bir `onrender.com` adresi verir; sonraki gönderimler otomatik dağıtılır.

Render statik siteleri ücretsiz yayımlanır ve CDN üzerinden sunulur. Trafik ve build süreleri çalışma alanının dahil olan aylık kullanım miktarlarına sayılır. Ayrıntılar: [Static Sites](https://render.com/docs/static-sites), [Blueprint YAML](https://render.com/docs/blueprint-spec), [Deploy for Free](https://render.com/docs/free).

Web oyunu altı tahmin hakkı, fiziksel ve ekran klavyesi, yeni oyun düğmesi ve AI tahmini içerir. AI düğmesi ilk turda projedeki sabit `SOARE` başlangıç kelimesini, sonraki turlarda en yüksek entropy değerine sahip kelimeyi boş satıra yazar. Öneriyi göndermek için Enter kullanılır. AI çalışırken oyun penceresi yanıt vermeye devam eder.

## Masaüstü oyununu çalıştırma

```powershell
python wordle.py
```

## Çözücü simülasyonu

```powershell
python test_wordle_entropy.py
python test_wordle_entropy.py --all-answers
```

Varsayılan olarak `441` tohumu ile cevap listesinden 100 tekrarlanabilir örnek seçilir. `--games N` ve `--seed N` örneklemi değiştirir. `--all-answers` özgün 2.315 cevap kelimesinin tamamını tarar. Sonuçlar `wordle_entropy_test_results.txt` dosyasına kaydedilir.

## Kelime listeleri

`eng_dict.txt` geçerli tahminleri, `answers.txt` ise olası gizli cevapları içerir. Kaynak ve kapsam bilgisi [WORDLIST_SOURCES.md](WORDLIST_SOURCES.md) dosyasındadır. Cevap listesi özgün Wordle listesi olup canlı NYT günlük cevap akışı değildir.

## Rapor metrikleri

Ekli son rapordaki 100 oyun ve 3,87 ortalama tahmin ölçümü eski test yöntemine aittir. O test cevap ve tahmin havuzunu tek listede birleştirip alfabetik ilk 100 kelimeyi seçiyordu. Mevcut kod havuzları ayırır ve örneklemi tüm cevap listesine yayar; güncel performans değerleri için simülasyon yeniden çalıştırılmalıdır.
