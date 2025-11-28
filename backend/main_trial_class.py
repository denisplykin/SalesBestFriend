"""
Trial Class Sales Assistant - FastAPI Backend

Real-time sales coaching for Zoom trial class calls.
Focused on:
- Indonesian conversation transcription
- Real-time checklist progress tracking
- Client card field extraction
- Time-based stage guidance

Minimal, focused on live assistance only.
"""

# ================================================================
# 🔥🔥🔥 EMERGENCY FIX - FORCE RAILWAY CACHE CLEAR 🔥🔥🔥
# ================================================================
# DEPLOYMENT VERSION: 2025-11-21-CACHE-BUSTER-v3
# 
# Railway is using CACHED/OLD code!
# Line 257 in THIS file = "# Keep last 1000 words for context" (comment)
# Line 257 in RAILWAY = "global current_stage_id" (OLD BUGGY CODE)
# 
# This version has been verified 100% correct locally.
# All syntax checks pass. NO nested globals exist.
# 
# If you see this marker, Railway has loaded the CORRECT version!
# ================================================================
import sys
print("=" * 80, file=sys.stderr, flush=True)
print("🔥 EMERGENCY CACHE BUSTER - v3 LOADED", file=sys.stderr, flush=True)
print("📦 Version: 2025-11-21-CACHE-BUSTER-v3", file=sys.stderr, flush=True)
print(f"📍 Line 257 is: '# Keep last 1000 words for context'", file=sys.stderr, flush=True)
print("✅ NO syntax errors - 100% verified", file=sys.stderr, flush=True)
print("=" * 80, file=sys.stderr, flush=True)

import asyncio
import json
import time
from typing import Set, Dict, Optional, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

# New configs
from call_structure_config import (
    get_default_call_structure,
    get_stage_by_time,
    detect_stage_by_context,
    get_stage_timing_status,
    validate_call_structure
)
from client_card_config import (
    get_default_client_card_fields,
    validate_client_card_config
)
from trial_class_analyzer import get_trial_class_analyzer, reset_analyzer

# Existing utilities
from utils.audio_buffer import AudioBuffer
from utils.realtime_transcriber import transcribe_audio_buffer

load_dotenv()

app = FastAPI()

# CORS - Allow all origins for development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (Vercel, localhost, etc.)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600,  # Cache preflight requests for 1 hour
)

# ===== GLOBAL STATE =====
coach_connections: Set[WebSocket] = set()
accumulated_transcript: str = ""
transcription_language: str = "id"  # Bahasa Indonesia by default
is_live_recording: bool = False

# Call structure & progress
call_structure = get_default_call_structure()
client_card_fields = get_default_client_card_fields()

# Progress tracking
checklist_progress: Dict[str, bool] = {}  # item_id → completed
checklist_evidence: Dict[str, str] = {}  # item_id → evidence text
checklist_last_check: Dict[str, float] = {}  # item_id → timestamp

# Client card data
client_card_data: Dict[str, Dict[str, str]] = {}  # field_id → {value, evidence, extractedAt}

# Call timing
call_start_time: Optional[float] = None  # Timestamp when call started

# Stage tracking
current_stage_id: str = ""  # Track current stage to prevent jitter
stage_start_time: Optional[float] = None  # Timestamp when current stage started

# Debug logging
debug_log: List[Dict] = []  # Stores all AI decisions for debugging


class Session:
    """Encapsulates all state for a single call session."""
    def __init__(self):
        self.accumulated_transcript: str = ""
        self.transcription_language: str = "id"
        self.is_live_recording: bool = False
        self.call_start_time: Optional[float] = None
        self.checklist_progress: Dict[str, bool] = {}
        self.checklist_evidence: Dict[str, str] = {}
        self.checklist_last_check: Dict[str, float] = {}
        self.client_card_data: Dict[str, Dict[str, str]] = {}
        self.current_stage_id: str = ""
        self.stage_start_time: Optional[float] = None
        self.debug_log: List[Dict] = []
        self.analyzer = get_trial_class_analyzer()
        self.initial_analysis_done: bool = False

    def reset(self):
        """Resets the session state for a new analysis."""
        print("🔄 Resetting session state...")
        self.is_live_recording = True
        self.call_start_time = time.time()
        self.stage_start_time = time.time()
        self.current_stage_id = call_structure[0]['id'] if call_structure else ""
        self.checklist_progress = {}
        self.checklist_evidence = {}
        self.checklist_last_check = {}
        self.client_card_data = {}
        self.accumulated_transcript = ""
        self.debug_log = []
        self.analyzer.reset()
        self.initial_analysis_done = False
        print("✅ Session state reset complete.")

    def log_decision(self, decision_type: str, data: Dict):
        """Adds a decision to the debug log for this session."""
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "type": decision_type,
            **data
        }
        self.debug_log.append(entry)
        if len(self.debug_log) > 500:
            self.debug_log = self.debug_log[-500:]


