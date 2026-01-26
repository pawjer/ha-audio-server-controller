# YAMP Menu-Based Radio UX - Visual Example

## The New UX Flow

### Before (Separate Radio Tiles)
```
┌────────────────────────────────────┐
│  🎵 Multi-Room Audio               │
│  ┌──────────────────────────────┐  │
│  │ [Kitchen] [Living] [Bedroom] │  │
│  │                              │  │
│  │  ♫ Now Playing: Jazz Radio  │  │
│  │  ▶ ⏸ ⏹ ⏭                    │  │
│  │  🔊 ═════════════ 80%        │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│  📻 Quick Radio                     │
│  ┌────────────┐  ┌────────────┐   │
│  │ USB-C Dock │  │ Paulacton  │   │
│  │ [Jazz ▼]   │  │ [Rock ▼]   │   │
│  └────────────┘  └────────────┘   │
└────────────────────────────────────┘
```
**Issues:**
- Scrolling required
- Radio tiles take screen space
- Separate tiles per room clutter UI
- Not obvious which radio affects which room

---

### After (Menu Integration) ✨
```
┌────────────────────────────────────┐
│  🎵 Multi-Room Audio               │
│  ┌──────────────────────────────┐  │
│  │ [Kitchen] [Living] [Bedroom] │  │◄─ Tap to select room
│  │                              │  │
│  │  ♫ Now Playing: Jazz Radio  │  │
│  │  ▶ ⏸ ⏹ ⏭                 ⋮ │  │◄─ Tap ⋮ for menu
│  │  🔊 ═════════════ 80%        │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘

Tap ⋮ menu:
┌────────────────────────────────────┐
│  Menu                              │
├────────────────────────────────────┤
│  📻 RADIO STATIONS                 │
│  🎵 Jazz Radio                     │◄─ Tap to play
│  🎹 Classical Music                │
│  🎸 Rock Station                   │
│  🌅 Chill Music                    │
│  ─────────────────                 │
│  🎵 ASSIGN PLAYER                  │
│  ② Player 2 → This Room           │
│  ③ Player 3 → This Room           │
│  ④ Player 4 → This Room           │
│  ─────────────────                 │
│  ⚙️ UTILITIES                      │
│  ⏹ Stop Playback                  │
│  🔊 Output Selection               │
│  ℹ️ More Info                      │
└────────────────────────────────────┘
```

**Benefits:**
- ✅ Everything in one card
- ✅ No scrolling needed
- ✅ Clear room context (chip shows selected room)
- ✅ Organized menu structure
- ✅ Radio + Player assignment + Utilities in one place
- ✅ Cleaner dashboard (no separate radio tiles)

---

## Real Usage Example

### Scenario: Play Jazz in Kitchen, Rock in Living Room

**Step 1: Kitchen Jazz**
```
1. Tap "Kitchen" chip
2. Tap ⋮ menu
3. Tap "Jazz Radio"
   → Jazz plays on Kitchen speaker
```

**Step 2: Living Room Rock**
```
4. Tap "Living Room" chip
5. Tap ⋮ menu
6. Tap "🎵 ASSIGN PLAYER"
7. Tap "Player 3 → This Room"
8. Tap "Rock Station"
   → Rock plays on Living Room speaker
```

**Result:**
- Kitchen: Jazz Radio (Player 2)
- Living Room: Rock Station (Player 3)
- Two different stations playing simultaneously!

---

## Menu Organization Strategy

```yaml
# Section 1: Radio (Most Frequent Action)
📻 RADIO STATIONS
  - Quick access to all stations
  - Most-used feature on top
  - Icons differentiate station types

# Section 2: Player Assignment (Advanced Users)
🎵 ASSIGN PLAYER
  - Multi-room setup
  - Shows which player goes to current room
  - Template auto-fills sink_name

# Section 3: Utilities (Less Frequent)
⚙️ UTILITIES
  - Stop, source, more info
  - Bottom of menu (least used)
```

**Design Principle:** Most-used actions on top, advanced features in middle, utilities at bottom.

---

## Customization Examples

### Minimal Radio Setup (3 stations)
```yaml
actions:
  - name: "📻 RADIO STATIONS"
    icon: mdi:radio
    in_menu: true

  - name: "Jazz"
    icon: mdi:music-note
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Jazz FM"
    in_menu: true

  - name: "News"
    icon: mdi:microphone
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "BBC News"
    in_menu: true

  - name: "Classical"
    icon: mdi:piano
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Classical Radio"
    in_menu: true
```

