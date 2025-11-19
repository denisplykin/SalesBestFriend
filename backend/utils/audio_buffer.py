"""
Audio buffer for real-time transcription
Accumulates audio chunks and triggers transcription periodically
"""

import io
import time
import tempfile
import os
from typing import Optional, Callable
import asyncio


class AudioBuffer:
    """Manages audio chunks for periodic transcription"""
    
    def __init__(self, interval_seconds: float = 10.0):
        """
        Initialize audio buffer
        
        Args:
            interval_seconds: How often to trigger transcription (seconds)
        """
        self.interval_seconds = interval_seconds
        self.buffer = io.BytesIO()
        self.last_transcription_time = time.time()
        self.chunk_count = 0
        self.min_chunks = 8  # Minimum chunks before transcription (снижено для быстрее транскрипции)
        
    def add_chunk(self, chunk: bytes) -> bool:
        """
        Add audio chunk to buffer
        
        Args:
            chunk: Audio data bytes
            
        Returns:
            True if ready for transcription, False otherwise
        """
        self.buffer.write(chunk)
        self.chunk_count += 1
        
        # Check if enough time has passed
        elapsed = time.time() - self.last_transcription_time
        
        # Transcribe if:
        # 1. Enough time passed (interval_seconds)
        # 2. AND we have enough chunks (at least min_chunks = ~4 seconds of audio)
        # 3. AND buffer has enough data (at least 80KB для WebM)
        buffer_size = self.buffer.tell()
        
        # Для WebM нужно больше данных чтобы получить валидный файл
        min_buffer_size = 60000  # 60KB minimum (снижено для 5-сек интервала)
        
        if (elapsed >= self.interval_seconds and 
            self.chunk_count >= self.min_chunks and
            buffer_size >= min_buffer_size):
            print(f"📊 Buffer ready: {self.chunk_count} chunks, {buffer_size} bytes, {elapsed:.1f}s elapsed")
            return True
        
        # Показываем прогресс
        if self.chunk_count % 5 == 0:
            progress_pct = (buffer_size / min_buffer_size) * 100
            print(f"   📦 Accumulating: {self.chunk_count} chunks, {buffer_size} bytes ({progress_pct:.0f}% of min), {elapsed:.1f}s")
        
        return False
    
    def get_audio_data(self) -> bytes:
        """Get accumulated audio data"""
        return self.buffer.getvalue()
    
    def clear(self):
        """Clear buffer and reset counters"""
        self.buffer = io.BytesIO()
        self.last_transcription_time = time.time()
        self.chunk_count = 0
        print(f"🔄 Audio buffer cleared, ready for next batch")
    
    def save_to_temp_file(self) -> str:
        """
        Save buffer to temporary WebM file
        
        Returns:
            Path to temporary file
        """
        data = self.get_audio_data()
        
        # Create temp file
        fd, temp_path = tempfile.mkstemp(suffix='.webm')
        
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        
        print(f"💾 Saved {len(data)} bytes to {temp_path}")
        return temp_path
    
    def has_data(self) -> bool:
        """Check if buffer has any data"""
        return self.chunk_count > 0