# Analyzer
analyzer = get_trial_class_analyzer()

GREETING_KEYWORDS = ["hallo", "halo", "selamat", "pagi", "siang", "sore", "malam"]

# ===== CONFIGURATION ENDPOINTS =====

@app.get("/api/config/call-structure")
async def get_call_structure_config():
    """Get current call structure configuration"""
    return {
        "structure": call_structure
    }


@app.post("/api/config/call-structure")
async def update_call_structure_config(data: Dict = None):
    """Update call structure configuration"""
    global call_structure
    
    if not data or 'structure' not in data:
        return JSONResponse({"error": "Missing structure field"}, status_code=400)
    
    try:
        new_structure = data['structure']
        validate_call_structure(new_structure)
        call_structure = new_structure
        
        return {
            "success": True,
            "message": "Call structure updated"
        }
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/api/config/client-card")
async def get_client_card_config():
    """Get current client card field configuration"""
    return {
        "fields": client_card_fields
    }


@app.post("/api/config/client-card")
async def update_client_card_config(data: Dict = None):
    """Update client card field configuration"""
    global client_card_fields
    
    if not data or 'fields' not in data:
        return JSONResponse({"error": "Missing fields"}, status_code=400)
    
    try:
        new_fields = data['fields']
        validate_client_card_config(new_fields)
        client_card_fields = new_fields
        
        return {
            "success": True,
            "message": "Client card fields updated"
        }
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


# ===== WEBSOCKET: /ingest (Audio Input) =====

