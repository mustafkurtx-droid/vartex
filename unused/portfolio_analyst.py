import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def main():
    if len(sys.argv) < 3:
        print("Hata: En az iki hisse kodu belirtilmelidir.")
        sys.exit(1)
        
    ticker1 = sys.argv[1]
    ticker2 = sys.argv[2]
    report_file = sys.argv[3] if len(sys.argv) > 3 else f"portfolio_report_{ticker1}_{ticker2}.md".replace(".", "_")
    
    clean_t1 = ticker1.replace(".", "_")
    clean_t2 = ticker2.replace(".", "_")
    
    csv1 = f"{clean_t1}_data.csv"
    csv2 = f"{clean_t2}_data.csv"
    
    if not os.path.exists(csv1) or not os.path.exists(csv2):
        print(f"Hata: Analiz için gerekli veri dosyaları ({csv1} veya {csv2}) bulunamadı.")
        sys.exit(1)
        
    # 1. Verileri yükle
    df1 = pd.read_csv(csv1, parse_dates=['Date'], index_col='Date').dropna(subset=['Close'])
    df2 = pd.read_csv(csv2, parse_dates=['Date'], index_col='Date').dropna(subset=['Close'])
    
    # Kapanış fiyatlarını birleştir
    df = pd.merge(df1[['Close']], df2[['Close']], left_index=True, right_index=True, suffixes=('_1', '_2'))
    
    if df.empty:
        print("Hata: İki hisse senedinin kesişen tarihli verisi bulunamadı.")
        sys.exit(1)
        
    # 2. Logaritmik getirileri hesapla
    df['Return_1'] = np.log(df['Close_1'] / df['Close_1'].shift(1))
    df['Return_2'] = np.log(df['Close_2'] / df['Close_2'].shift(1))
    df = df.dropna()
    
    # Korelasyon katsayısı
    correlation = df['Return_1'].corr(df['Return_2'])
    
    # 3. Portföy getirilerini oluştur (%50-%50)
    df['Port_Return'] = 0.5 * df['Return_1'] + 0.5 * df['Return_2']
    
    # Tekil metrikler
    vol1 = df['Return_1'].std() * np.sqrt(252)
    vol2 = df['Return_2'].std() * np.sqrt(252)
    
    # Portföy metrikleri
    port_vol = df['Port_Return'].std() * np.sqrt(252)
    mean_return = df['Port_Return'].mean() * 252
    port_sharpe = mean_return / port_vol if port_vol != 0 else 0.0
    
    var_95_hist = -np.percentile(df['Port_Return'], 5)
    var_99_hist = -np.percentile(df['Port_Return'], 1)
    
    # Maksimum Drawdown hesaplama (Portföy Değeri bazlı)
    port_prices = 5000 * (df['Close_1'] / df['Close_1'].iloc[0]) + 5000 * (df['Close_2'] / df['Close_2'].iloc[0])
    roll_max = port_prices.cummax()
    drawdown = (port_prices - roll_max) / roll_max
    max_dd = drawdown.min()
    
    # 4. Portföy Monte Carlo Simülasyonu (21 Günlük, 10,000 deneme)
    mu = df['Port_Return'].mean()
    sigma = df['Port_Return'].std()
    S0 = 10000
    dt = 1
    N_days = 21
    M_paths = 10000
    
    np.random.seed(42)
    paths = np.zeros((N_days + 1, M_paths))
    paths[0] = S0
    
    for t in range(1, N_days + 1):
        paths[t] = paths[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * np.random.normal(0, 1, M_paths))
        
    final_prices = paths[-1]
    mc_losses = S0 - final_prices
    mc_losses_pct = mc_losses / S0
    
    var_95_mc_1d = -(np.exp((mu - 0.5 * sigma**2) + sigma * np.percentile(np.random.normal(0, 1, M_paths), 5)) - 1)
    var_99_mc_1d = -(np.exp((mu - 0.5 * sigma**2) + sigma * np.percentile(np.random.normal(0, 1, M_paths), 1)) - 1)
    
    var_95_mc_21d = np.percentile(mc_losses_pct, 95)
    var_99_mc_21d = np.percentile(mc_losses_pct, 99)
    
    # 5. Grafik çizimi ve kaydetme
    chart_name = f"portfolio_{clean_t1}_{clean_t2}_monte_carlo.png"
    plt.figure(figsize=(10, 6))
    plt.plot(paths[:, :100], lw=1, alpha=0.6)
    plt.title(f"Portföy Monte Carlo 21 Günlük Projeksiyonu (%50 {ticker1} / %50 {ticker2})")
    plt.xlabel("İşlem Günü")
    plt.ylabel("Portföy Değeri ($)")
    plt.axhline(S0, color='black', linestyle='--', label='Başlangıç ($10k)')
    plt.grid(True, alpha=0.3)
    plt.savefig(chart_name, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Dağılım grafiği
    hist_name = f"portfolio_{clean_t1}_{clean_t2}_mc_returns_histogram.png"
    plt.figure(figsize=(10, 6))
    plt.hist(mc_losses_pct * 100, bins=50, alpha=0.75, color='royalblue', edgecolor='black')
    plt.axvline(var_95_mc_21d * 100, color='orange', linestyle='--', lw=2, label=f'%95 MC VaR: %{var_95_mc_21d*100:.2f}')
    plt.axvline(var_99_mc_21d * 100, color='red', linestyle='--', lw=2, label=f'%99 MC VaR: %{var_99_mc_21d*100:.2f}')
    plt.title(f"Portföy 21 Günlük Monte Carlo Kayıp Dağılımı (%50 {ticker1} / %50 {ticker2})")
    plt.xlabel("Portföy Değer Kaybı (%)")
    plt.ylabel("Deneme Frekansı")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(hist_name, dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. Rapor yazma
    corr_desc = ""
    if correlation > 0.7:
        corr_desc = "Çok yüksek pozitif korelasyon. İki hisse senedi hemen hemen aynı yönlü hareket etmektedir. Çeşitlendirme faydası oldukça sınırlıdır."
    elif correlation > 0.3:
        corr_desc = "Orta düzeyde pozitif korelasyon. Kısmi bir çeşitlendirme koruması sağlar, ancak piyasa düşüşlerinde birlikte hareket etme eğilimleri mevcuttur."
    elif correlation > -0.1 and correlation <= 0.3:
        corr_desc = "Düşük korelasyon. Çok iyi bir çeşitlendirme faydası sağlar. Hisselerden birindeki düşüş diğerinin hareketiyle dengelenebilir."
    else:
        corr_desc = "Negatif korelasyon. Mükemmel bir çeşitlendirme koruması sağlar. Portföy oynaklığı ciddi şekilde dengelenir."
        
    report_content = f"""# Portföy Risk Senaryoları Raporu ($10,000 Yatırım)

Bu rapor, **{ticker1}** ve **{ticker2}** hisse senetlerine eşit ağırlıklı (%50 - %50) olarak yapılan **10,000 $** tutarındaki bir yatırım portföyünün risk metriklerini ve gelecek projeksiyonlarını içerir.

## Portföy Yapısı ve Temel Korelasyon

| Parametre | Değer | Açıklama |
| :--- | :--- | :--- |
| **Varlık 1 ({ticker1}) Ağırlığı** | %50.00 (5,000 $) | Portföye ayrılan birinci hisse senedi tutarıdır. |
| **Varlık 2 ({ticker2}) Ağırlığı** | %50.00 (5,000 $) | Portföye ayrılan ikinci hisse senedi tutarıdır. |
| **Korelasyon Katsayısı ($r$)** | {correlation:.4f} | İki hisse senedinin günlük getirilerinin doğrusal ilişkisidir. |

> **Korelasyon Analizi:** {corr_desc}

---

## Karşılaştırmalı Risk Metrikleri Tablosu

Aşağıdaki tablo, tekil hisse senetlerinin riskleri ile oluşturulan çeşitlendirilmiş portföyün risk metriklerini karşılaştırmaktadır.

| Risk Metriği | {ticker1} | {ticker2} | Birleşik Portföy (%50 / %50) |
| :--- | :---: | :---: | :---: |
| **Yıllıklandırılmış Volatilite** | %{vol1*100:.2f} | %{vol2*100:.2f} | **%{port_vol*100:.2f}** |
| **Tarihsel VaR (%95 Güven - 1 Gün)** | %{df['Return_1'].std()*1.645*100:.2f} (Tahmini) | %{df['Return_2'].std()*1.645*100:.2f} (Tahmini) | **%{var_95_hist*100:.2f}** |
| **Tarihsel VaR (%99 Güven - 1 Gün)** | %{df['Return_1'].std()*2.326*100:.2f} (Tahmini) | %{df['Return_2'].std()*2.326*100:.2f} (Tahmini) | **%{var_99_hist*100:.2f}** |
| **Maksimum Değer Kaybı (Max DD)** | %{df1['Close'].pct_change().cumsum().min()*100:.2f} (Basit) | %{df2['Close'].pct_change().cumsum().min()*100:.2f} (Basit) | **%{max_dd*100:.2f}** |
| **Sharpe Oranı (Rf = %0)** | - | - | **{port_sharpe:.4f}** |

*Not: Portföy Maksimum Değer Kaybı (Max DD), 10,000 $'lık başlangıç tutarının iki hissenin ağırlıklı fiyat seyri üzerinden hesaplanan kümülatif tepe-dip kaybını gösterir.*

---

## Portföy Monte Carlo Simülasyonu (10,000 Deneme)

Portföyün günlük getiri parametreleri kullanılarak gerçekleştirilen 21 işlem günlük Monte Carlo simülasyon sonuçları aşağıdaki gibidir:

### Olası Değer Kaybı Eşikleri (1 Aylık Ufuk)
* **%95 Güven Düzeyinde Maksimum Kayıp:** %{var_95_mc_21d*100:.2f} (Portföy kaybı en fazla **{var_95_mc_21d*S0:.2f} $** olur).
* **%99 Güven Düzeyinde Maksimum Kayıp:** %{var_99_mc_21d*100:.2f} (Portföy kaybı en fazla **{var_99_mc_21d*S0:.2f} $** olur - Ekstrem durum).

### Portföy Değer Dağılım Grafiği (Monte Carlo)
Monte Carlo simülasyonu sonucu 21 gün sonundaki olası portföy değer kayıplarının frekans histogramı:

![Portföy Monte Carlo Dağılımı](C:/Users/musta/.gemini/antigravity-cli/brain/7e4fbed8-a390-41f7-a04f-e7eaf33b3915/portfolio_{clean_t1}_{clean_t2}_mc_returns_histogram.png)

### Portföy Fiyat Patikaları Grafiği
10,000 dolarlık başlangıç değerinin 21 işlem günü boyunca çizdiği 100 örnek patika:

![Portföy Patikaları](C:/Users/musta/.gemini/antigravity-cli/brain/7e4fbed8-a390-41f7-a04f-e7eaf33b3915/portfolio_{clean_t1}_{clean_t2}_monte_carlo.png)

---
*Bu analiz tamamen Python pandas, numpy ve matplotlib kütüphaneleriyle hesaplanmış olup, yatırım tavsiyesi içermez.*
"""
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"\n[OK] Portföy risk analiz raporu '{report_file}' dosyasına başarıyla kaydedildi.")

if __name__ == "__main__":
    main()
