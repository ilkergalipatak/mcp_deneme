// API URL'sini ayarla
const API_BASE_URL = 'http://localhost:5000/api';

// DOM elementlerini seçme
const youtubeForm = document.getElementById('youtube-form');
const localVideoForm = document.getElementById('local-video-form');
const loadingIndicator = document.getElementById('loading');
const resultContainer = document.getElementById('result');
const segmentsContainer = document.getElementById('segments-container');
const fullTranscriptContainer = document.getElementById('full-transcript');
const showFullTranscriptBtn = document.getElementById('show-full-transcript');
const autoScrollToggle = document.getElementById('auto-scroll-toggle');
const errorMessageContainer = document.getElementById('error-message');
const videoTitleElement = document.getElementById('video-title');
const videoContainer = document.getElementById('video-container');

// YouTube formu gönderildiğinde
youtubeForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const youtubeUrl = document.getElementById('youtube-url').value;
    const modelName = document.getElementById('model').value;
    const doDiarization = document.getElementById('youtube-diarization-checkbox').checked;
    
    if (!youtubeUrl) {
        showError('Lütfen geçerli bir YouTube URL\'si girin.');
        return;
    }
    
    // Giriş ekranını gizle ve yükleme animasyonunu göster
    loadingIndicator.style.display = 'block';
    resultContainer.style.display = 'none';
    errorMessageContainer.style.display = 'none';
    
    try {
        // API'ye istek gönder
        const response = await fetch(`${API_BASE_URL}/transcribe`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                youtube_url: youtubeUrl,
                model: modelName,
                diarization: doDiarization
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Transkripsiyon işlemi sırasında bir hata oluştu.');
        }
        
        const data = await response.json();
        
        // Sonuçları göster
        displayResults(data, youtubeUrl);
    } catch (error) {
        showError(error.message);
    } finally {
        loadingIndicator.style.display = 'none';
    }
});

// Yerel video formu gönderildiğinde
localVideoForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    const videoFile = document.getElementById('local-video-file').files[0];
    const doDiarization = document.getElementById('diarization-checkbox').checked;
    
    if (!videoFile) {
        showError('Lütfen bir video dosyası seçin.');
        return;
    }
    
    // Form verisini oluştur
    const formData = new FormData();
    formData.append('file', videoFile);
    formData.append('diarization', doDiarization);
    
    // Giriş ekranını gizle ve yükleme animasyonunu göster
    loadingIndicator.style.display = 'block';
    resultContainer.style.display = 'none';
    errorMessageContainer.style.display = 'none';
    
    try {
        // API'ye istek gönder
        const response = await fetch(`${API_BASE_URL}/process-video`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Video işleme sırasında bir hata oluştu.');
        }
        
        const data = await response.json();
        
        // Sonuçları göster
        displayLocalVideoResults(data, videoFile);
    } catch (error) {
        showError(error.message);
    } finally {
        loadingIndicator.style.display = 'none';
    }
});

// YouTube sonuçlarını gösterme
function displayResults(data, youtubeUrl) {
    // Video başlığını ayarla
    videoTitleElement.textContent = data.title || 'Video Transkripsiyon';
    
    // YouTube iframe'i oluştur
    const videoId = extractVideoId(youtubeUrl);
    
    if (videoId) {
        videoContainer.innerHTML = `
            <iframe 
                id="youtube-player"
                width="100%" 
                height="100%" 
                src="https://www.youtube.com/embed/${videoId}" 
                title="YouTube video player" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
            </iframe>
        `;
    }
    
    // Segmentleri temizle
    segmentsContainer.innerHTML = '';
    
    // Tüm transkripsiyon metnini oluştur
    fullTranscriptContainer.textContent = data.text;
    
    // Segmentleri oluştur
    createSegments(data.segments);
    
    // Sonuç alanını göster
    resultContainer.style.display = 'block';
}