### Extended Radio Setup (8+ stations)
```yaml
actions:
  - name: "📻 MUSIC"
    icon: mdi:music
    in_menu: true

  - name: "Jazz"
    icon: mdi:music-note
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Jazz FM"
    in_menu: true

  - name: "Classical"
    icon: mdi:piano
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Classical"
    in_menu: true

  - name: "Rock"
    icon: mdi:guitar-electric
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Rock Station"
    in_menu: true

  - name: "Chill"
    icon: mdi:weather-sunset
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Lounge Music"
    in_menu: true

  # Second section for talk/news
  - name: "─────────────────"
    icon: mdi:minus
    in_menu: true

  - name: "📻 TALK & NEWS"
    icon: mdi:radio
    in_menu: true

  - name: "BBC News"
    icon: mdi:newspaper
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "BBC World Service"
    in_menu: true

  - name: "NPR"
    icon: mdi:microphone
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "NPR News"
    in_menu: true

  - name: "Podcasts"
    icon: mdi:podcast
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Podcast Stream"
    in_menu: true
```

### Genre-Organized Setup
```yaml
actions:
  - name: "🎸 ROCK & POP"
    icon: mdi:guitar-electric
    in_menu: true

  - name: "Classic Rock"
    icon: mdi:guitar-acoustic
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Classic Rock"
    in_menu: true

  - name: "Modern Rock"
    icon: mdi:guitar-electric
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Alt Rock"
    in_menu: true

  - name: "─────────────────"
    icon: mdi:minus
    in_menu: true

  - name: "🎹 CLASSICAL & JAZZ"
    icon: mdi:piano
    in_menu: true

  - name: "Classical"
    icon: mdi:piano
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Classical FM"
    in_menu: true

  - name: "Jazz"
    icon: mdi:saxophone
    service: linux_audio_server.play_radio_stream
    service_data:
      name: "Jazz Radio"
    in_menu: true
```

---

## Pro Tips

### Icon Selection
Choose icons that make stations instantly recognizable:
- 🎵 `mdi:music-note` - Generic music
- 🎹 `mdi:piano` - Classical
- 🎸 `mdi:guitar-electric` - Rock
- 🎺 `mdi:saxophone` - Jazz
- 🎤 `mdi:microphone` - Talk/Interview
- 📰 `mdi:newspaper` - News
- 🎙️ `mdi:podcast` - Podcasts
- 🌅 `mdi:weather-sunset` - Chill/Ambient
- 🌃 `mdi:weather-night` - Late night/Smooth

### Menu Length
- **3-5 stations:** No separators needed, simple list
- **6-10 stations:** Add genre separators for organization
- **10+ stations:** Group by genre with headers

### Station Naming
```yaml
# ✅ Good - Short, clear
"Jazz FM"
"Classical"
"Rock 101"

# ❌ Avoid - Too long
"Jazz Music Radio Station 24/7 Streaming"
```

### Testing
1. Add stations one at a time
2. Test each station plays correctly
3. Verify station name matches backend exactly
4. Check icons display correctly

---

## Comparison: Before vs After

| Aspect | Before (Tiles) | After (Menu) |
|--------|---------------|--------------|
| **Screen Space** | Separate section | Integrated in menu |
| **Scrolling** | Required | Minimal |
| **Organization** | Separate tiles per room | One menu, room via chips |
| **Clicks to Play** | 2 (select room tile, choose station) | 3 (select room chip, menu, station) |
| **Visual Clarity** | Room context unclear | Clear room chip selection |
| **Scalability** | Tiles multiply with rooms | Single menu for all rooms |
| **Customization** | Per-room tiles | Single station list |

**Verdict:** Menu approach is cleaner, more scalable, and better organized for multi-room setups.

---

## Summary

The menu-based radio UX provides:
- ✅ Cleaner dashboard (no separate radio section)
- ✅ Better organization (Radio → Assignment → Utilities)
- ✅ Scalable to many stations without clutter
- ✅ Clear room context via chip selection
- ✅ All controls in one unified card

**Recommended for:** All multi-room audio setups with YAMP
