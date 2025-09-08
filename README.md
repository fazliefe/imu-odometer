# 🚶‍♂️ PDR Odometre (IMU Sensörleri ile Adım Sayısı, Adım Uzunluğu ve İstikamet Tahmini)

Bu proje, **Pedestrian Dead Reckoning (PDR)** yaklaşımı ile **IMU sensörlerinden** (ivmeölçer, jiroskop, manyetometre) gelen veriler kullanılarak kişilerin yürüyüşünün gerçek zamanlı takibini amaçlamaktadır.  

Temel amaç:  
- 🦶 Adım sayısını doğru tespit etmek  
- 📏 Adım uzunluğunu makine öğrenmesi ile tahmin etmek  
- 🧭 İstikameti (heading) sensör füzyonu ile belirlemek  
- 🗺️ Tüm bu bilgilerle kişinin **2D yürüyüş rotasını** çıkarmak  

---

## 🎯 Projenin Amacı ve Katkısı

GPS sinyalinin zayıf veya hiç olmadığı ortamlarda (ör. bina içi, yeraltı yapıları, tüneller), konum takibi zorlaşır. Bu proje:  

- **IMU tabanlı odometri** ile adım tabanlı konum tahmini sağlar.  
- **Makine öğrenmesi** kullanarak adım uzunluğu kişiye özgü şekilde tahmin edilir.  
- **Gerçek zamanlı görselleştirme** ile kullanıcının yürüdüğü rota ekranda anlık olarak gösterilir.  
- **Veri seti oluşturma + model eğitme + canlı tahmin** aşamalarını kapsayan uçtan uca bir sistemdir.  

---

## 🛠️ Kullanılan Teknolojiler

- **Python** (veri işleme, model eğitimi ve gerçek zamanlı tahmin)  
- **TensorFlow / Keras** (derin öğrenme modeli)  
- **Scikit-learn** (veri ölçekleme)  
- **PySerial** (sensör ile seri port haberleşmesi)  
- **Matplotlib** (canlı rota görselleştirme)  
- **OpenPyXL & CSV** (ham veri kayıtları)  

---

## 📂 Proje Yapısı

- **`deneme_6h.py`**  
  Kullanıcıdan temel bilgileri alır (boy, kilo, cinsiyet, yürüyüş türü).  
  IMU sensöründen gelen verileri seri port üzerinden okur.  
  Her tur için verileri **Excel ve CSV dosyalarına** kaydeder.  
  → **Amaç: Veri seti oluşturmak.**

- **`model_4.py`**  
  Kaydedilen veri setini işler.  
  Adım uzunluğunu tahmin edebilmek için **Makine Öğrenmesi / Derin Öğrenme** modeli eğitir.  
  Sonuçta iki dosya üretir:  
  - `model.h5` → Eğitilmiş model  
  - `scaler.pkl` → Veri normalizasyonu için scaler  

- **`canli_veri6.py`**  
  Eğitilen modeli kullanarak gerçek zamanlı çalışır.  
  IMU’dan gelen verileri işler ve:  
  - Adım sayısı  
  - Adım uzunluğu (ML tahmini)  
  - İstikamet (gyro + manyetometre)  
  bilgilerini hesaplar.  
  Kullanıcının **2D yürüyüş rotasını** ekranda çizer.  
  Tahmin edilen değerler ayrıca CSV dosyasına kaydedilir.  

---

## ⚙️ Gereksinimler

- Python 3.8+  

- Kütüphaneler:
  ```bash
  pip install numpy pandas matplotlib tensorflow scikit-learn pyserial openpyxl keyboard
  <img width="940" height="813" alt="odo1" src="https://github.com/user-attachments/assets/a8b12369-902f-462d-9d91-2e9f2c811b37" />
![Uploading odo1.png…]()
<img width="885" height="992" alt="odo4" src="https://github.com/user-attachments/assets/581d8342-cdfd-4d69-8dcd-f4279d92679e" />
<img width="908" height="889" alt="odo3" src="https://github.com/user-attachments/assets/3aeffe4e-bafc-4402-b3ca-26668af1f837" />

