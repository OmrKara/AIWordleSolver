# Wordle Entropy Solver

Projede hem Tkinter masaüstü oyunu hem de tarayıcıda çalışan yerel Wordle sürümü bulunur. Web sürümündeki AI tahmini, projedeki Shannon entropy stratejisini kullanır;

## Canlı site

[Wordle Entropy Solver'ı oyna](https://aiwordlesolver.onrender.com/)

## Yerel web sitesini çalıştırma

```powershell
python server.py
```

Sunucu `http://127.0.0.1:8766` adresinde açılır ve varsayılan tarayıcıda siteyi gösterir. Durdurmak için sunucu penceresinde `Ctrl+C` kullan.

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

