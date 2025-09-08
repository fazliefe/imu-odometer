import serial
import openpyxl
import csv
import time
import keyboard
import os

# === Seri Port Ayarları ===
PORT = 'COM3'
BAUD_RATE = 115200

# === Kullanıcı Bilgileri ===
cinsiyet = input("Cinsiyet (E/K): ").strip().upper()
boy = input("Boy (cm): ").strip()
kilo = input("Kilo (kg): ").strip()
yuruyus_turu = input("Yürüyüş türü (normal/hizli): ").strip().lower()

if yuruyus_turu not in ["normal", "hizli"]:
    print("❌ Geçersiz yürüyüş türü. 'normal' veya 'hizli' girin.")
    exit()

try:
    adim_uzunlugu = float(input("Adım uzunluğu (metre): ").strip())
    katedilen_mesafe = float(input("Katedilen mesafe (metre): ").strip())
except ValueError:
    print("❌ Geçersiz giriş.")
    exit()

user_name = input("Kullanıcı adı: ").strip()

# === Veri Kayıt Dizini ===
base_dir = r"C:\Users\Karakamlar\Desktop\odo\veri_seti"
test_root = os.path.join(base_dir, user_name, yuruyus_turu)
os.makedirs(test_root, exist_ok=True)

# === Tur Hazırlayıcı ===
def yeni_tur_olustur(tur):
    test_dir = os.path.join(test_root, f"test{tur}")
    os.makedirs(test_dir, exist_ok=True)

    excel_path = os.path.join(test_dir, f"veri_kayit_{user_name}_{tur}.xlsx")
    csv_path = os.path.join(test_dir, f"veri_kayit_{user_name}_{tur}.csv")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Veriler"

    columns = [
        'adim_sayisi', 'istikamet_norm', 'thegx', 'thegy', 'thegz',
        'ax', 'ay', 'az', 'millis',
        'boy', 'kilo', 'cinsiyet', 'adim_uzunlugu', 'katedilen_mesafe',
        'yuruyus_turu',
    ]
    ws.append(columns)

    csv_file = open(csv_path, mode='w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(columns)

    print(f"\n🚩 Yeni tur başladı: test{tur}")
    print(f"📁 Klasör: {test_dir}")

    return wb, ws, csv_file, csv_writer, excel_path, csv_path


print("\n🎮 Tuşlar: [p] duraklat + kaydet + sıfırla, [s] yeni tur, [q] çıkış\n")

try:
    with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
        print(f"📡 {PORT} portundan veri okunuyor...\n")

        base_istikamet = None  # İstikamet sıfırlama referansı

        for tur in range(1000):  # En fazla 1000 tur
            local_step_count = 0
            last_sensor_step = None
            step_offset = None
            istikamet_norm = 0.0  # İstikameti sıfırla tur başlangıcında

            wb, ws, csv_file, csv_writer, excel_path, csv_path = yeni_tur_olustur(tur)

            while True:
                if keyboard.is_pressed('q'):
                    print("\n🛑 Çıkış yapılıyor...")
                    wb.save(excel_path)
                    csv_file.close()
                    exit()

                if keyboard.is_pressed('p'):
                    print("⏸️ Duraklatıldı. Tur kaydedildi. Adım sayısı ve istikamet sıfırlandı.")
                    wb.save(excel_path)
                    csv_file.close()

                    # Hem adım hem istikamet sıfırlanıyor
                    local_step_count = 0
                    last_sensor_step = None
                    step_offset = None
                    istikamet_norm = 0.0
                    base_istikamet = None  # İstikamet sıfırlama referansı sıfırlanıyor

                    time.sleep(0.5)
                    break

                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) != 9:
                    print(f"⚠️ Geçersiz veri: {line}")
                    continue

                try:
                    raw_step = float(parts[0])

                    if step_offset is None:
                        step_offset = raw_step

                    corrected_step = int(raw_step - step_offset)
                    if corrected_step < 0:
                        corrected_step = 0

                    if last_sensor_step is None:
                        last_sensor_step = corrected_step

                    step_diff = corrected_step - last_sensor_step
                    if step_diff < 0:
                        step_diff = 0

                    local_step_count += step_diff
                    last_sensor_step = corrected_step

                    adim_sayisi = int(round(local_step_count))

                    # İstikameti sensörden al (2. sütun index 1)
                    istikamet_raw = float(parts[1])
                    if base_istikamet is None:
                        base_istikamet = istikamet_raw
                        print(f"🆕 İstikamet sıfırlandı. Yeni referans: {base_istikamet}")

                    # Normalize et ve 1-360 arası ölçekle
                    istikamet_diff = istikamet_raw - base_istikamet
                    if istikamet_diff < 0:
                        istikamet_diff += 360

                    istikamet_norm = istikamet_diff / 360.0  # 0-1 arası normalizasyon
                    istikamet_norm_1_360 = istikamet_norm * 359 + 1  # 1 ile 360 arası

                    data_row = [
                        adim_sayisi,
                        round(istikamet_norm_1_360, 2)
                    ] + parts[2:9] + [
                        boy, kilo, cinsiyet,
                        round(adim_uzunlugu, 3),
                        round(katedilen_mesafe, 3),
                        yuruyus_turu
                    ]

                    ws.append(data_row)
                    csv_writer.writerow(data_row)
                    print("✔️", data_row)

                except ValueError:
                    print(f"⚠️ Hatalı veri: {parts}")
                    continue

            print("▶️ Yeni tur için [s] tuşuna basın...")
            while True:
                if keyboard.is_pressed('s'):
                    base_istikamet = None  # Yeni turda istikameti sıfırla
                    print("🔁 Yeni tur başlatılıyor...\n")
                    time.sleep(0.5)
                    break

except KeyboardInterrupt:
    print("\n🛑 Manuel durduruldu.")
except serial.SerialException as e:
    print(f"❌ Seri port hatası: {e}")
except Exception as e:
    print(f"❌ Hata: {e}")