// Yerel video sonuçlarını gösterme
function displayLocalVideoResults(data, videoFile) {
    // Video başlığını ayarla
    videoTitleElement.textContent = data.title || 'Video Transkripsiyon';
    
    // Videoyu ekrana yerleştir
    const videoUrl = URL.createObjectURL(videoFile);
    videoContainer.innerHTML = `
        <video id="local-video" controls width="100%" height="100%">
            <source src="${videoUrl}" type="${videoFile.type}">
            Tarayıcınız video etiketini desteklemiyor.
        </video>
    `;
    
    // Segmentleri temizle
    segmentsContainer.innerHTML = '';
    
    // Tüm transkripsiyon metnini oluştur
    fullTranscriptContainer.textContent = data.text;
    
    // Segmentleri oluştur
    createSegments(data.segments);
    
    // Sonuç alanını göster
    resultContainer.style.display = 'block';
    
    // Video elemanını seç
    const videoElement = document.getElementById('local-video');
    
    // Video oynatıldığında segmentleri takip et
    videoElement.addEventListener('timeupdate', () => {
        updateActiveSegment(videoElement.currentTime);
    });
}

// Segmentleri oluşturma
function createSegments(segments) {
    segments.forEach((segment, index) => {
        const speakerClass = segment.speaker ? `speaker-${segment.speaker.replace('SPEAKER_', '')}` : '';
        
        const segmentElement = document.createElement('div');
        segmentElement.className = `segment segment-${index}`;
        segmentElement.dataset.start = segment.start;
        segmentElement.dataset.end = segment.end;
        
        segmentElement.innerHTML = `
            <span class="segment-time">${segment.start_str}</span>
            <span class="segment-speaker ${speakerClass}">${segment.speaker || 'Konuşmacı'}</span>
            <span class="segment-text">${segment.text}</span>
        `;
        
        // Segmente tıklandığında videoyu belirli bir noktaya konumlandır
        segmentElement.addEventListener('click', () => {
            seekVideo(segment.start);
        });
        
        segmentsContainer.appendChild(segmentElement);
    });
}

// Video ID'sini çıkarma
function extractVideoId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
}

// Videoyu belirli bir zamana konumlandırma
function seekVideo(time) {
    // YouTube player'ını kontrol et
    const youtubePlayer = document.getElementById('youtube-player');
    if (youtubePlayer) {
        // YouTube iframe API'sini kullanarak videoyu konumlandır
        youtubePlayer.contentWindow.postMessage(JSON.stringify({
            event: 'command',
            func: 'seekTo',
            args: [time, true]
        }), '*');
    }
    
    // Yerel videoyu kontrol et
    const localVideo = document.getElementById('local-video');
    if (localVideo) {
        localVideo.currentTime = time;
    }
}

// Aktif segmenti güncelleme
function updateActiveSegment(currentTime) {
    // Tüm segmentler
    const segments = document.querySelectorAll('.segment');
    let activeSegment = null;
    
    // Aktif segmenti bul
    segments.forEach(segment => {
        const start = parseFloat(segment.dataset.start);
        const end = parseFloat(segment.dataset.end);
        
        if (currentTime >= start && currentTime <= end) {
            segment.classList.add('active');
            activeSegment = segment;
        } else {
            segment.classList.remove('active');
        }
    });
    
    // Otomatik kaydırma açıksa ve aktif segment varsa
    if (autoScrollToggle.checked && activeSegment) {
        // Aktif segmenti görünür alana kaydır
        activeSegment.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Tam transkripsiyon göster/gizle
showFullTranscriptBtn.addEventListener('click', () => {
    const isShowing = fullTranscriptContainer.style.display === 'block';
    
    if (isShowing) {
        fullTranscriptContainer.style.display = 'none';
        segmentsContainer.style.display = 'block';
        showFullTranscriptBtn.textContent = 'Tam Metni Göster';
    } else {
        fullTranscriptContainer.style.display = 'block';
        segmentsContainer.style.display = 'none';
        showFullTranscriptBtn.textContent = 'Segmentleri Göster';
    }
});

// Hata mesajı gösterme
function showError(message) {
    errorMessageContainer.textContent = message;
    errorMessageContainer.style.display = 'block';
    loadingIndicator.style.display = 'none';
}

// YouTube API'si ile iletişim kurma
window.addEventListener('message', (event) => {
    try {
        // YouTube iframe'den gelen mesajları dinle
        const data = JSON.parse(event.data);
        
        if (data.event === 'infoDelivery' && data.info && data.info.currentTime) {
            updateActiveSegment(data.info.currentTime);
        }
    } catch (e) {
        // JSON parse hatalarını görmezden gel
    }
});