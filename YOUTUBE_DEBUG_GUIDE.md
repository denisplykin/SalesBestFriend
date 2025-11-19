# 🎬 YouTube Debug - Quick Guide

## 📋 Overview

YouTube Debug feature allows you to test and analyze recorded sales calls without needing to do a live recording. Perfect for:
- Testing the system with known recordings
- Training and demonstration
- Debugging analysis logic
- Comparing different call approaches

---

## 🚀 How to Use

### **1. Open YouTube Debug Panel**

Click the **🎬** button in the top-right corner of the app (next to Settings ⚙️).

A panel will slide up from the bottom of the screen.

### **2. Paste YouTube URL**

1. Find a YouTube video with a recorded sales call
2. Copy the URL (e.g., `https://youtube.com/watch?v=ABC123`)
3. Paste it into the input field
4. Click **"🔍 Analyze Video"**

### **3. Wait for Processing**

The system will:
1. **Download** the video audio (10-30 seconds)
2. **Transcribe** with Whisper (1-2 minutes for 30-min video)
3. **Analyze** with LLM (30-60 seconds)
4. **Update** the UI with results

**Status messages:**
- ⏳ Processing... (downloading/transcribing)
- ✅ Analysis complete! (success)
- ❌ Error: ... (failure)

### **4. Review Results**

After processing, you'll see:
- **Stage Checklist** auto-filled with completed items
- **Client Card** populated with extracted information
- **Current Stage** determined from timing
- **Success message** with statistics

---

## 📺 Finding Good Test Videos

### **Recommended Video Types**

✅ **Good for testing:**
- Trial class recordings (target use case)
- Product demo calls
- Consultations/discovery calls
- Any structured sales conversation

❌ **Not ideal:**
- Webinars or presentations
- Group meetings with multiple speakers
- Low audio quality recordings
- Videos without clear dialogue

### **Example YouTube Searches**

Try searching for:
- "sales call recording"
- "trial lesson recording"
- "product demo call"
- "sales discovery call"
- "consultative selling example"

---

## ⚙️ Configuration

### **Language Selection**

The system uses your currently selected language (shown in the panel).

To change language:
1. Click **⚙️ Settings**
2. Select language: Indonesian (id), English (en), or Russian (ru)
3. Close settings
4. Open YouTube Debug panel - new language will be used

### **Call Structure**

The analysis uses your current call structure configuration:
- Default: 7 stages for trial class calls
- Customizable in `backend/call_structure_config.py`

---

## 🔍 What Gets Analyzed

### **1. Checklist Items**

For each item in each stage:
- ✅ Checks if the action was completed
- 📋 Extracts evidence (relevant quotes)
- 🎯 Marks completion with confidence score

### **2. Client Card**

Extracts structured information:
- 👶 Child information (name, interests, experience)
- 👨‍👩‍👧 Parent goals and motivation
- 🎯 Needs and desired outcomes
- ⚠️ Objections and concerns
- 📝 Additional notes

### **3. Stage Detection**

Determines:
- Current stage based on timing
- Whether call is on-time or late per stage
- Overall progress through call structure

---

## 💡 Tips for Best Results

### **1. Video Quality**

- **Clear audio** is essential
- Prefer videos with **single speaker per side** (sales + client)
- Avoid videos with heavy background noise

### **2. Video Length**

- **Optimal:** 15-45 minutes
- Longer videos take more time to process
- Very short videos (<5 min) may not provide enough data

### **3. Language Match**

- Set language to match the video language
- Mixed-language videos may produce incomplete results
- Indonesian is the primary target language

### **4. Interpretation**

- AI analysis is **not perfect**
- Use as a **guide**, not absolute truth
- Manual verification is recommended
- Compare with your own assessment

---

## ⚡ Processing Time

Approximate times (depends on video length):

