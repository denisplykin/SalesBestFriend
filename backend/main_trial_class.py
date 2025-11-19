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

import asyncio
import json
import time
from typing import Set, Dict, Optional
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
client_card_data: Dict[str, str] = {}  # field_id → value

# Call timing
call_start_time: Optional[float] = None  # Timestamp when call started

# Analyzer
analyzer = get_trial_class_analyzer()

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
    global transcription_language, is_live_recording, call_start_time
    global checklist_progress, checklist_evidence, checklist_last_check
    global client_card_data, accumulated_transcript
    
    # Reset state for new session
    is_live_recording = True
    call_start_time = time.time()
    checklist_progress = {}
    checklist_evidence = {}
    checklist_last_check = {}
    client_card_data = {field['id']: "" for field in client_card_fields}
    accumulated_transcript = ""
    reset_analyzer()
    
    await websocket.accept()
    print("🎤 /ingest connected - starting trial class session")
    print(f"   Language: {transcription_language}")
    print(f"   Call start time: {datetime.now().isoformat()}")
    
    # Audio buffer (transcribe every 10 seconds)
    audio_buffer = AudioBuffer(interval_seconds=10.0)
    
    try:
        while True:
            message = await websocket.receive()
            
            # Handle text messages (settings)
            if 'text' in message:
                try:
                    data = json.loads(message['text'])
                    if data.get('type') == 'set_language':
                        transcription_language = data.get('language', 'id')
                        print(f"🌍 Language set to: {transcription_language}")
                except Exception as e:
                    print(f"⚠️ Failed to process setting: {e}")
                continue
            
            # Handle audio data
            elif 'bytes' in message:
                data = message['bytes']
                ready = audio_buffer.add_chunk(data)
                
                if ready:
                    print(f"\n🎯 Transcription triggered (10s buffer ready)")
                    
                    try:
                        # Get audio
                        buffer_data = audio_buffer.get_audio_data()
                        
                        # Transcribe
                        loop = asyncio.get_event_loop()
                        transcript = await loop.run_in_executor(
                            None,
                            transcribe_audio_buffer,
                            buffer_data,
                            transcription_language
                        )
                        
                        if transcript:
                            print(f"📝 Transcript ({len(transcript)} chars):")
                            print(f"   {transcript[:200]}...")
                            
                            # Accumulate
                            accumulated_transcript += " " + transcript
                            # Keep last 1000 words for context
                            words = accumulated_transcript.split()
                            if len(words) > 1000:
                                accumulated_transcript = " ".join(words[-1000:])
                            
                            # ===== ANALYZE: Check checklist items =====
                            elapsed = time.time() - call_start_time
                            current_stage_id = get_stage_by_time(int(elapsed))
                            
                            print(f"\n📋 Checking checklist items...")
                            newly_completed = []
                            
                            for stage in call_structure:
                                for item in stage['items']:
                                    item_id = item['id']
                                    
                                    # Skip if already completed
                                    if checklist_progress.get(item_id, False):
                                        continue
                                    
                                    # Skip if checked recently (30s cooldown)
                                    if item_id in checklist_last_check:
                                        if time.time() - checklist_last_check[item_id] < 30:
                                            continue
                                    
                                    # Update last check time
                                    checklist_last_check[item_id] = time.time()
                                    
                                    # Check with LLM
                                    completed, confidence, evidence = analyzer.check_checklist_item(
                                        item_id,
                                        item['content'],
                                        item['type'],
                                        accumulated_transcript[-1500:]  # Last 1500 chars
                                    )
                                    
                                    if completed:
                                        checklist_progress[item_id] = True
                                        checklist_evidence[item_id] = evidence
                                        newly_completed.append(item['content'])
                                        print(f"   ✅ {item['content']}")
                                    else:
                                        print(f"   ❌ {item['content']} (confidence: {confidence:.0%})")
                            
                            if newly_completed:
                                print(f"\n🎯 Newly completed: {len(newly_completed)} items")
                            
                            # ===== ANALYZE: Extract client card info =====
                            print(f"\n👤 Extracting client info...")
                            new_client_info = analyzer.extract_client_card_fields(
                                accumulated_transcript[-1000:],  # Last 1000 chars
                                client_card_data
                            )
                            
                            if new_client_info:
                                print(f"   ✅ Extracted {len(new_client_info)} fields:")
                                for field_id, value in new_client_info.items():
                                    print(f"      - {field_id}: {value[:50]}...")
                                    client_card_data[field_id] = value
                            else:
                                print(f"   ⏭️ No new client info extracted")
                            
                            # ===== BUILD AND SEND RESPONSE =====
                            elapsed = time.time() - call_start_time
                            current_stage_id = get_stage_by_time(int(elapsed))
                            
                            # Build stages with progress and timing
                            stages_with_progress = []
                            for stage in call_structure:
                                stage_items = []
                                for item in stage['items']:
                                    stage_items.append({
                                        "id": item['id'],
                                        "type": item['type'],
                                        "content": item['content'],
                                        "completed": checklist_progress.get(item['id'], False),
                                        "evidence": checklist_evidence.get(item['id'], "")
                                    })
                                
                                timing_status = get_stage_timing_status(stage['id'], int(elapsed))
                                
                                stages_with_progress.append({
                                    "id": stage['id'],
                                    "name": stage['name'],
                                    "startOffsetSeconds": stage['startOffsetSeconds'],
                                    "durationSeconds": stage['durationSeconds'],
                                    "items": stage_items,
                                    "isCurrent": stage['id'] == current_stage_id,
                                    "timingStatus": timing_status['status'],
                                    "timingMessage": timing_status['message']
                                })
                            
                            # Send to all clients
                            message_data = {
                                "type": "update",
                                "callElapsedSeconds": int(elapsed),
                                "currentStageId": current_stage_id,
                                "stages": stages_with_progress,
                                "clientCard": client_card_data,
                                "transcriptPreview": accumulated_transcript[-300:]
                            }
                            
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
                        
                        # Clear buffer
                        audio_buffer.clear()
                        
                    except Exception as e:
                        print(f"❌ Analysis error: {e}")
                        import traceback
                        traceback.print_exc()
                        audio_buffer.clear()
    
    except WebSocketDisconnect:
        print("🎤 /ingest disconnected")
        is_live_recording = False
        call_start_time = None
    except Exception as e:
        print(f"❌ /ingest error: {e}")
        is_live_recording = False
        call_start_time = None
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
        "clientCard": client_card_data,
        "transcriptPreview": ""
    }
    
    await websocket.send_text(json.dumps(initial_data))
    
    try:
        while True:
            # Keep connection open, listen for settings
            text_data = await websocket.receive_text()
            message = json.loads(text_data)
            
            if message.get('type') == 'set_language':
                global transcription_language
                transcription_language = message.get('language', 'id')
                print(f"🌍 Language set to: {transcription_language}")
            
            elif message.get('type') == 'manual_toggle_item':
                # Allow manual checkbox toggle
                item_id = message.get('item_id')
                if item_id:
                    checklist_progress[item_id] = not checklist_progress.get(item_id, False)
                    print(f"✋ Manual toggle: {item_id} = {checklist_progress[item_id]}")
            
            elif message.get('type') == 'update_client_card':
                # Allow manual client card updates
                field_id = message.get('field_id')
                value = message.get('value')
                if field_id and field_id in client_card_data:
                    client_card_data[field_id] = value
                    print(f"✋ Manual update: {field_id}")
    
    except WebSocketDisconnect:
        coach_connections.discard(websocket)
        print(f"👥 /coach disconnected (remaining: {len(coach_connections)})")
    except Exception as e:
        coach_connections.discard(websocket)
        print(f"❌ /coach error: {e}")


