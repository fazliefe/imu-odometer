import os
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping


def load_all_csvs(folder_path, max_files_per_folder=5, dt_saniye=0.02):
    data_list, labels_list = [], []

    for root, dirs, files in os.walk(folder_path):
        csv_files = [f for f in files if f.lower().endswith('.csv')]
        if not csv_files:
            continue

        selected_files = sorted(csv_files)[:max_files_per_folder]
        for file in selected_files:
            file_path = os.path.join(root, file)
            try:
                df = pd.read_csv(file_path)

                required_columns = {
                    'thegx', 'thegy', 'thegz', 'ax', 'ay', 'az',
                    'boy', 'kilo', 'cinsiyet', 'adim_uzunlugu'
                }
                if not required_columns.issubset(df.columns):
                    print(f"⚠️ Eksik sütun(lar): {file_path}")
                    continue

                df = df[df['cinsiyet'].isin(['E', 'K'])]
                df['cinsiyet'] = df['cinsiyet'].map({'E': 0, 'K': 1})

                # === Heading hesapla ===
                df['heading_deg'] = (df['thegz'] * dt_saniye).cumsum() % 360
                df['heading_rad'] = np.radians(df['heading_deg'])
                df['sin_heading'] = np.sin(df['heading_rad'])
                df['cos_heading'] = np.cos(df['heading_rad'])

                # === Feature & Label ===
                features = [
                    'thegx', 'thegy', 'thegz',
                    'ax', 'ay', 'az',
                    'boy', 'kilo', 'cinsiyet',
                    'sin_heading', 'cos_heading'
                ]

                X = df[features].astype(float).values
                y = df['adim_uzunlugu'].astype(float).values

                data_list.append(X)
                labels_list.append(y)

                print(f"✅ Yüklendi: {file_path} | Satır sayısı: {len(y)}")

            except Exception as e:
                print(f"❌ Hata ({file_path}): {e}")

    if not data_list:
        raise RuntimeError("❌ Hiç geçerli veri bulunamadı.")

    return np.vstack(data_list), np.concatenate(labels_list)


def create_windows(data, labels, window_size):
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i+window_size])
        y.append(labels[i+window_size-1])
    return np.array(X), np.array(y)


def main(data_dir, window_size=50, epochs=20):
    print("\n📂 Veriler yükleniyor...")
    X_raw, y_raw = load_all_csvs(data_dir)
    print("📏 Ham veri şekli:", X_raw.shape, y_raw.shape)

    # Ölçekleme
    print("\n🔧 Veriler ölçekleniyor...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # Pencereleme
    print("\n🪟 Pencereler oluşturuluyor...")
    X_windows, y_windows = create_windows(X_scaled, y_raw, window_size)
    print("📐 Pencerelenmiş veri şekli:", X_windows.shape, y_windows.shape)

    # Eğitim/test bölme
    print("\n🔀 Eğitim ve test setlerine ayrılıyor...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_windows, y_windows, test_size=0.2, random_state=42
    )

    # Model oluşturma
    print("\n🧠 Model oluşturuluyor...")
    model = Sequential([
        LSTM(64, input_shape=(window_size, X_windows.shape[2])),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    model.summary()

    # Eğitim
    print("\n🚀 Model eğitiliyor...")
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=epochs,
        batch_size=32,
        callbacks=[early_stop],
        verbose=1
    )

    # Tahmin
    print("\n📊 Tahminler yapılıyor...")
    y_pred = model.predict(X_test).flatten()

    # Karşılaştırma grafiği
    plt.figure(figsize=(12, 6))
    plt.plot(y_test[:200], label='Gerçek', linestyle='--')
    plt.plot(y_pred[:200], label='Tahmin')
    plt.title("🎯 Adım Uzunluğu - Gerçek vs Tahmin (İlk 200)")
    plt.xlabel("Örnek")
    plt.ylabel("Adım Uzunluğu (m)")
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.show()

    # Hata grafiği
    plt.figure(figsize=(10, 4))
    plt.plot(np.abs(y_test - y_pred), color='red')
    plt.title("📉 Mutlak Hata Dağılımı")
    plt.xlabel("Örnek")
    plt.ylabel("Hata (m)")
    plt.grid()
    plt.tight_layout()
    plt.show()

    # Tahmin sonuçları CSV
    tahmin_csv_path = os.path.join(data_dir, "tahmin_sonuc.csv")
    pd.DataFrame({
        "Gerçek": y_test,
        "Tahmin": y_pred
    }).to_csv(tahmin_csv_path, index=False, encoding='utf-8-sig')
    print(f"💾 Tahminler kaydedildi: {tahmin_csv_path}")

    # Model ve scaler dosyaları
    model_path = os.path.join(data_dir, "model.h5")
    scaler_path = os.path.join(data_dir, "scaler.pkl")
    model.save(model_path)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"✅ Model kaydedildi: {model_path}")
    print(f"✅ Scaler kaydedildi: {scaler_path}")


if __name__ == "__main__":
    dataset_directory = r"C:\Users\Karakamlar\Desktop\odo\veri_seti"
    main(dataset_directory, window_size=50, epochs=20)
