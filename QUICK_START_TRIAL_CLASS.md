# 🚀 Quick Start - Trial Class Sales Assistant

## ⚡ 5-Minute Setup

### **Prerequisites**

- Python 3.11+
- Node.js 16+
- FFmpeg installed
- Chrome/Edge/Brave browser
- OpenRouter API key

---

## **Step 1: Backend Setup** (2 min)

```bash
# Navigate to backend
cd backend

# Activate virtual environment (if not already activated)
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Configure API key
cp env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run the NEW trial class backend
python main_trial_class.py
```

✅ Backend should start on `http://localhost:8000`

---

## **Step 2: Frontend Setup** (2 min)

```bash
# Navigate to frontend (in new terminal)
cd frontend

# Install dependencies (if not already installed)
npm install

# Update main.tsx to use new App
# Edit frontend/src/main.tsx
```

Change this line in `main.tsx`:

```typescript
// FROM:
import App from './App.tsx'

// TO:
import App from './App_TrialClass.tsx'
```

Then start frontend:

```bash
npm run dev
```

✅ Frontend should start on `http://localhost:3000`

---

## **Step 3: Start Using** (1 min)

1. Open `http://localhost:3000` in **Chrome/Edge/Brave**
2. Click **"🎤 Start Session"**
3. Select **Zoom window**
4. ✅ Check **"Share audio"**
5. Click **"Share"**
6. Start your trial class!

---

## 🎯 What You'll See

### **Left Panel: Stage Checklist**
- 7 stages with time budgets
- Checkboxes auto-complete as you talk
- Current stage highlighted
- Timing indicators (on time / late)

### **Right Panel: Client Card**
- Auto-fills with client info
- Editable fields
- Organized by category

### **Top Bar**
- Call timer (elapsed time)
- Settings button (⚙️)
- Stop button

---

## ⚙️ Configuration

### **Change Language**

Click ⚙️ Settings → Select language:
- **Bahasa Indonesia** (id) - default
- **English** (en)
- **Русский** (ru)

### **Customize Stages**

Edit `backend/call_structure_config.py`:

```python
DEFAULT_CALL_STRUCTURE = [
    {
        "id": "stage_1_opening",
        "name": "Opening & Greeting",
        "startOffsetSeconds": 0,
        "durationSeconds": 120,  # 2 minutes
        "items": [
            {
                "id": "greet_client",
                "type": "say",
                "content": "Greet the client warmly"
            }
        ]
    }
]
```

### **Customize Client Card**

Edit `backend/client_card_config.py`:

```python
DEFAULT_CLIENT_CARD_FIELDS = [
    {
        "id": "child_name",
        "label": "Child's Name",
        "hint": "Name and age",
        "multiline": False,
        "category": "child_info"
    }
]
```

---

## 🎬 YouTube Debug (Testing)

### **For Testing Without Live Recording**

Instead of starting a live session, you can test with YouTube videos:

1. Click **🎬** button (top-right, next to Settings)
2. Paste YouTube URL with sales call recording
3. Click **"🔍 Analyze Video"**
4. Wait 2-3 minutes for processing
5. Review results in the UI

**Perfect for:**
- Testing the system
- Training demonstrations
- Debugging analysis logic
- Learning without live calls

**See:** `YOUTUBE_DEBUG_GUIDE.md` for detailed instructions

---

## 🔍 Troubleshooting

### **Backend won't start**

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check FFmpeg
ffmpeg -version

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### **Frontend shows "Connection refused"**

1. Check backend is running on port 8000
2. Check `frontend/.env` has `VITE_API_WS=ws://localhost:8000`
3. Restart frontend after `.env` changes

### **No audio captured**

1. Use **Chrome/Edge/Brave** (not Firefox/Safari)
2. Select **"Chrome Tab"** (not entire screen)
3. ✅ **Must check "Share audio"** checkbox
4. Select the **Zoom tab**

### **Checklist items not completing**

1. Speak in Indonesian (or selected language)
2. Wait 10 seconds for transcription
3. Items need clear, explicit evidence
4. Check backend logs for errors

### **Client card not filling**

1. Information must be explicitly mentioned
2. LLM needs high confidence (80%+)
3. Check backend logs for extraction attempts

---

## 📊 Cost Estimate

With **Claude 3 Haiku** (recommended):
- **~$0.01-0.03 per minute** of call
- **~$0.60-1.80 for 60-minute call**

With **Llama 3.3 70B** (FREE):
- **$0.00 per minute**
- Use by setting: `LLM_MODEL=meta-llama/llama-3.3-70b-instruct:free`

---

## 🎓 Tips for Best Results

### **1. Audio Quality**
- Use good internet connection
- Minimize background noise
- Speak clearly

### **2. Stage Timing**
- Follow the time budgets
- Green badge = on time
- Yellow badge = slightly late
- Red badge = very late

### **3. Manual Override**
- Click checkboxes manually if AI misses something
- Edit client card fields anytime
- Changes sync in real-time

### **4. Screen Sharing**
- UI is designed to be unobtrusive
- Minimal colors and distractions
- Plenty of whitespace

---

## 📝 During the Call

### **Do:**
- ✅ Follow stage progression
- ✅ Check timing indicators
- ✅ Review client card periodically
- ✅ Use manual overrides when needed

### **Don't:**
- ❌ Don't obsess over checklist
- ❌ Don't interrupt flow to click boxes
- ❌ Don't share backend logs screen
- ❌ Don't rely 100% on AI (it's a guide!)

---

## 🔄 Post-Call

1. Click **"⏹️ Stop"** to end session
2. Review client card for notes
3. Copy important info to CRM
4. Start new session for next call

**Note:** MVP doesn't save call history. Copy important info before stopping!

---

## 📚 Next Steps

- Read `REFACTOR_SUMMARY.md` for detailed architecture
- Read `PRODUCT_ARCHITECTURE.md` for system overview
- Customize stages and fields for your needs
- Train your sales team on the UI

---

## 🆘 Need Help?

1. Check `TROUBLESHOOTING.md`
2. Check `REFACTOR_SUMMARY.md`
3. Check backend logs (terminal)
4. Check browser console (F12)

---

**Ready to coach! 🎯**

*Last updated: 2025-11-19*

