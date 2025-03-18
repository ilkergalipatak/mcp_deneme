from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import speech_recognition as sr
from pyannote.audio import Pipeline
import torch
import json
import time
import yt_dlp  # pytube yerine yt-dlp kullanıyoruz
import logging
import whisper  # Whisper modelini ekleyin
import numpy as np
from pydub import AudioSegment
from datetime import timedelta
import shutil
from werkzeug.utils import secure_filename

# Günlük kaydı ayarla
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# CORS ayarlarını güncelleyelim - tüm kaynaklardan isteklere izin ver
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Hugging Face için token
HF_TOKEN = os.getenv("HF_TOKEN")
device = "cuda" if torch.cuda.is_available() else "cpu"
# Konuşmacı diarization için model
pipeline = None

def initialize_pipeline():
    global pipeline
    if pipeline is None:
        try:
            # Hugging Face'den pyannote/speaker-diarization modelini yükle
            logger.info("Diarization modelini yüklüyorum...")
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization",
                use_auth_token=HF_TOKEN
            )
            pipeline.to(device=torch.device(device))
            logger.info("Diarization modeli başarıyla yüklendi")
            return True
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            return False
    return True

def download_youtube_audio(youtube_url):
    """YouTube videosunu indir ve ses dosyasını çıkar (yt-dlp ile)"""
    try:
        logger.info(f"İndirmeye başlıyorum: {youtube_url}")
        
        # Geçici bir dizin oluştur
        temp_dir = tempfile.mkdtemp()
        output_file = os.path.join(temp_dir, "audio")
        
        logger.debug(f"Geçici dizin: {temp_dir}")
        logger.debug(f"Çıktı dosyası: {output_file}")
        
        # yt-dlp seçenekleri
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_file,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': False,  # Hata ayıklama için yt-dlp çıktısını göster
        }
        
        # Video bilgilerini al ve indir
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("yt-dlp ile video bilgilerini alıyorum")
            info = ydl.extract_info(youtube_url, download=True)
            
        # yt-dlp otomatik olarak dosya uzantısını ekler
        audio_file = f"{output_file}.wav"
        
        if not os.path.exists(audio_file):
            logger.error(f"Ses dosyası oluşturulamadı: {audio_file}")
            return None, None
            
        logger.info(f"Ses dosyası oluşturuldu: {audio_file}")
        
        # Video başlığını ve ses dosyasını döndür
        return audio_file, info.get('title', 'İsimsiz Video')
        
    except Exception as e:
        logger.error(f"YouTube video indirme hatası: {e}")
        return None, None

def transcribe_audio(audio_file_path, model_name="whisper-1"):
    """Ses dosyasını Whisper modeliyle transkript et"""
    try:
        logger.info(f"Transkripsiyon başlatılıyor. Model: {model_name}")
        
        # Model adına göre Whisper modelini seç
        if model_name == "whisper-1" or model_name == "whisper-small":
            model = whisper.load_model("small")
        elif model_name == "whisper-medium":
            model = whisper.load_model("medium")
        elif model_name == "whisper-large-v3":
            model = whisper.load_model("large-v3")
        else:
            model = whisper.load_model("small")  # Varsayılan olarak small modeli kullan
            
        logger.info(f"Model yüklendi: {model_name}")
        
        # Transkripsiyon işlemi
        result = model.transcribe(audio_file_path, verbose=False)
        logger.info("Transkripsiyon tamamlandı")
        
        return result
    except Exception as e:
        logger.error(f"Transkripsiyon hatası: {e}")
        return None

def perform_speaker_diarization(audio_file):
    """Ses dosyasında konuşmacı diarizasyonu gerçekleştir"""
    try:
        logger.info("Konuşmacı diarizasyonu başlatılıyor")
        
        # Pipeline'ı başlat
        if not initialize_pipeline():
            logger.error("Diarization modeli başlatılamadı")
            return None
            
        # Diarizasyon işlemini gerçekleştir
        diarization = pipeline(audio_file)
        
        # Sonuçları işle ve döndür
        result = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segment = {
                "start": round(turn.start, 2),
                "end": round(turn.end, 2),
                "speaker": speaker
            }
            result.append(segment)
            
        logger.info(f"Diarizasyon tamamlandı. {len(result)} segment bulundu.")
        return result
    except Exception as e:
        logger.error(f"Diarizasyon hatası: {e}")
        return None