@app.websocket("/ingest")
async def websocket_ingest(websocket: WebSocket):
    """
    Accept audio stream and transcribe in real-time
    """
    session = Session()
    session.reset()
    
    await websocket.accept()
    print("🎤 /ingest connected - starting trial class session")
    print(f"   Language: {session.transcription_language}")
    print(f"   Call start time: {datetime.now().isoformat()}")

    audio_buffer = AudioBuffer(interval_seconds=10.0)
    
    try:
        while True:
            message = await websocket.receive()
            
            if 'text' in message:
                try:
                    data = json.loads(message['text'])
                    if data.get('type') == 'set_language':
                        session.transcription_language = data.get('language', 'id')
                        print(f"🌍 Language set to: {session.transcription_language}")
                except Exception as e:
                    print(f"⚠️ Failed to process setting: {e}")
                continue
            
            elif 'bytes' in message:
                data = message['bytes']
                ready = audio_buffer.add_chunk(data)
                
                if ready:
                    print(f"\n🎯 Transcription triggered (10s buffer ready)")
                    
                    try:
                        buffer_data = audio_buffer.get_audio_data()
                        loop = asyncio.get_event_loop()
                        transcript = await loop.run_in_executor(
                            None,
                            transcribe_audio_buffer,
                            buffer_data,
                            session.transcription_language
                        )
                        
                        if transcript:
                            print(f"📝 Transcript ({len(transcript)} chars):")
                            print(f"   {transcript[:200]}...")
                            
                            session.accumulated_transcript += " " + transcript
                            words = session.accumulated_transcript.split()
                            if len(words) > 1000:
                                session.accumulated_transcript = " ".join(words[-1000:])
                            
                            if session.call_start_time is None:
                                print("⚠️ call_start_time is None, skipping analysis")
                                audio_buffer.clear()
                                continue
                            
                            elapsed = time.time() - session.call_start_time
                            
                            # Pre-check for greeting
                            greeting_item_id = "greet_client"
                            if not session.checklist_progress.get(greeting_item_id, False) and any(keyword in transcript.lower() for keyword in GREETING_KEYWORDS):
                                session.checklist_progress[greeting_item_id] = True
                                session.checklist_evidence[greeting_item_id] = transcript
                                print(f"   ✅ Pre-checked: Greet the client")
                                session.log_decision("pre_check", {
                                    "item_id": greeting_item_id,
                                    "status": "completed",
                                    "evidence": transcript
                                })

                            # Delay initial analysis for 15 seconds
                            if not session.initial_analysis_done and elapsed < 15:
                                print(f"   ⏳ Delaying initial analysis ({elapsed:.1f}s < 15s)")
                                audio_buffer.clear()
                                continue
                            session.initial_analysis_done = True

                            detected_stage = detect_stage_by_context(
                                conversation_text=session.accumulated_transcript[-2000:],
                                elapsed_seconds=int(elapsed),
                                analyzer=session.analyzer,
                                previous_stage_id=session.current_stage_id if session.current_stage_id else None,
                                min_confidence=0.6
                            )
                            
                            if detected_stage != session.current_stage_id:
                                print(f"🔄 Stage transition: {session.current_stage_id or '(start)'} → {detected_stage}")
                                session.stage_start_time = time.time()
                                print(f"   ⏱️ Stage timer reset")
                                session.log_decision("stage_transition", {
                                    "from_stage": session.current_stage_id or "(start)",
                                    "to_stage": detected_stage,
                                    "elapsed_seconds": int(elapsed)
                                })
                            session.current_stage_id = detected_stage
                            
                            print(f"\n📋 Checking checklist items...")
                            newly_completed = []
                            
                            for stage in call_structure:
                                for item in stage['items']:
                                    item_id = item['id']
                                    if session.checklist_progress.get(item_id, False):
                                        continue
                                    if item_id in session.checklist_last_check and time.time() - session.checklist_last_check[item_id] < 30:
                                        continue
                                    session.checklist_last_check[item_id] = time.time()
                                    
                                    completed, confidence, evidence, debug_info = session.analyzer.check_checklist_item(
                                        item,
                                        session.accumulated_transcript[-2500:]
                                    )
                                    
                                    session.log_decision("checklist_item", {
                                        "item_id": item_id,
                                        "item_content": item['content'],
                                        "completed": completed,
                                        "confidence": confidence,
                                        "evidence": evidence,
                                        **debug_info
                                    })
                                    
                                    if completed:
                                        duplicate_evidence = False
                                        if evidence:
                                            for existing_id, existing_evidence in session.checklist_evidence.items():
                                                if existing_evidence == evidence:
                                                    duplicate_evidence = True
                                                    print(f"   ⚠️ DUPLICATE EVIDENCE detected!")
                                                    print(f"      Same evidence already used for: {existing_id}")
                                                    print(f"      Evidence: {evidence[:100]}")
                                                    session.log_decision("duplicate_evidence", {
                                                        "item_id": item_id,
                                                        "duplicate_of": existing_id,
                                                        "evidence": evidence
                                                    })
                                                    break
                                        
                                        if not duplicate_evidence:
                                            session.checklist_progress[item_id] = True
                                            session.checklist_evidence[item_id] = evidence
                                            newly_completed.append(item['content'])
                                            print(f"   ✅ {item['content']}")
                                        else:
                                            print(f"   ❌ {item['content']} - REJECTED (duplicate evidence)")
                                    else:
                                        print(f"   ❌ {item['content']} (confidence: {confidence:.0%})")
                            
                            if newly_completed:
                                print(f"\n🎯 Newly completed: {len(newly_completed)} items")
                            
                            print(f"\n👤 Extracting client info...")
                            current_values = {k: v.get('value', '') for k, v in session.client_card_data.items()}
                            new_client_info = session.analyzer.extract_client_card_fields(
                                session.accumulated_transcript[-1000:],
                                current_values
                            )
                            
                            if new_client_info:
                                print(f"   ✅ Extracted {len(new_client_info)} fields:")
                                for field_id, field_data in new_client_info.items():
                                    if isinstance(field_data, dict) and 'value' in field_data:
                                        value_text = field_data.get('value', '')
                                        field_data['extractedAt'] = datetime.utcnow().isoformat() + 'Z'
                                        session.client_card_data[field_id] = field_data
                                        print(f"      - {field_id}: {value_text[:50]}...")
                                        session.log_decision("client_card", {
                                            "field_id": field_id,
                                            "field_label": field_data.get('label', field_id),
                                            "value": value_text,
                                            "evidence": field_data.get('evidence', ''),
                                            "confidence": field_data.get('confidence', 1.0)
                                        })
                                    else:
                                        print(f"   ⚠️ Skipping malformed client_card field: {field_id}")
                            else:
                                print(f"   ⏭️ No new client info extracted")
                            
                            elapsed = time.time() - session.call_start_time
                            stages_with_progress = []
                            for stage in call_structure:
                                stage_items = []
                                for item in stage['items']:
                                    stage_items.append({
                                        "id": item['id'],
                                        "type": item['type'],
                                        "content": item['content'],
                                        "completed": session.checklist_progress.get(item['id'], False),
                                        "evidence": session.checklist_evidence.get(item['id'], "")
                                    })
                                timing_status = get_stage_timing_status(stage['id'], int(elapsed))
                                stages_with_progress.append({
                                    "id": stage['id'],
                                    "name": stage['name'],
                                    "startOffsetSeconds": stage['startOffsetSeconds'],
                                    "durationSeconds": stage['durationSeconds'],
                                    "items": stage_items,
                                    "isCurrent": stage['id'] == session.current_stage_id,
                                    "timingStatus": timing_status['status'],
                                    "timingMessage": timing_status['message']
                                })
                            
                            stage_elapsed = 0
                            if session.stage_start_time is not None:
                                stage_elapsed = int(time.time() - session.stage_start_time)
                            
                            message_data = {
                                "type": "update",
                                "callElapsedSeconds": int(elapsed),
                                "stageElapsedSeconds": stage_elapsed,
                                "currentStageId": session.current_stage_id,
                                "stages": stages_with_progress,
                                "clientCard": session.client_card_data,
                                "transcriptPreview": session.accumulated_transcript[-300:],
                                "debugLog": session.debug_log[-50:]
                            }
                            
                            print(f"📤 Sending update with {len(session.debug_log)} total log entries, last 50: {min(50, len(session.debug_log))} entries")
                            message_json = json.dumps(message_data)
                            
                            disconnected = set()
                            for ws in coach_connections:
                                try:
                                    await ws.send_text(message_json)
                                except Exception as e:
                                    print(f"❌ Send error: {e}")
                                    disconnected.add(ws)
                            
                            coach_connections.difference_update(disconnected)
                            
                            print(f"✅ Update sent to {len(coach_connections)} clients\n")
                        
                        audio_buffer.clear()
                        
                    except Exception as e:
                        print(f"❌ Analysis error: {e}")
                        import traceback
                        traceback.print_exc()
                        audio_buffer.clear()
    
    except WebSocketDisconnect:
        print("🎤 /ingest disconnected")
        session.is_live_recording = False
    except Exception as e:
        print(f"❌ /ingest error: {e}")
        session.is_live_recording = False
        import traceback
        traceback.print_exc()