# ===== HTTP ENDPOINTS =====

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


# For backward compatibility / debugging
@app.post("/api/process-transcript")
async def process_transcript(transcript: str = Form(...), language: str = Form("id")):
    """Process a text transcript (for testing)"""
    global accumulated_transcript, call_start_time
    
    if not call_start_time:
        call_start_time = time.time()
    
    accumulated_transcript = transcript
    
    # Quick analysis
    elapsed = time.time() - call_start_time
    current_stage_id = get_stage_by_time(int(elapsed))
    
    # Check items
    for stage in call_structure:
        for item in stage['items']:
            if not checklist_progress.get(item['id'], False):
                completed, conf, evidence = analyzer.check_checklist_item(
                    item['id'],
                    item['content'],
                    item['type'],
                    transcript
                )
                if completed:
                    checklist_progress[item['id']] = True
                    checklist_evidence[item['id']] = evidence
    
    # Extract client info
    new_info = analyzer.extract_client_card_fields(transcript, client_card_data)
    for field_id, value in new_info.items():
        client_card_data[field_id] = value
    
    return {
        "success": True,
        "currentStage": current_stage_id,
        "itemsCompleted": sum(1 for v in checklist_progress.values() if v),
        "clientCardFields": len([v for v in client_card_data.values() if v])
    }


