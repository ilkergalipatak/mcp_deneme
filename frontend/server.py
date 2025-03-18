import os
import socket
import threading
import http.server
import socketserver
import webbrowser
from urllib.parse import urlparse

# Statik dosyaları sunacak basit HTTP sunucusu
class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        # URL'yi ayrıştır
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        # Kök dizin veya / ile biten istekler için index.html'e yönlendir
        if path == '/' or path == '':
            self.path = '/index.html'
        
        # Normal GET işlemini devam ettir
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def log_message(self, format, *args):
        # İstek günlüklerini gösterme
        pass

def find_free_port():
    """Kullanılabilir bir port bul"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run_http_server(port):
    """Belirtilen portta HTTP sunucusunu çalıştır"""
    handler = CustomHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"Frontend HTTP sunucusu {port} portunda çalışıyor")
            httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:  # Port zaten kullanımda
            print(f"Port {port} zaten kullanımda, başka bir port deneniyor...")
            new_port = find_free_port()
            print(f"Yeni port: {new_port}")
            run_http_server(new_port)
        else:
            raise

if __name__ == "__main__":
    # Varsayılan olarak 8000 portunu kullan
    server_port = 8000
    
    # Mevcut dizini print et
    print(f"Çalışma dizini: {os.getcwd()}")
    
    # HTTP sunucusunu başlat
    run_http_server(server_port)