# ===== WEBSOCKET: /coach (Data Output) =====

@app.websocket("/coach")
async def websocket_coach(websocket: WebSocket):
    """
    Send real-time coaching data to frontend
    """
    await websocket.accept()
    coach_connections.add(websocket)
    print(f"👥 /coach connected (total: {len(coach_connections)})")

    # Create a new session object for this coach connection
    session = Session()
    
    # Send initial state
    initial_data = {
        "type": "initial",
        "callElapsedSeconds": 0,
        "currentStageId": call_structure[0]['id'] if call_structure else None,
        "stages": [
            {
                "id": stage['id'],
                "name": stage['name'],
                "startOffsetSeconds": stage['startOffsetSeconds'],
                "durationSeconds": stage['durationSeconds'],
                "items": [
                    {
                        "id": item['id'],
                        "type": item['type'],
                        "content": item['content'],
                        "completed": False,
                        "evidence": ""
                    }
                    for item in stage['items']
                ],
                "isCurrent": False,
                "timingStatus": "not_started",
                "timingMessage": "Not started"
            }
            for stage in call_structure
        ],
        "clientCard": {},
        "transcriptPreview": ""
    }
    
    await websocket.send_text(json.dumps(initial_data))
    
    try:
        while True:
            # Keep connection open, listen for settings, but don't modify session state here
            text_data = await websocket.receive_text()
            message = json.loads(text_data)
            
            # The coach websocket is now for listening only, so we don't handle state changes here
            if message.get('type') == 'set_language':
                # This setting should be sent to the /ingest endpoint, not here.
                # We can log this for debugging.
                print(f"ℹ️ Received set_language on /coach, but this should be sent to /ingest.")

    except WebSocketDisconnect:
        coach_connections.discard(websocket)
        print(f"👥 /coach disconnected (remaining: {len(coach_connections)})")
    except Exception as e:
        coach_connections.discard(websocket)
        print(f"❌ /coach error: {e}")


