# WebSocket Implementation - Testing Checklist

Use this checklist to validate the WebSocket implementation is working correctly.

---

## ✅ Pre-Deployment Checklist

### Backend Preparation
- [ ] Backend code updated with `event_monitor.py`
- [ ] `requirements.txt` includes `flask-sock` and `websocket-client`
- [ ] `app.py` imports and initializes event system
- [ ] WebSocket endpoint `/api/events/ws` added

### Integration Preparation
- [ ] Integration updated to v0.7.0
- [ ] `api.py` has `connect_websocket()` method
- [ ] `coordinator.py` has WebSocket listener
- [ ] `__init__.py` starts/stops WebSocket
- [ ] `manifest.json` shows `local_push` IoT class

---

## 🚀 Deployment Steps

### 1. Deploy Backend

```bash
cd /Users/proboszcz/Devel/linux-audio-server

# Install dependencies
pip install -r services/bluetooth-api/requirements.txt

# Or rebuild Docker
docker-compose build
docker-compose up -d
```

**Verify:**
- [ ] Backend starts without errors
- [ ] Logs show: "Event monitoring started for real-time updates"
- [ ] Logs show: "MopidyEventMonitor started for player1" (x4)
- [ ] Logs show: "PulseAudioEventMonitor started"
- [ ] Logs show: "Connected to Mopidy WebSocket for player1" (x4)
- [ ] Logs show: "Listening to PulseAudio events"

### 2. Deploy Integration

```bash
# Copy to Home Assistant
scp -r custom_components/linux_audio_server root@10.9.0.3:/config/custom_components/
```

**Verify:**
- [ ] Files copied successfully
- [ ] Version is 0.7.0 in manifest.json

### 3. Restart Home Assistant

```bash
# Via UI: Settings → System → Restart
# Or SSH: ha core restart
```

**Verify:**
- [ ] HA restarts cleanly
- [ ] Integration loads without errors
- [ ] Logs show: "Starting WebSocket listener for real-time updates"
- [ ] Logs show: "Connecting to WebSocket event stream..."
- [ ] Logs show: "WebSocket connected successfully"
- [ ] Logs show: "WebSocket listener started for real-time state updates"

---

## 🧪 Functional Tests

### Test 1: Radio Playback State Change

**Objective:** Verify instant state detection when radio starts playing

**Steps:**
1. Open Home Assistant dashboard
2. Find a media player entity
3. Note current state (should be "idle")
4. Play a radio station
5. **Immediately** watch the state

**Expected Result:**
- [ ] State changes from "idle" to "playing" in **<1 second**
- [ ] No 2-5 second delay
- [ ] HA logs show: `WebSocket event: mopidy.playback_state_changed`
- [ ] HA logs show: `Triggering update from WebSocket event`
- [ ] Backend logs show: `Mopidy event (player2): playback_state_changed`

**If it fails:**
- Check backend logs for Mopidy WebSocket connection
- Check HA logs for WebSocket events
- Enable debug logging and retry

---

### Test 2: Radio Stop State Change

**Objective:** Verify instant detection when radio stops

**Steps:**
1. While radio is playing (from Test 1)
2. Stop the radio
3. **Immediately** watch the state

**Expected Result:**
- [ ] State changes from "playing" to "idle" in **<1 second**
- [ ] WebSocket event logged
- [ ] Update triggered

---

### Test 3: Multiple Simultaneous Players

**Objective:** Verify multi-player tracking works

**Steps:**
1. Play radio on Speaker 1 (e.g., kitchen)
2. Play different radio on Speaker 2 (e.g., bedroom)
3. Watch both states

**Expected Result:**
- [ ] Both speakers show "playing" instantly
- [ ] Each player's events are tracked separately
- [ ] Backend logs show events for player1 AND player2
- [ ] Player assignments recorded correctly

---

### Test 4: WebSocket Reconnection

**Objective:** Verify auto-reconnect works

**Steps:**
1. While integration is running
2. Restart the backend: `docker-compose restart bluetooth-api`
3. Wait and watch HA logs

**Expected Result:**
- [ ] HA logs show: "WebSocket connection closed"
- [ ] HA logs show: "Reconnecting WebSocket in 5 seconds..."
- [ ] After ~5 seconds: "Connecting to WebSocket event stream..."
- [ ] Connection re-established: "WebSocket connected successfully"
- [ ] System continues working

---

### Test 5: Fallback Polling

**Objective:** Verify polling backup works if WebSocket fails