| Video Duration | Download | Transcription | Analysis | Total |
|----------------|----------|---------------|----------|-------|
| 5 minutes      | 10s      | 20s           | 15s      | ~45s  |
| 15 minutes     | 15s      | 1min          | 30s      | ~2min |
| 30 minutes     | 20s      | 2min          | 45s      | ~3min |
| 60 minutes     | 30s      | 4min          | 60s      | ~6min |

**Note:** Times vary based on:
- Internet speed (download)
- CPU speed (transcription)
- LLM API response time (analysis)

---

## 🐛 Troubleshooting

### **"Failed to transcribe video"**

**Possible causes:**
- Video is private or region-blocked
- No audio track in video
- Video download failed

**Solutions:**
- Check video is publicly accessible
- Try a different video
- Ensure video has audio

### **"Error: Invalid URL"**

**Possible causes:**
- URL format incorrect
- Not a YouTube URL
- URL contains special characters

**Solutions:**
- Copy URL directly from YouTube
- Format: `https://youtube.com/watch?v=...`
- Remove tracking parameters

### **Analysis takes too long**

**Possible causes:**
- Very long video
- Slow internet connection
- LLM API slow response

**Solutions:**
- Try shorter video first
- Check internet connection
- Check backend logs for errors

### **Incomplete results**

**Possible causes:**
- Audio quality issues
- Wrong language selected
- Conversation not matching expected structure

**Solutions:**
- Verify language setting
- Check video audio quality
- Try different video

---

## 🔧 Technical Details

### **Backend Endpoint**

```
POST /api/process-youtube
```

**Parameters:**
- `url`: YouTube video URL
- `language`: Language code (id/en/ru)

**Response:**
```json
{
  "success": true,
  "transcriptLength": 5000,
  "currentStage": "stage_2_discovery",
  "itemsCompleted": 8,
  "totalItems": 32,
  "clientCardFields": 5,
  "message": "Analysis complete"
}
```

### **Technology Stack**

- **yt-dlp**: YouTube video download
- **FFmpeg**: Audio extraction
- **Whisper**: Speech-to-text transcription
- **OpenRouter (Claude)**: LLM analysis
- **WebSocket**: Real-time UI updates

---

## 📊 Cost Estimate

### **Per Video Analysis**

With **Claude 3 Haiku**:
- Transcription: Free (local Whisper)
- Checklist checking: ~$0.01-0.02 per item
- Client card extraction: ~$0.01
- **Total: ~$0.30-0.60 per video** (30 min, 32 items)

With **Llama 3.3 70B (Free)**:
- Transcription: Free
- Analysis: Free
- **Total: $0.00 per video** 🎉

---

## 🎓 Use Cases

### **1. Training**

- Analyze exemplary sales calls
- Show team members what "good" looks like
- Compare different approaches

### **2. Testing**

- Test new checklist configurations
- Validate client card field definitions
- Debug analysis logic

### **3. Benchmarking**

- Analyze competitor calls (if public)
- Study successful call patterns
- Learn from different industries

### **4. Demonstration**

- Show the system to stakeholders
- No need for live recording setup
- Predictable, repeatable results

---

## 📝 Best Practices

### **Do:**

✅ Use for testing and training
✅ Compare AI analysis with human assessment
✅ Try multiple videos to understand patterns
✅ Use as a learning tool

### **Don't:**

❌ Rely 100% on AI without verification
❌ Use copyrighted material inappropriately
❌ Process sensitive/private recordings
❌ Expect perfect accuracy on all videos

---

## 🔮 Future Enhancements

Planned improvements:
- [ ] Support for uploaded video files
- [ ] Batch processing of multiple videos
- [ ] Save and compare analyses
- [ ] Export results to CSV/PDF
- [ ] Video timestamp linking (jump to evidence)

---

## 🆘 Need Help?

If you encounter issues:

1. Check backend logs (terminal where backend is running)
2. Check browser console (F12)
3. Verify video is publicly accessible
4. Try with a different video
5. Check `TROUBLESHOOTING.md`

---

**Happy Testing! 🎬**

*Last updated: 2025-11-19*

