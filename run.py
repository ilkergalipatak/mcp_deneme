import os
import subprocess
import threading
import sys
import time
import webbrowser

def run_backend():
    """Backend Flask uygulamasını çalıştır"""
    print("Backend başlatılıyor...")
    
    # Proje kök dizinini al
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    
    # Backend dizinine git ve app.py'nin varlığını kontrol et
    if not os.path.exists(os.path.join(backend_dir, "app.py")):
        print(f"Hata: app.py dosyası bulunamadı: {os.path.join(backend_dir, 'app.py')}")
        return
    
    # Backend dizinine git
    original_dir = os.getcwd()
    os.chdir(backend_dir)
    
    try:
        # Python yorumlayıcısının tam yolunu kullan
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("Backend kapatılıyor...")
    except Exception as e:
        print(f"Backend hata: {e}")
    finally:
        # Orijinal dizine geri dön
        os.chdir(original_dir)

def run_frontend():
    """Frontend HTTP sunucusunu çalıştır"""
    print("Frontend başlatılıyor...")
    
    # Proje kök dizinini al
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # Frontend dizinine git ve server.py'nin varlığını kontrol et
    if not os.path.exists(os.path.join(frontend_dir, "server.py")):
        print(f"Hata: server.py dosyası bulunamadı: {os.path.join(frontend_dir, 'server.py')}")
        return
        
    # Frontend dizinine git
    original_dir = os.getcwd()
    os.chdir(frontend_dir)
    
    try:
        # Python yorumlayıcısının tam yolunu kullan
        subprocess.run([sys.executable, "server.py"], check=True)
    except KeyboardInterrupt:
        print("Frontend kapatılıyor...")
    except Exception as e:
        print(f"Frontend hata: {e}")
    finally:
        # Orijinal dizine geri dön
        os.chdir(original_dir)

def main():
    """Ana fonksiyon"""
    # Hugging Face token'ını ortam değişkeni olarak ayarla
    # Gerçek API anahtarınızı buraya yazın veya çevre değişkeninden alın
    os.environ["HF_TOKEN"] = "your_huggingface_token_here"
    
    # Backend ve frontend'i ayrı thread'lerde çalıştır
    backend_thread = threading.Thread(target=run_backend)
    frontend_thread = threading.Thread(target=run_frontend)
    
    # Thread'leri başlat
    backend_thread.daemon = True
    frontend_thread.daemon = True
    
    print("YouTube Transkripsiyon ve Konuşmacı Tanıma Uygulaması başlatılıyor...")
    backend_thread.start()
    frontend_thread.start()
    
    # Biraz bekleyelim ve tarayıcıyı açalım
    time.sleep(3)
    webbrowser.open("http://localhost:8000")
    
    try:
        # Ana thread'i canlı tut
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nUygulama kapatılıyor...")

if __name__ == "__main__":
    main()