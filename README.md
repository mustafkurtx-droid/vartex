# Vartex - Çoklu Varlık Risk Analiz ve Portföy Yönetim Sistemi

**Vartex**, hisse senetlerinin risk metriklerini deterministik yöntemler ve olasılıksal simülasyonlar kullanarak analiz eden, PyPI güvenlik denetimlerine sahip, esnek portföy çeşitlendirmesi sunan modüler bir risk yönetim sistemidir.

---

## 🚀 Temel Özellikler

1. **Güvenlik & Bağımlılık Kontrolü:** Typosquatting ve halüsinasyon kütüphane risklerine karşı `requirements.txt` dosyasını PyPI JSON API'si üzerinden otomatik doğrular.
2. **Deterministik Risk Metrikleri:** Logaritmik getiriler üzerinden Volatilite, Sharpe Oranı, Maksimum Tarihsel Kayıp (Max DD) ve Tarihsel VaR (%95/%99) hesaplar.
3. **Kritik Risk Geçitleri (Human-in-the-Loop):** Belirlenen risk eşikleri aşıldığında onay mekanizmasını devreye alır.
4. **Olasılıksal Projeksiyon:** Geometrik Brownian Motion (GBM) modeliyle 10,000 denemeli Monte Carlo simülasyonları gerçekleştirir.
5. **Çoklu Varlık Portföy Modu (--portfolio):** N adet varlık arasındaki korelasyon matrisini hesaplar, eşit ağırlıklı portföy riski ile tekil riskleri karşılaştırıp **dolar bazında çeşitlendirme faydasını (risk kazancını)** sunar.
6. **Zengin Terminal Arayüzü (Rich):** CLI ekranında renk kodlu özet paneller, korelasyon analizleri ve tablolar basar.

---

## 🛠️ Kurulum ve Çalıştırma

### 1. Sanal Ortamı Aktif Edin
* **Windows PowerShell:**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **Windows CMD:**
  ```cmd
  venv\Scripts\activate.bat
  ```

### 2. Tek Hisse Analiz Modu
```bash
python main.py THYAO.IS
```

### 3. Çoklu Varlık Portföy Risk Karşılaştırma Modu
```bash
python main.py --portfolio THYAO.IS AAPL GARAN.IS MSFT GOOGL --amount 10000 --no-interactive
```

---
*Bu sistem tamamen Python numpy, pandas, matplotlib ve rich kütüphaneleriyle yazılmış olup, yatırım tavsiyesi içermez.*
