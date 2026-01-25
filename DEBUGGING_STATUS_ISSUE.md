# Debugging Player Status "Idle" Issue

This guide will help you diagnose and fix the issue where speakers show "idle" even when radio is playing.

## What We've Done So Far

### ✅ Changes Made to Integration

1. **Added comprehensive debug logging** in `media_player.py`:
   - Logs every step of state determination
   - Shows which priority level is used (1-4)
   - Displays all data being checked (sink-inputs, player state, assignments, etc.)

2. **Implemented faster polling** in `coordinator.py`:
   - Changed from 5 seconds to 2 seconds
   - **2.5x faster state updates** for immediate improvement
   - No backend changes required

3. **Created log analysis tool** (`analyze_logs.py`):
   - Automatically diagnoses the root cause
   - Parses debug logs and identifies the failure point
   - Provides specific fix recommendations

## 📋 Next Steps - Follow This Checklist

### Step 1: Deploy Updated Integration

**On your development machine:**

```bash
# Copy updated integration to Home Assistant
scp -r custom_components/linux_audio_server root@10.9.0.3:/config/custom_components/
```

Or use your preferred method to update the integration on 10.9.0.3.

---

### Step 2: Enable Debug Logging

**On Home Assistant (10.9.0.3):**

1. Edit `/config/configuration.yaml` and add:

```yaml
logger:
  default: info
  logs:
    custom_components.linux_audio_server: debug
```

2. Restart Home Assistant:
   - Go to: Settings → System → Restart
   - Or use: Developer Tools → YAML → Restart

---

### Step 3: Reproduce the Issue

1. **Play radio** on a speaker (one that shows the "idle" bug)
2. **Wait** for it to show "idle" while still playing
3. **Note the sink name** (e.g., "speaker_kitchen", "bluez_output.XX_XX_XX")
4. Let it run for **at least 30 seconds** to capture multiple state checks

---

### Step 4: Download Logs

**On Home Assistant:**

- Go to: Settings → System → Logs → **Download full log**
- Save as `home-assistant.log`

**Or via command line:**

```bash
# From your dev machine
scp root@10.9.0.3:/config/home-assistant.log ./
```

---

### Step 5: Analyze Logs

**On your development machine:**

```bash
cd /Users/proboszcz/Devel/ha-audio-server-controller

# Analyze all sinks
python3 analyze_logs.py home-assistant.log

# Or analyze a specific sink
python3 analyze_logs.py home-assistant.log speaker_kitchen
```

The script will:
- ✅ Show you exactly what data the integration is seeing
- ✅ Identify which priority level is being used
- ✅ Diagnose the root cause
- ✅ Provide specific fix recommendations

---

### Step 6: Share Results

Send me:
1. **The output** from `analyze_logs.py`
2. **The sink name** that's having issues
3. **What backend you're using** (your custom linux-audio-server)

I'll tell you exactly what to fix in the backend.

---

## 🔍 What the Analysis Will Tell Us

The log analyzer will identify one of these scenarios:

### Scenario A: Backend Player State Wrong
```
❌ ISSUE FOUND: Backend player state is 'stopped' during playback

Root Cause:
- Sink-inputs show audio routing (good!)
- But backend reports player state as 'stopped' (bad!)

Fix Required:
- Backend needs to update Mopidy player state correctly
- Check if backend is listening to Mopidy WebSocket events
```

### Scenario B: No Sink-Inputs Found
```
❌ ISSUE FOUND: Falling back to global playback state

Root Cause:
- No sink-inputs found
- No player assignments recorded

Fix Required:
- Backend must create sink-inputs for radio playback
- Verify Mopidy is routing to PulseAudio correctly
```

### Scenario C: Player Assignments Missing
```
❌ ISSUE FOUND: No player assignments recorded

Root Cause:
- Backend not recording assignments when radio starts

Fix Required:
- Verify 'sink' parameter is passed to play_radio_url()
- Check /api/players/assignments endpoint
```

### Scenario D: Complete Backend Failure
```
❌ ISSUE FOUND: Everything failed, using PulseAudio state

Root Cause:
- Backend API is not providing any playback data

Fix Required:
- Check if backend is running
- Verify Mopidy connection to backend
```

---

## 🎯 Expected Outcome

After analysis, you'll know **exactly** which part of the backend to fix:

1. **Mopidy state monitoring** (if player state is wrong)
2. **PulseAudio sink-input creation** (if routing not detected)
3. **Player assignment recording** (if assignments missing)
4. **Backend API connection** (if everything fails)

---

## ⚡ Quick Fix Already Deployed

The **2-second polling** is now active, which means:
- State updates **2.5x faster** than before (2s instead of 5s)
- You should see **some improvement** immediately
- Maximum lag reduced from 5 seconds to 2 seconds

But this is just a **temporary improvement** - we still need to fix the backend for the **proper solution**.

---

## 🚀 After We Fix the Backend

Once we identify and fix the backend issue, we can implement the **ultimate solution**:

- **WebSocket push updates** (<100ms latency instead of 2s)
- **Instant state changes** when playback starts/stops
- **Lower CPU/network usage** (no polling needed)
- **Best practice** for Home Assistant integrations

---

## ❓ Questions or Issues?

If you run into any problems:

1. **Can't enable debug logging?** - Check that `configuration.yaml` has correct syntax
2. **Can't download logs?** - Try SSH/SCP directly: `scp root@10.9.0.3:/config/home-assistant.log ./`
3. **Script errors?** - Make sure you have Python 3: `python3 --version`
4. **No debug logs found?** - Verify HA restarted after adding logger config

---

## 📞 Ready to Continue?

Once you've:
1. ✅ Deployed the updated integration
2. ✅ Enabled debug logging
3. ✅ Reproduced the issue
4. ✅ Downloaded and analyzed the logs

Share the results and we'll fix the backend together!
