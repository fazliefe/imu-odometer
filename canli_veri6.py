import serial
import numpy as np
import pickle
import pandas as pd
from tensorflow.keras.models import load_model
import time
import matplotlib.pyplot as plt

# === Model ve Scaler Yolları ===
MODEL_PATH = r"C:\Users\Karakamlar\Desktop\odo\veri_seti\model.h5"
SCALER_PATH = r"C:\Users\Karakamlar\Desktop\odo\veri_seti\scaler.pkl"
OUTPUT_CSV_PATH = r"C:\Users\Karakamlar\Desktop\odo\veri_seti\tahmin_konum_kaydi.csv"

# === Seri Port Ayarları ===
PORT = 'COM3'
BAUD_RATE = 115200

# === Model ve scaler yükleniyor ===
print("📦 Model yükleniyor...")
model = load_model(MODEL_PATH, compile=False)

print("📦 Scaler yükleniyor...")
with open(SCALER_PATH, 'rb') as f:
    scaler = pickle.load(f)

# === Kullanıcı bilgileri ===
print("\n🧍 Kullanıcı bilgilerini giriniz:")
boy = float(input("Boy (cm): "))
kilo = float(input("Kilo (kg): "))
cinsiyet_input = input("Cinsiyet (E/K): ").strip().upper()
cinsiyet = 0 if cinsiyet_input == 'E' else 1

# === Diğer ayarlar ===
window_size = 50
buffer = []
step_counter = 0
step_offset = None
last_sensor_step = None

# === Pozisyon takibi ===
current_x, current_y = 0.0, 0.0
positions_x = [current_x]
positions_y = [current_y]

csv_records = []

# === Grafik ayarları ===
plt.ion()
fig, ax_plot = plt.subplots(figsize=(6, 6))
line_plot, = ax_plot.plot(positions_x, positions_y, 'b-', linewidth=2)
ax_plot.set_title("🚶 Yürüyüş Rotası")
ax_plot.set_xlabel("X (m)")
ax_plot.set_ylabel("Y (m)")
ax_plot.grid(True)
ax_plot.set_aspect('equal', adjustable='datalim')

# === Pencere işleme fonksiyonu ===
def process_window(window):
    try:
        window_scaled = scaler.transform(window)
        window_scaled = np.expand_dims(window_scaled, axis=0)
        prediction = model.predict(window_scaled, verbose=0)
        return prediction.flatten()[0]
    except Exception as e:
        print("❌ Tahmin hatası:", e)
        return None

# === Yaw entegrasyonu için başlangıç ===
yaw = 0.0
dt = 0.02  # Sensör örnekleme süresi (saniye), sensörüne göre ayarla

# === Ana Döngü ===
try:
    print(f"\n📡 {PORT} portu açılıyor...")
    with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
        print(f"✅ {PORT} portu başarıyla açıldı. Veri bekleniyor...\n")

        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            parts = line.split('|')
            if len(parts) < 8:
                continue

            try:
                raw_step = float(parts[0])
                gx = float(parts[1])
                gy = float(parts[2])
                gz = float(parts[3])  # Jiroskop Z ekseni (derece/saniye)
                ax = float(parts[4])
                ay = float(parts[5])
                az = float(parts[6])
                imu_yaw_sensor = float(parts[7]) % 360  # Kullanılmıyor

                # Yaw entegrasyonu (gz derece/saniye ise)
                yaw += gz * dt
                yaw %= 360

                # İlk adım referansı
                if step_offset is None:
                    step_offset = raw_step
                    print(f"🔁 İlk adım referansı: {step_offset}")

                corrected_step = int(raw_step - step_offset)
                corrected_step = max(corrected_step, 0)

                heading = yaw
                heading_rad = np.radians(heading)
                sin_heading = np.sin(heading_rad)
                cos_heading = np.cos(heading_rad)

                features = [gx, gy, gz, ax, ay, az, boy, kilo, cinsiyet, sin_heading, cos_heading]
                buffer.append(features)
                if len(buffer) > window_size:
                    buffer.pop(0)

                if last_sensor_step is not None and corrected_step > last_sensor_step:
                    if len(buffer) == window_size:
                        tahmin = process_window(np.array(buffer))
                        if tahmin is not None:
                            tahmin = max(0.3, min(tahmin, 1.5))  # sınırlama
                            step_counter += 1

                            dx = np.cos(heading_rad) * tahmin
                            dy = np.sin(heading_rad) * tahmin
                            current_x += dx
                            current_y += dy
                            positions_x.append(current_x)
                            positions_y.append(current_y)

                            csv_records.append({
                                "Adım": step_counter,
                                "Adım_Uzunlugu_m": tahmin,
                                "X_m": current_x,
                                "Y_m": current_y,
                                "Heading_deg": heading
                            })

                            # Grafik güncelle
                            line_plot.set_xdata(positions_x)
                            line_plot.set_ydata(positions_y)
                            ax_plot.relim()
                            ax_plot.autoscale_view()
                            plt.draw()
                            plt.pause(0.001)

                            print(f"\n🧠 Yeni adım algılandı!")
                            print(f"📏 Tahmin: {tahmin:.2f} m")
                            print(f"🔢 Adım sayısı: {step_counter}")
                            print(f"📍 X: {current_x:.2f} m | Y: {current_y:.2f} m | Yön: {heading:.1f}°")

                            buffer = []

                last_sensor_step = corrected_step

            except ValueError:
                print("⚠️ Veri hatası:", parts)
                continue

except KeyboardInterrupt:
    print("\n🛑 Program kullanıcı tarafından kapatıldı.")
except serial.SerialException as se:
    print(f"❌ Seri port hatası: {se}")
except Exception as e:
    print(f"❌ Genel hata: {e}")
finally:
    if csv_records:
        df = pd.DataFrame(csv_records)
        df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')
        print(f"💾 Veriler kaydedildi: {OUTPUT_CSV_PATH}")
    else:
        print("⚠️ Kayıt yapılacak veri yok.")