def extract_audio_from_video(video_path, output_path="temp"):
    """Video dosyasından ses çıkar"""
    try:
        logger.info(f"Video dosyasından ses çıkarılıyor: {video_path}")
        
        # Çıktı dizinini oluştur
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        # Rastgele bir dosya adı oluştur
        temp_dir = tempfile.mkdtemp(dir=output_path)
        output_file = os.path.join(temp_dir, "audio.wav")
        
        # ffmpeg'i kullanarak ses çıkarma
        import subprocess
        command = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1",
            output_file
        ]
        
        subprocess.run(command, check=True, capture_output=True)
        
        if not os.path.exists(output_file):
            logger.error("Ses dosyası oluşturulamadı")
            return None
            
        logger.info(f"Ses dosyası çıkarıldı: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Ses çıkarma hatası: {e}")
        return None

def format_time(seconds):
    """Saniyeleri gg:ss formatına çevirir"""
    return str(timedelta(seconds=seconds)).split('.')[0].replace('0:', '')

def merge_transcription_with_speakers(transcription, diarization):
    """Transkripsiyon ve diarizasyon sonuçlarını birleştir"""
    if not diarization or not transcription:
        return transcription["segments"] if transcription else []
        
    try:
        logger.info("Transkripsiyon ve diarizasyon birleştiriliyor")
        merged_segments = []
        
        # Whisper segmentlerini döngüye al
        for segment in transcription["segments"]:
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"]
            
            # Bu segment için en uzun çakışma süresine sahip konuşmacıyı bul
            max_overlap = 0
            assigned_speaker = "Konuşmacı"
            
            for speaker_segment in diarization:
                s_start = speaker_segment["start"]
                s_end = speaker_segment["end"]
                speaker = speaker_segment["speaker"]
                
                # Çakışma var mı?
                if (s_start <= end_time and s_end >= start_time):
                    # Çakışma süresini hesapla
                    overlap_start = max(start_time, s_start)
                    overlap_end = min(end_time, s_end)
                    overlap = overlap_end - overlap_start
                    
                    # En uzun çakışma süresine sahip konuşmacıyı seç
                    if overlap > max_overlap:
                        max_overlap = overlap
                        assigned_speaker = speaker
            
            # Birleştirilmiş segment
            merged_segment = {
                "start": start_time,
                "end": end_time,
                "text": text,
                "speaker": assigned_speaker,
                "start_str": format_time(start_time),
                "end_str": format_time(end_time)
            }
            
            merged_segments.append(merged_segment)
            
        logger.info(f"Birleştirme tamamlandı. {len(merged_segments)} segment.")
        return merged_segments
    except Exception as e:
        logger.error(f"Birleştirme hatası: {e}")
        # Hata durumunda sadece transkripsiyon segmentlerini döndür
        return transcription["segments"] if transcription else []

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """YouTube URL'sinden transkripsiyon oluştur"""
    try:
        data = request.get_json()
        
        if not data or 'youtube_url' not in data:
            return jsonify({
                "error": "Geçersiz istek. YouTube URL'si gerekli."
            }), 400
            
        youtube_url = data['youtube_url']
        do_diarization = data.get('diarization', True)
        model_name = data.get('model', 'whisper-1')
        
        logger.info(f"YouTube URL alındı: {youtube_url}")
        logger.info(f"Diarizasyon: {do_diarization}")
        logger.info(f"Model: {model_name}")
        
        # YouTube videosunu indir
        audio_file, video_title = download_youtube_audio(youtube_url)
        
        if not audio_file:
            return jsonify({
                "error": "Video indirilemedi. URL'yi kontrol edin."
            }), 400
            
        # Whisper ile transkripsiyon yap
        transcription = transcribe_audio(audio_file, model_name)
        
        if not transcription:
            return jsonify({
                "error": "Transkripsiyon oluşturulamadı."
            }), 500
            
        # Diarizasyon isteniyorsa gerçekleştir
        diarization_result = None
        if do_diarization:
            diarization_result = perform_speaker_diarization(audio_file)
        
        # Transkripsiyon ve diarizasyon sonuçlarını birleştir
        final_result = merge_transcription_with_speakers(
            transcription, diarization_result
        )
        
        # İndirilen geçici dosyaları temizle
        if os.path.exists(audio_file):
            os.remove(audio_file)
            # Geçici dizini de temizle
            temp_dir = os.path.dirname(audio_file)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
        # Sonuçları döndür
        return jsonify({
            "title": video_title,
            "youtube_url": youtube_url,
            "language": transcription.get("language", "tr"),
            "segments": final_result,
            "text": transcription.get("text", ""),
            "speakers": list(set([s["speaker"] for s in final_result])) if do_diarization else []
        })
    except Exception as e:
        logger.error(f"İşlem hatası: {e}")
        return jsonify({
            "error": f"İşlem sırasında hata oluştu: {str(e)}"
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """API sağlık kontrolü"""
    # GPU kullanılabilirliğini kontrol et
    gpu_available = torch.cuda.is_available()
    gpu_count = torch.cuda.device_count() if gpu_available else 0
    gpu_name = torch.cuda.get_device_name(0) if gpu_available and gpu_count > 0 else "Yok"
    
    return jsonify({
        "status": "up",
        "gpu_available": gpu_available,
        "gpu_count": gpu_count,
        "gpu_name": gpu_name,
        "device": device
    })

@app.route('/api/process-video', methods=['POST'])
def process_video():
    """Yerel video dosyasını işle"""
    try:
        # Diarizasyon ve model seçimi
        do_diarization = request.form.get('diarization', 'true').lower() == 'true'
        model_name = request.form.get('model', 'whisper-1')
        
        logger.info(f"Diarizasyon: {do_diarization}")
        logger.info(f"Model: {model_name}")
        
        # Dosyayı al
        if 'file' not in request.files:
            return jsonify({"error": "Dosya bulunamadı"}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "Dosya seçilmedi"}), 400
            
        # Geçici dizin oluştur
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, secure_filename(file.filename))
        
        # Dosyayı kaydet
        file.save(video_path)
        logger.info(f"Video dosyası kaydedildi: {video_path}")
        
        # Ses çıkar
        audio_file = extract_audio_from_video(video_path)
        
        if not audio_file:
            return jsonify({"error": "Ses dosyası çıkarılamadı"}), 500
            
        # Transkripsiyon yap
        transcription = transcribe_audio(audio_file, model_name)
        
        if not transcription:
            return jsonify({"error": "Transkripsiyon oluşturulamadı"}), 500
            
        # Diarizasyon yap
        diarization_result = None
        if do_diarization:
            diarization_result = perform_speaker_diarization(audio_file)
            
        # Sonuçları birleştir
        final_result = merge_transcription_with_speakers(
            transcription, diarization_result
        )
        
        # Geçici dosyaları temizle
        if os.path.exists(audio_file):
            os.remove(audio_file)
            shutil.rmtree(os.path.dirname(audio_file))
            
        if os.path.exists(video_path):
            os.remove(video_path)
            shutil.rmtree(temp_dir)
            
        # Sonuçları döndür
        return jsonify({
            "title": os.path.splitext(os.path.basename(file.filename))[0],
            "language": transcription.get("language", "tr"),
            "segments": final_result,
            "text": transcription.get("text", ""),
            "speakers": list(set([s["speaker"] for s in final_result])) if do_diarization else []
        })
    except Exception as e:
        logger.error(f"Video işleme hatası: {e}")
        return jsonify({
            "error": f"İşlem sırasında hata oluştu: {str(e)}"
        }), 500

if __name__ == "__main__":
    # API'yi başlat
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)