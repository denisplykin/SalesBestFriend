# 🔧 Vercel Environment Variables Setup

## 🚨 Problem

Frontend is trying to connect to itself instead of Railway backend:
```
❌ https://sales-best-friend-tkoj.vercel.app/api/process-youtube
✅ https://salesbestfriend-production.up.railway.app/api/process-youtube
```

**Cause:** `vercel.json` `build.env` is not being applied!

---

## ✅ Solution: Set Environment Variables in Vercel Dashboard

### **Step 1: Open Vercel Project Settings**

1. Go to: https://vercel.com/dashboard
2. Click on your project: **SalesBestFriend** (or similar)
3. Click **Settings** tab
4. Click **Environment Variables** (left sidebar)

---

### **Step 2: Add Environment Variables**

Add the following variables:

#### **Variable 1:**
- **Key:** `VITE_API_HTTP`
- **Value:** `https://salesbestfriend-production.up.railway.app`
- **Environments:** ✅ Production, ✅ Preview, ✅ Development

#### **Variable 2:**
- **Key:** `VITE_API_WS`
- **Value:** `wss://salesbestfriend-production.up.railway.app`
- **Environments:** ✅ Production, ✅ Preview, ✅ Development

---

### **Step 3: Redeploy**

After adding variables:

1. Go to **Deployments** tab
2. Click on latest deployment
3. Click **⋯** (three dots menu)
4. Click **Redeploy**
5. Check **✅ Use existing Build Cache** is **UNCHECKED**
6. Click **Redeploy**

**OR** just push a new commit:
```bash
git commit --allow-empty -m "🔄 Trigger Vercel rebuild with env vars"
git push origin main
```

---

## 🔍 Verify Deployment

### **Check if env vars are working:**

1. Open: https://sales-best-friend-tkoj.vercel.app/
2. Open Console (F12)
3. Look for:
   ```
   🔍 Connecting to backend: https://salesbestfriend-production.up.railway.app
   ```
4. Should **NOT** show localhost or vercel.app URL!

---

## 📸 Screenshot Guide

### **Where to add variables:**

```
Vercel Dashboard
└─ Your Project
   └─ Settings
      └─ Environment Variables
         ├─ Add New
         ├─ Key: VITE_API_HTTP
         ├─ Value: https://salesbestfriend-production.up.railway.app
         └─ Environments: ✅ All
```

---

## ⚠️ Important Notes

### **Why `vercel.json` doesn't work:**

- Vercel **ignores** `build.env` in `vercel.json` for some projects
- Environment variables **MUST** be set in Dashboard
- This is a Vercel limitation/quirk

### **After adding variables:**

- Variables are **only applied to NEW builds**
- Existing builds **won't** use new variables
- **Must** redeploy or push new commit

---

## ✅ Expected Result

After redeployment:

**Console should show:**
```javascript
🔍 Connecting to backend: https://salesbestfriend-production.up.railway.app  ✅
📤 Sending YouTube URL: https://www.youtube.com/watch?v=...
📡 Response status: 200 OK
```

**NOT:**
```javascript
❌ https://sales-best-friend-tkoj-xxx.vercel.app/api/process-youtube
```

---

## 🆘 Still Not Working?

### **Check:**

1. Variables are set for **Production** environment
2. Variable names are **exactly** `VITE_API_HTTP` and `VITE_API_WS` (case-sensitive!)
3. Values **don't** have trailing slashes
4. Redeployment **cleared** build cache
5. Browser cache **cleared** (Ctrl+Shift+R)

### **Debug:**

```bash
# Check current Vercel deployment
curl -s https://sales-best-friend-tkoj.vercel.app/assets/index-*.js | grep -o "salesbestfriend-production"

# Should output: salesbestfriend-production
# If not found, env vars are still not applied!
```

---

**Last Updated:** 2025-11-20  
**Status:** Awaiting Vercel Dashboard Configuration

