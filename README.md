# YouTube Transkripsiyon ve Konuşmacı Tanıma Uygulaması

Bu proje, YouTube videolarının transkripsiyon (yazıya dökme) işlemini yapan ve konuşmacıları tanımlayan bir web uygulamasıdır. Uygulama, kullanıcıdan alınan YouTube URL'sini kullanarak videonun metne dönüştürülmüş halini oluşturur, konuşmacıları tanımlar ve bunları video ile senkronize şekilde gösterir.

## Özellikler

- YouTube URL'lerinden video verilerini çekme
- Otomatik konuşma tanıma ile transkripsiyon oluşturma (Whisper AI)
- Konuşmacı diarizasyonu (farklı konuşmacıların tanımlanması)
- Transkripsiyon metninin video ile senkronize gösterimi
- Kullanıcı dostu arayüz

## Teknolojiler

### Backend
- Python 3.8+
- Flask (web sunucusu)
- Whisper AI (konuşma tanıma)
- Pyannote.audio (konuşmacı diarizasyonu)
- yt-dlp (YouTube video indirme)

### Frontend
- HTML/CSS/JavaScript
- Bootstrap 5

## Kurulum

### Gereksinimler
- Python 3.8 veya daha üstü
- CUDA destekli GPU (opsiyonel, daha hızlı transkripsiyon için)
- Hugging Face hesabı ve API anahtarı (diarizasyon için)

### Adımlar

1. Bu repo'yu klonlayın:
```bash
git clone https://github.com/ilkergalipatak/mcp_deneme.git
cd mcp_deneme
```

2. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

3. Hugging Face API anahtarınızı ayarlayın:
```bash
export HF_TOKEN="sizin_hugging_face_anahtariniz"
```

4. Uygulamayı başlatın:
```bash
python run.py
```

5. Tarayıcınızda `http://localhost:8000` adresine gidin.

## Kullanım

1. Ana sayfada YouTube video URL'sini girin
2. "Transkripsiyon Oluştur" butonuna tıklayın
3. İşlem tamamlandığında, transkripsiyon metin ve konuşmacı bilgileriyle birlikte gösterilecektir
4. Alternatif olarak, yerel video dosyalarını da yükleyebilirsiniz

## Klasör Yapısı

- `backend/` - Flask API ve transkripsiyon kodu içerir
  - `app.py` - Ana Flask uygulaması
- `frontend/` - Web arayüzü dosyaları
  - `index.html` - Kullanıcı arayüzü
  - `styles.css` - Stil dosyası
  - `main.js` - Frontend JavaScript kodu
  - `server.py` - Frontend sunucusu
- `run.py` - Uygulamayı başlatan script
- `requirements.txt` - Gerekli Python kütüphaneleri

## Notlar

- Bu uygulama eğitim amaçlıdır ve yüksek trafik için optimize edilmemiştir
- Whisper ve Pyannote.audio modellerini kullanırken Hugging Face ve OpenAI kullanım koşullarını göz önünde bulundurun

## Lisans

Bu proje MIT lisansı altında dağıtılmaktadır.