**Steps:**
1. Stop the backend completely: `docker-compose stop bluetooth-api`
2. Try to play radio (will fail - that's OK)
3. Check HA logs
4. Start backend: `docker-compose start bluetooth-api`
5. Play radio

**Expected Result:**
- [ ] While backend down: "WebSocket connection failed"
- [ ] HA keeps trying to reconnect every 5s
- [ ] 10-second polling provides backup data (check coordinator logs)
- [ ] After backend up: WebSocket reconnects
- [ ] Radio playback detected instantly again

---

### Test 6: PulseAudio Events

**Objective:** Verify PulseAudio sink-input events work

**Steps:**
1. Enable debug logging in backend
2. Play radio on a speaker
3. Check backend logs for PulseAudio events

**Expected Result:**
- [ ] Backend logs show: `PulseAudio event: sink_input.new`
- [ ] Backend logs show: `PulseAudio event: sink_input.change`
- [ ] Events broadcasted to WebSocket
- [ ] HA receives and processes events

---

## 📊 Performance Tests

### Latency Measurement

**Objective:** Measure actual latency

**Steps:**
1. Use stopwatch or video recording
2. Start radio playback
3. Measure time until HA state changes

**Expected Result:**
- [ ] Latency < 500ms (target: <100ms)
- [ ] Consistently fast across multiple tests

### API Call Reduction

**Objective:** Verify fewer API calls

**Steps:**
1. Enable HA debug logging
2. Watch logs for 1 minute
3. Count API requests to backend

**Expected Result:**
- [ ] ~1-2 requests per minute (backup polling)
- [ ] Previously was 12 requests/minute
- [ ] 80-90% reduction confirmed

---

## 🐛 Debug Mode Testing

### Enable Debug Logging

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.linux_audio_server: debug
```

### Verify Debug Output

- [ ] Coordinator shows: "=== Determining state ==="
- [ ] WebSocket events logged: "WebSocket event: mopidy.playback_state_changed"
- [ ] Event handling logged: "Triggering update from WebSocket event"
- [ ] Backend shows Mopidy events: "Mopidy event (player2): ..."
- [ ] Backend shows PA events: "PulseAudio event: sink_input.new"

---

## ✅ Success Criteria

### All Tests Must Pass

- [X] ✅ Task 1: Add WebSocket dependencies
- [X] ✅ Task 2: Create Mopidy event monitor
- [X] ✅ Task 3: Create PulseAudio event monitor
- [X] ✅ Task 4: Create WebSocket server endpoint
- [X] ✅ Task 5: Add WebSocket client to integration
- [X] ✅ Task 6: Update coordinator for push updates
- [ ] ⏳ Task 7: Test and validate implementation

### Functional Requirements

- [ ] Radio playback detected in <1 second
- [ ] Radio stop detected in <1 second
- [ ] Multiple players tracked correctly
- [ ] WebSocket auto-reconnects
- [ ] Fallback polling works
- [ ] PulseAudio events detected

### Performance Requirements

- [ ] Latency < 500ms (ideally <100ms)
- [ ] API calls reduced by >80%
- [ ] No errors in logs
- [ ] System stable for 24+ hours

---

## 📝 Test Results Template

```
## WebSocket Implementation Test Results

**Date:** 2026-01-26
**Tester:** [Your Name]
**Environment:** HA 2026.x, Backend v1.0.0

### Deployment
- Backend deployed: ✅/❌
- Integration deployed: ✅/❌
- Backend started cleanly: ✅/❌
- HA connected to WebSocket: ✅/❌

### Functional Tests
- Test 1 (Radio start): ✅/❌ - Latency: ___ ms
- Test 2 (Radio stop): ✅/❌ - Latency: ___ ms
- Test 3 (Multi-player): ✅/❌
- Test 4 (Reconnection): ✅/❌
- Test 5 (Fallback): ✅/❌
- Test 6 (PA events): ✅/❌

### Performance Tests
- Average latency: ___ ms
- API calls/min: ___
- Reduction vs polling: ___%

### Issues Found
- [List any issues discovered]

### Overall Status
- [ ] ✅ All tests passed
- [ ] ⚠️ Minor issues (specify)
- [ ] ❌ Major issues (describe)

### Notes
[Any additional observations]
```

---

## 🚀 Ready to Test!

1. Follow deployment steps
2. Run through all functional tests
3. Verify performance improvements
4. Fill out test results template
5. Report any issues

**Good luck! 🎉**
