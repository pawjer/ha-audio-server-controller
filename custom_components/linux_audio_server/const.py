"""Constants for the Linux Audio Server integration."""

DOMAIN = "linux_audio_server"

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
DEFAULT_PORT = 6681
DEFAULT_NAME = "Linux Audio Server"

# Update intervals
SCAN_INTERVAL_SINKS = 5  # seconds
SCAN_INTERVAL_STREAMS = 2  # seconds (more frequent for active streams)

# API endpoints
API_BASE = "/api"
API_AUDIO_SINKS = f"{API_BASE}/audio/sinks"
API_AUDIO_VOLUME = f"{API_BASE}/audio/volume"
API_AUDIO_SINK_INPUTS = f"{API_BASE}/audio/sink-inputs"
API_AUDIO_SINK_DEFAULT = f"{API_BASE}/audio/sink/default"
API_BLUETOOTH_DEVICES = f"{API_BASE}/bluetooth/devices"
API_HEALTH = f"{API_BASE}/health"

# Device classes
DEVICE_CLASS_SPEAKER = "speaker"

# Entity attributes
ATTR_SINK_NAME = "sink_name"
ATTR_SINK_INDEX = "sink_index"
ATTR_SINK_STATE = "sink_state"
ATTR_IS_DEFAULT = "is_default"
ATTR_STREAM_INDEX = "stream_index"
ATTR_STREAM_NAME = "stream_name"
