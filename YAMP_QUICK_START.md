# YAMP Dashboard - Quick Start Guide

## 5-Minute Setup

### Step 1: Install YAMP (2 minutes)
```
1. HACS → Frontend
2. Search "yet another media player"
3. Download
4. Restart Home Assistant
```

### Step 2: Get Your Radio Station Names (1 minute)

**Option A: Backend Config**
```bash
# SSH to your server
cat config/bluetooth-api/radio_streams.conf

# Example output:
# Jazz FM=http://url...
# Classical=http://url...
```

**Option B: Home Assistant**
```
Developer Tools → States → search "select.*_radio"
Look at options list
```

### Step 3: Copy Dashboard (1 minute)

1. **Settings** → **Dashboards** → **+ Add Dashboard**
2. Name it "Audio"
3. **Edit** → **⋮** → **Raw configuration editor**
4. Copy content from `dashboard-yamp.yaml`
5. Paste and save

### Step 4: Customize (1 minute)

**Replace these:**
```yaml
# Your media player entities
- entity_id: media_player.usb_c_dual_4k_dock_analogowe_stereo
  name: USB-C Dock
# Change to:
- entity_id: media_player.YOUR_SINK
  name: YOUR_ROOM

# Your radio stations
- name: "Jazz Radio"
  service_data:
    name: "Jazz Radio"  # Must match backend
# Change to:
- name: "YOUR_STATION"
  service_data:
    name: "BACKEND_NAME"  # Exact name from Step 2

# Your Bluetooth addresses
address: "54:B7:E5:89:E6:E3"
# Change to:
address: "XX:XX:XX:XX:XX:XX"  # Your BT MAC
```

### Step 5: Done! Use It

**Play Radio:**
```
1. Tap room chip (e.g., "Kitchen")
2. Tap ⋮ menu
3. Tap radio station
```

**Multi-Room:**
```
1. Tap "Kitchen" chip → Menu → "Jazz Radio"
2. Tap "Living Room" chip → Menu → "Player 3 → This Room"
3. Tap "Rock Station"
→ Different music in each room!
```

---

## Common Customizations

### Add More Rooms
```yaml
entities:
  - entity_id: media_player.kitchen
    name: Kitchen
  - entity_id: media_player.living_room
    name: Living
  - entity_id: media_player.bedroom
    name: Bedroom
  # Add as many as you want
```

### Add More Radio Stations
```yaml
actions:
  # After "📻 RADIO STATIONS" header
  - name: "Your New Station"
    icon: mdi:radio-fm
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Backend Station Name"
    in_menu: true
```

### Remove Player Assignment (If Not Needed)
```yaml
# Just delete this entire section:
- name: "🎵 ASSIGN PLAYER"
  ...
- name: "Player 2 → This Room"
  ...
# etc.
```

### Change Idle Timeout
```yaml
idle_timeout_ms: 30000  # 30 seconds (default)
idle_timeout_ms: 60000  # 1 minute (relaxed)
idle_timeout_ms: 15000  # 15 seconds (aggressive)
```

---

## Troubleshooting

### "Custom element doesn't exist"
```
1. Check HACS → Frontend → YAMP installed
2. Clear browser cache (Ctrl+Shift+R)
3. Restart Home Assistant
```

### Radio Station Doesn't Play
```
1. Check station name matches backend EXACTLY
2. Case sensitive: "Jazz FM" ≠ "jazz fm"
3. Test via Developer Tools:
   service: linux_audio_server.play_radio_stream
   data:
     name: "Your Station"
```

### Player Assignment Doesn't Work
```
1. Verify sink_name attribute exists:
   Developer Tools → States → media_player.your_sink
   Look for "sink_name" in attributes
2. Or hardcode for testing:
   sink_name: "bluez_output.XX_XX_XX.1"
```

### Chips Not Showing Room Names
```
# Make sure names are short
✅ Good: "Kitchen", "Living", "Dock"
❌ Too long: "USB-C Dual 4K Dock Analogowe Stereo"

# Update in entities section:
- entity_id: media_player.long_name
  name: "Short"  # Override here
```

---

## Quick Reference

### Menu Structure
```
⋮ Menu
├── 📻 RADIO STATIONS
│   └── [Your stations here]
├── 🎵 ASSIGN PLAYER
│   └── Player 2/3/4 options
└── ⚙️ UTILITIES
    └── Stop, Source, Info
```

### Key Actions
| Action | How |
|--------|-----|
| Switch room | Tap chip at top |
| Play radio | Menu → Radio station |
| Assign player | Menu → Player X → This Room |
| Stop music | Menu → Stop Playback |
| Bluetooth | Hold device in BT section |

### File Locations
```
dashboard-yamp.yaml              # Standard version
dashboard-yamp-advanced.yaml     # With Mushroom cards
DASHBOARD_YAMP.md                # Full documentation
YAMP_MENU_EXAMPLE.md             # Visual examples
YAMP_QUICK_START.md              # This file
```

---

## Next Steps

### Basic Setup
✅ Install YAMP
✅ Copy dashboard-yamp.yaml
✅ Customize entities and stations
✅ Start using it!

### Advanced Setup (Optional)
- Install Mushroom cards
- Use dashboard-yamp-advanced.yaml
- Enhanced status visualization
- Create audio scene scripts

### Power User
- Add more stations (10+)
- Organize by genre
- Custom icons per station
- Create automation triggers

---

## Support

- **Full docs:** [DASHBOARD_YAMP.md](DASHBOARD_YAMP.md)
- **Visual guide:** [YAMP_MENU_EXAMPLE.md](YAMP_MENU_EXAMPLE.md)
- **YAMP GitHub:** https://github.com/jianyu-li/yet-another-media-player
- **Integration:** [README.md](README.md)

**Enjoy your multi-room audio dashboard!** 🎵