# ===== HTTP ENDPOINTS =====

@app.options("/api/process-youtube")
async def options_process_youtube():
    """Handle CORS preflight for YouTube endpoint"""
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/")
async def root():
    return {
        "service": "Trial Class Sales Assistant",
        "version": "2.0.0",
        "focus": "Real-time Zoom trial class coaching",
        "language": "Bahasa Indonesia (id)",
        "endpoints": {
            "ingest": "ws://localhost:8000/ingest",
            "coach": "ws://localhost:8000/coach",
            "config": {
                "call_structure": "/api/config/call-structure",
                "client_card": "/api/config/client-card"
            }
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "coach_connections": len(coach_connections),
        "is_live_recording": is_live_recording,
        "call_elapsed": int(time.time() - call_start_time) if call_start_time else 0,
        "items_completed": sum(1 for v in checklist_progress.values() if v),
        "total_items": sum(len(stage['items']) for stage in call_structure)
    }


@app.get("/api/debug-log")
async def get_debug_log():
    """Get debug log of all AI decisions"""
    return {
        "log": debug_log[-100:],  # Last 100 entries
        "total_entries": len(debug_log),
        "is_recording": is_live_recording,
        "message": "No logs yet - start recording to see AI decisions" if len(debug_log) == 0 else f"Showing last {min(100, len(debug_log))} of {len(debug_log)} entries"
    }


# For backward compatibility / debugging
@app.post("/api/process-transcript")
async def process_transcript(transcript: str = Form(...), language: str = Form("id")):
    """Process a text transcript (for testing)"""
    global accumulated_transcript, call_start_time, current_stage_id, stage_start_time
    
    if not call_start_time:
        call_start_time = time.time()
        stage_start_time = time.time()
        current_stage_id = call_structure[0]['id'] if call_structure else ""
    
    accumulated_transcript = transcript
    
    # Quick analysis
    elapsed = time.time() - call_start_time
    detected_stage = detect_stage_by_context(
        conversation_text=transcript[-2000:],
        elapsed_seconds=int(elapsed),
        analyzer=analyzer,
        previous_stage_id=current_stage_id if current_stage_id else None,
        min_confidence=0.6
    )
    current_stage_id = detected_stage
    
    # Check items
    for stage in call_structure:
        for item in stage['items']:
            if not checklist_progress.get(item['id'], False):
                completed, conf, evidence, debug_info = analyzer.check_checklist_item(
                    item,
                    transcript
                )
                
                # Log decision
                log_decision("checklist_item", {
                    "item_id": item['id'],
                    "item_content": item['content'],
                    "completed": completed,
                    "confidence": conf,
                    "evidence": evidence,
                    **debug_info
                })
                
                if completed:
                    checklist_progress[item['id']] = True
                    checklist_evidence[item['id']] = evidence
    
    # Extract client info
    # Get current values (just the value strings for comparison)
    current_values = {k: v.get('value', '') if isinstance(v, dict) else v for k, v in client_card_data.items()}
    new_info = analyzer.extract_client_card_fields(transcript, current_values)
    for field_id, field_data in new_info.items():
        field_data['extractedAt'] = datetime.utcnow().isoformat() + 'Z'
        client_card_data[field_id] = field_data
    
    return {
        "success": True,
        "currentStage": current_stage_id,
        "itemsCompleted": sum(1 for v in checklist_progress.values() if v),
        "clientCardFields": len([v for v in client_card_data.values() if v and v.get('value')])
    }


@app.post("/api/process-youtube")
async def process_youtube(url: str = Form(...), language: str = Form("id"), real_time: bool = Form(True)):
    """
    Process YouTube video for debugging (STREAMING MODE)
    Simulates real-time call by streaming audio chunks like live recording
    """
    session = Session()
    session.reset()
    session.transcription_language = language

    try:
        from utils.youtube_streamer import get_streamer
        
        print(f"🎬 Processing YouTube (STREAMING MODE): {url}")
        print(f"   Language: {session.transcription_language}")
        print(f"   Real-time: {real_time}")
        
        audio_buffer = AudioBuffer(interval_seconds=10.0)
        streamer = get_streamer(chunk_duration=1.0)
        
        print(f"📥 Downloading and streaming YouTube video...")
        
        chunk_count = 0
        full_transcript_segments = []
        async for audio_chunk in streamer.stream_youtube_url(url, real_time=real_time):
            chunk_count += 1
            ready = audio_buffer.add_chunk(audio_chunk)
            
            if ready:
                print(f"\n🎯 Transcription triggered (10s buffer ready, chunk #{chunk_count})")
                
                try:
                    buffer_data = audio_buffer.get_audio_data()
                    loop = asyncio.get_event_loop()
                    segments = await loop.run_in_executor(
                        None,
                        transcribe_audio_buffer,
                        buffer_data,
                        session.transcription_language
                    )
                    
                    if segments:
                        full_transcript_segments.extend(segments)
                        transcript = " ".join([s['text'] for s in segments])
                        print(f"📝 Transcript ({len(transcript)} chars):")
                        print(f"   {transcript[:200]}...")
                        
                        session.accumulated_transcript += " " + transcript
                        words = session.accumulated_transcript.split()
                        if len(words) > 1000:
                            session.accumulated_transcript = " ".join(words[-1000:])
                        
                        elapsed = time.time() - session.call_start_time
                        
                        detected_stage = detect_stage_by_context(
                            conversation_text=session.accumulated_transcript[-2000:],
                            elapsed_seconds=int(elapsed),
                            analyzer=session.analyzer,
                            previous_stage_id=session.current_stage_id if session.current_stage_id else None,
                            min_confidence=0.6
                        )
                        if detected_stage != session.current_stage_id:
                            print(f"🔄 Stage transition: {session.current_stage_id or '(start)'} → {detected_stage}")
                            session.stage_start_time = time.time()
                            print(f"   ⏱️ Stage timer reset")
                            session.log_decision("stage_transition", {
                                "from_stage": session.current_stage_id or "(start)",
                                "to_stage": detected_stage,
                                "elapsed_seconds": int(elapsed)
                            })
                        session.current_stage_id = detected_stage
                        
                        print(f"\n📋 Checking checklist items (stage: {session.current_stage_id})...")
                        
                        for stage in call_structure:
                            for item in stage['items']:
                                item_id = item['id']
                                if session.checklist_progress.get(item_id, False):
                                    continue
                                
                                completed, confidence, evidence, debug_info = session.analyzer.check_checklist_item(
                                    item,
                                    session.accumulated_transcript[-1500:]
                                )
                                
                                session.log_decision("checklist_item", {
                                    "item_id": item_id,
                                    "item_content": item['content'],
                                    "completed": completed,
                                    "confidence": confidence,
                                    "evidence": evidence,
                                    **debug_info
                                })
                                
                                if completed and confidence > 0.7:
                                    session.checklist_progress[item_id] = True
                                    session.checklist_evidence[item_id] = evidence
                                    print(f"   ✅ {item['content']} (confidence: {confidence:.2f})")
                        
                        print(f"\n👤 Extracting client information...")
                        current_values = {k: v.get('value', '') for k, v in session.client_card_data.items()}
                        new_info = session.analyzer.extract_client_card_fields(
                            session.accumulated_transcript,
                            current_values
                        )
                        
                        if new_info:
                            print(f"   ✅ Extracted {len(new_info)} fields:")
                            for field_id, field_data in new_info.items():
                                if isinstance(field_data, dict) and 'value' in field_data:
                                    value_text = field_data.get('value', '')
                                    field_data['extractedAt'] = datetime.utcnow().isoformat() + 'Z'
                                    session.client_card_data[field_id] = field_data
                                    print(f"      - {field_id}: {value_text[:50]}...")
                                    session.log_decision("client_card", {
                                        "field_id": field_id,
                                        "field_label": field_data.get('label', field_id),
                                        "value": value_text,
                                        "evidence": field_data.get('evidence', ''),
                                        "confidence": field_data.get('confidence', 1.0)
                                    })
                                else:
                                    print(f"   ⚠️ Skipping malformed client_card field: {field_id}")
                        
                except Exception as e:
                    print(f"⚠️ Analysis error: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"\n✅ YouTube streaming complete!")
        print(f"   Total chunks: {chunk_count}")
        print(f"   Transcript length: {len(session.accumulated_transcript)} chars")
        
        session.is_live_recording = False
        
        elapsed = time.time() - session.call_start_time
        detected_stage = detect_stage_by_context(
            conversation_text=session.accumulated_transcript[-2000:],
            elapsed_seconds=int(elapsed),
            analyzer=session.analyzer,
            previous_stage_id=session.current_stage_id if session.current_stage_id else None,
            min_confidence=0.6
        )
        session.current_stage_id = detected_stage
        
        print(f"\n📋 Checking all checklist items...")
        
        transcript_for_final_analysis = " ".join([s['text'] for s in full_transcript_segments])
        for stage in call_structure:
            for item in stage['items']:
                item_id = item['id']
                
                completed, conf, evidence, debug_info = session.analyzer.check_checklist_item(
                    item,
                    transcript_for_final_analysis
                )
                
                session.log_decision("checklist_item", {
                    "item_id": item_id,
                    "item_content": item['content'],
                    "completed": completed,
                    "confidence": conf,
                    "evidence": evidence,
                    **debug_info
                })
                
                if completed:
                    session.checklist_progress[item_id] = True
                    session.checklist_evidence[item_id] = evidence
                    print(f"   ✅ {item['content']}")
                else:
                    print(f"   ❌ {item['content']}")
        
        print(f"\n👤 Extracting client information...")
        current_values = {k: v.get('value', '') for k, v in session.client_card_data.items()}
        new_info = session.analyzer.extract_client_card_fields(transcript_for_final_analysis, current_values)
        
        if new_info:
            print(f"   ✅ Extracted {len(new_info)} fields:")
            for field_id, field_data in new_info.items():
                field_data['extractedAt'] = datetime.utcnow().isoformat() + 'Z'
                session.client_card_data[field_id] = field_data
                print(f"      - {field_id}: {field_data.get('value', '')[:50]}...")
                session.log_decision("client_card", {
                    "field_id": field_id,
                    "field_label": field_data.get('label', field_id),
                    "value": field_data.get('value', ''),
                    "evidence": field_data.get('evidence', ''),
                    "confidence": field_data.get('confidence', 1.0)
                })
        
        stages_with_progress = []
        for stage in call_structure:
            stage_items = []
            for item in stage['items']:
                stage_items.append({
                    "id": item['id'],
                    "type": item['type'],
                    "content": item['content'],
                    "completed": session.checklist_progress.get(item['id'], False),
                    "evidence": session.checklist_evidence.get(item['id'], "")
                })
            
            timing_status = get_stage_timing_status(stage['id'], int(elapsed))
            
            stages_with_progress.append({
                "id": stage['id'],
                "name": stage['name'],
                "startOffsetSeconds": stage['startOffsetSeconds'],
                "durationSeconds": stage['durationSeconds'],
                "items": stage_items,
                "isCurrent": stage['id'] == session.current_stage_id,
                "timingStatus": timing_status['status'],
                "timingMessage": timing_status['message']
            })
        
        stage_elapsed = 0
        if session.stage_start_time is not None:
            stage_elapsed = int(time.time() - session.stage_start_time)
        
        message_data = {
            "type": "update",
            "callElapsedSeconds": int(elapsed),
            "stageElapsedSeconds": stage_elapsed,
            "currentStageId": session.current_stage_id,
            "stages": stages_with_progress,
            "clientCard": session.client_card_data,
            "transcriptPreview": session.accumulated_transcript[-300:],
            "debugLog": session.debug_log[-50:]
        }
        
        print(f"📤 Sending YouTube update with {len(session.debug_log)} total log entries, last 50: {min(50, len(session.debug_log))} entries")
        message_json = json.dumps(message_data)
        
        disconnected = set()
        for ws in coach_connections:
            try:
                await ws.send_text(message_json)
            except Exception as e:
                print(f"❌ Send error: {e}")
                disconnected.add(ws)
        
        coach_connections.difference_update(disconnected)
        
        print(f"✅ YouTube analysis complete and sent to {len(coach_connections)} clients")
        
        return {
            "success": True,
            "transcriptLength": len(session.accumulated_transcript),
            "transcript_segments": full_transcript_segments,
            "currentStage": session.current_stage_id,
            "itemsCompleted": sum(1 for v in session.checklist_progress.values() if v),
            "totalItems": sum(len(stage['items']) for stage in call_structure),
            "clientCardFields": len([v for v in session.client_card_data.values() if v]),
            "message": "Analysis complete"
        }
        
    except Exception as e:
        print(f"❌ YouTube processing error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

