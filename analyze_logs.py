#!/usr/bin/env python3
"""
Log analyzer for Linux Audio Server integration.
Helps diagnose "idle" state issues when radio is playing.

Usage:
    python3 analyze_logs.py home-assistant.log [sink_name]

Example:
    python3 analyze_logs.py home-assistant.log speaker_kitchen
"""

import sys
import re
from collections import defaultdict


def analyze_logs(log_file, sink_name=None):
    """Analyze Home Assistant logs for state determination issues."""

    print("=" * 80)
    print("Linux Audio Server - State Diagnosis Tool")
    print("=" * 80)
    print()

    with open(log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find all sink names if not specified
    sink_names = set()
    sink_pattern = re.compile(r'\[([^\]]+)\] === Determining state ===')

    for line in lines:
        match = sink_pattern.search(line)
        if match:
            sink_names.add(match.group(1))

    if not sink_names:
        print("❌ No debug logs found!")
        print()
        print("Make sure you enabled debug logging:")
        print("  logger:")
        print("    logs:")
        print("      custom_components.linux_audio_server: debug")
        print()
        return

    print(f"📊 Found {len(sink_names)} sink(s): {', '.join(sorted(sink_names))}")
    print()

    # If sink_name specified, filter to that sink
    if sink_name:
        if sink_name not in sink_names:
            print(f"❌ Sink '{sink_name}' not found in logs!")
            print(f"Available sinks: {', '.join(sorted(sink_names))}")
            return
        sink_names = {sink_name}

    # Analyze each sink
    for sink in sorted(sink_names):
        analyze_sink(lines, sink)
        print()


def analyze_sink(lines, sink_name):
    """Analyze logs for a specific sink."""

    print(f"🔍 Analyzing: {sink_name}")
    print("-" * 80)

    # Find state determination blocks
    state_blocks = []
    current_block = []
    in_block = False

    for line in lines:
        if f"[{sink_name}] === Determining state ===" in line:
            if current_block:
                state_blocks.append(current_block)
            current_block = [line]
            in_block = True
        elif in_block and f"[{sink_name}]" in line:
            current_block.append(line)
            if "Returning" in line:
                state_blocks.append(current_block)
                current_block = []
                in_block = False

    if not state_blocks:
        print("  ⚠️  No state determination logs found")
        return

    # Analyze the most recent block
    latest_block = state_blocks[-1]

    print(f"  📅 Total state checks: {len(state_blocks)}")
    print(f"  🕐 Analyzing most recent check...")
    print()

    # Parse the block
    results = {
        'sink_inputs_count': None,
        'active_player': None,
        'player_state': None,
        'assigned_player': None,
        'global_state': None,
        'pa_state': None,
        'final_state': None,
        'priority_used': None,
    }

    for line in latest_block:
        # Sink inputs
        if "Total sink_inputs:" in line:
            match = re.search(r'Total sink_inputs: (\d+)', line)
            if match:
                results['sink_inputs_count'] = int(match.group(1))

        # Priority 1: Active player from sink-inputs
        if "Priority 1: Active player from sink-inputs:" in line:
            match = re.search(r'Active player from sink-inputs: (\w+)', line)
            if match:
                results['active_player'] = match.group(1)
        elif "Priority 1: No active player found" in line:
            results['active_player'] = None

        # Player state
        if "Found active player" in line and "with state:" in line:
            match = re.search(r'with state: (\w+)', line)
            if match:
                results['player_state'] = match.group(1)

        # Priority 2: Player assignments
        if "Priority 2: Checking player assignments. Assigned player:" in line:
            match = re.search(r'Assigned player: (\w+)', line)
            if match:
                results['assigned_player'] = match.group(1)

        # Priority 3: Global playback
        if "Priority 3: Checking global playback state:" in line:
            match = re.search(r'playback state: (\w+)', line)
            if match:
                results['global_state'] = match.group(1)

        # Priority 4: PA state
        if "Priority 4: Falling back to PulseAudio sink state:" in line:
            match = re.search(r'sink state: (\w+)', line)
            if match:
                results['pa_state'] = match.group(1)

        # Final state
        if "Returning" in line:
            if "Priority 1" in line or "from active player" in line:
                results['priority_used'] = 1
            elif "Priority 2" in line or "from assigned player" in line:
                results['priority_used'] = 2
            elif "Priority 3" in line or "from global playback" in line:
                results['priority_used'] = 3
            elif "Priority 4" in line or "from PA sink state" in line:
                results['priority_used'] = 4

            if "PLAYING" in line:
                results['final_state'] = "PLAYING"
            elif "PAUSED" in line:
                results['final_state'] = "PAUSED"
            elif "IDLE" in line:
                results['final_state'] = "IDLE"
            elif "ON" in line:
                results['final_state'] = "ON"
            elif "OFF" in line:
                results['final_state'] = "OFF"

    # Display results
    print("  📊 State Determination Results:")
    print()
    print(f"    Sink-inputs found:     {results['sink_inputs_count']}")
    print(f"    Active player:         {results['active_player'] or 'None'}")
    if results['active_player']:
        print(f"    Player state:          {results['player_state'] or 'Unknown'}")
    print(f"    Assigned player:       {results['assigned_player'] or 'None'}")
    print(f"    Global playback state: {results['global_state'] or 'Not checked'}")
    print(f"    PulseAudio state:      {results['pa_state'] or 'Not checked'}")
    print()
    print(f"    ✅ Final state:         {results['final_state']} (Priority {results['priority_used']})")
    print()

    # Diagnosis
    print("  🔬 Diagnosis:")
    print()

    if results['final_state'] == "IDLE" or results['final_state'] == "OFF":
        # Issue detected
        if results['priority_used'] == 1:
            if results['player_state'] == 'stopped':
                print("  ❌ ISSUE FOUND: Backend player state is 'stopped' during playback")
                print()
                print("     Root Cause:")
                print("     - Sink-inputs show audio routing (good!)")
                print("     - But backend reports player state as 'stopped' (bad!)")
                print()
                print("     Fix Required:")
                print("     - Backend needs to update Mopidy player state correctly")
                print("     - Check if backend is listening to Mopidy WebSocket events")
                print("     - Verify 'playback_state_changed' events update backend state")
            else:
                print("  ⚠️  Player found in sink-inputs but state is unexpected")
                print(f"     Player state: {results['player_state']}")

        elif results['priority_used'] == 2:
            if results['player_state'] == 'stopped':
                print("  ❌ ISSUE FOUND: Assigned player state is 'stopped' during playback")
                print()
                print("     Root Cause:")
                print("     - No sink-inputs found (concerning!)")
                print("     - Falling back to player assignments")
                print("     - Assigned player reports 'stopped'")
                print()
                print("     Fix Required:")
                print("     - Check why sink-inputs are not created")
                print("     - Verify Mopidy is routing audio to PulseAudio")
                print("     - Backend player state also needs fixing")

        elif results['priority_used'] == 3:
            print("  ❌ ISSUE FOUND: Falling back to global playback state")
            print()
            print("     Root Cause:")
            print("     - No sink-inputs found")
            print("     - No player assignments recorded")
            print("     - Using global (player1) state as fallback")
            print()
            print("     Fix Required:")
            print("     - Backend must record player assignments when radio starts")
            print("     - Verify 'sink' parameter is passed to play_radio_url()")
            print("     - Check /api/players/assignments endpoint")

        elif results['priority_used'] == 4:
            print("  ❌ ISSUE FOUND: Everything failed, using PulseAudio state")
            print()
            print("     Root Cause:")
            print("     - No sink-inputs")
            print("     - No player assignments")
            print("     - No global playback state")
            print("     - Complete backend data failure")
            print()
            print("     Fix Required:")
            print("     - Backend API is not providing playback data")
            print("     - Check if backend is running")
            print("     - Verify Mopidy connection to backend")
    else:
        print("  ✅ State looks correct!")
        print(f"     Returning {results['final_state']} from Priority {results['priority_used']}")

    print()
    print("  📋 Recent state determination log:")
    print()
    for line in latest_block[-10:]:  # Last 10 lines
        print(f"     {line.strip()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_logs.py <log_file> [sink_name]")
        print()
        print("Example:")
        print("  python3 analyze_logs.py home-assistant.log")
        print("  python3 analyze_logs.py home-assistant.log speaker_kitchen")
        sys.exit(1)

    log_file = sys.argv[1]
    sink_name = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        analyze_logs(log_file, sink_name)
    except FileNotFoundError:
        print(f"❌ Error: Log file '{log_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error analyzing logs: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