@app.post("/api/process-youtube")
async def process_youtube(url: str = Form(...), language: str = Form("id")):
    """
    Process YouTube video for debugging
    Downloads, transcribes, and analyzes a sales call recording
    """
    global accumulated_transcript, call_start_time, transcription_language
    global checklist_progress, checklist_evidence, client_card_data
    
    try:
        from utils.youtube_processor import process_youtube_url
        
        print(f"🎬 Processing YouTube: {url} (language: {language})")
        
        # Reset state for new analysis
        if not call_start_time:
            call_start_time = time.time()
        
        checklist_progress = {}
        checklist_evidence = {}
        client_card_data = {field['id']: "" for field in client_card_fields}
        transcription_language = language
        
        # Download and transcribe
        transcript = process_youtube_url(url, language=language)
        
        if not transcript:
            return JSONResponse({
                "success": False,
                "error": "Failed to transcribe video"
            }, status_code=400)
        
        print(f"📝 Transcription complete: {len(transcript)} chars")
        
        accumulated_transcript = transcript
        
        # Analyze
        elapsed = time.time() - call_start_time
        current_stage_id = get_stage_by_time(int(elapsed))
        
        print(f"\n📋 Checking all checklist items...")
        
        # Check all items
        for stage in call_structure:
            for item in stage['items']:
                item_id = item['id']
                
                completed, conf, evidence = analyzer.check_checklist_item(
                    item_id,
                    item['content'],
                    item['type'],
                    transcript
                )
                
                if completed:
                    checklist_progress[item_id] = True
                    checklist_evidence[item_id] = evidence
                    print(f"   ✅ {item['content']}")
                else:
                    print(f"   ❌ {item['content']}")
        
        print(f"\n👤 Extracting client information...")
        
        # Extract client info
        new_info = analyzer.extract_client_card_fields(transcript, client_card_data)
        
        if new_info:
            print(f"   ✅ Extracted {len(new_info)} fields:")
            for field_id, value in new_info.items():
                client_card_data[field_id] = value
                print(f"      - {field_id}: {value[:50]}...")
        
        # Build response
        stages_with_progress = []
        for stage in call_structure:
            stage_items = []
            for item in stage['items']:
                stage_items.append({
                    "id": item['id'],
                    "type": item['type'],
                    "content": item['content'],
                    "completed": checklist_progress.get(item['id'], False),
                    "evidence": checklist_evidence.get(item['id'], "")
                })
            
            timing_status = get_stage_timing_status(stage['id'], int(elapsed))
            
            stages_with_progress.append({
                "id": stage['id'],
                "name": stage['name'],
                "startOffsetSeconds": stage['startOffsetSeconds'],
                "durationSeconds": stage['durationSeconds'],
                "items": stage_items,
                "isCurrent": stage['id'] == current_stage_id,
                "timingStatus": timing_status['status'],
                "timingMessage": timing_status['message']
            })
        
        # Broadcast to connected clients
        message_data = {
            "type": "update",
            "callElapsedSeconds": int(elapsed),
            "currentStageId": current_stage_id,
            "stages": stages_with_progress,
            "clientCard": client_card_data,
            "transcriptPreview": transcript[-300:]
        }
        
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
            "transcriptLength": len(transcript),
            "currentStage": current_stage_id,
            "itemsCompleted": sum(1 for v in checklist_progress.values() if v),
            "totalItems": sum(len(stage['items']) for stage in call_structure),
            "clientCardFields": len([v for v in client_card_data.values() if v]),
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

