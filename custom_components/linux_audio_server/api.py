"""API client for Linux Audio Server."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from urllib.parse import quote

import aiohttp
from aiohttp import ClientError

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10


class LinuxAudioServerApiClient:
    """API client for communicating with Linux Audio Server."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._port = port
        self._session = session
        self._base_url = f"http://{host}:{port}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a request to the API."""
        url = f"{self._base_url}{endpoint}"

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                if method == "GET":
                    async with self._session.get(url) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method == "POST":
                    async with self._session.post(url, json=data) as response:
                        response.raise_for_status()
                        return await response.json()
                elif method == "DELETE":
                    async with self._session.delete(url) as response:
                        response.raise_for_status()
                        return await response.json()
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout connecting to %s: %s", url, err)
            raise ApiClientError(f"Timeout connecting to {url}") from err
        except (aiohttp.ContentTypeError, json.JSONDecodeError) as err:
            _LOGGER.error("Invalid JSON response from %s: %s", url, err)
            raise ApiClientError(f"Invalid JSON response from {url}") from err
        except ClientError as err:
            _LOGGER.error("Error communicating with %s: %s", url, err)
            raise ApiClientError(f"Error communicating with {url}") from err

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the server."""
        return await self._request("GET", "/api/health")

    async def get_sinks(self) -> dict[str, Any]:
        """Get all audio sinks."""
        return await self._request("GET", "/api/audio/sinks")

    async def get_default_sink(self) -> dict[str, Any]:
        """Get the default audio sink."""
        return await self._request("GET", "/api/audio/sink/default")

    async def set_default_sink(self, sink_name: str) -> dict[str, Any]:
        """Set the default audio sink."""
        return await self._request(
            "POST",
            "/api/audio/sink/default",
            {"sink_name": sink_name},
        )

    async def get_volume(self) -> dict[str, Any]:
        """Get the system volume."""
        return await self._request("GET", "/api/audio/volume")

    async def set_volume(self, volume: float) -> dict[str, Any]:
        """Set the system volume (0.0 to 1.0)."""
        return await self._request("POST", "/api/audio/volume", {"volume": volume})

    async def get_sink_volume(self, sink_name: str) -> dict[str, Any]:
        """Get the volume of a specific sink."""
        encoded_name = quote(sink_name, safe="")
        return await self._request("GET", f"/api/audio/sink/{encoded_name}/volume")

    async def set_sink_volume(self, sink_name: str, volume: float) -> dict[str, Any]:
        """Set the volume of a specific sink (0.0 to 1.0)."""
        encoded_name = quote(sink_name, safe="")
        return await self._request(
            "POST",
            f"/api/audio/sink/{encoded_name}/volume",
            {"volume": volume},
        )

    async def set_sink_mute(self, sink_name: str, mute: bool) -> dict[str, Any]:
        """Mute or unmute a specific sink."""
        encoded_name = quote(sink_name, safe="")
        return await self._request(
            "POST",
            f"/api/audio/sink/{encoded_name}/mute",
            {"mute": mute},
        )

    async def get_sink_inputs(self) -> dict[str, Any]:
        """Get all active audio streams (sink inputs)."""
        return await self._request("GET", "/api/audio/sink-inputs")

    async def set_stream_volume(self, input_index: int, volume: float) -> dict[str, Any]:
        """Set the volume of a specific stream."""
        return await self._request(
            "POST",
            f"/api/audio/sink-input/{input_index}/volume",
            {"volume": volume},
        )

    async def set_stream_mute(self, input_index: int, mute: bool) -> dict[str, Any]:
        """Mute or unmute a specific stream."""
        return await self._request(
            "POST",
            f"/api/audio/sink-input/{input_index}/mute",
            {"mute": mute},
        )

    async def move_stream(self, input_index: int, sink_name: str) -> dict[str, Any]:
        """Move a stream to a different sink."""
        return await self._request(
            "POST",
            "/api/audio/sink-input/move",
            {"input_index": input_index, "sink_name": sink_name},
        )

    async def get_combined_sinks(self) -> dict[str, Any]:
        """Get all combined sinks and stereo pairs."""
        return await self._request("GET", "/api/audio/combined-sinks")

    async def create_combined_sink(
        self, name: str, sinks: list[str]
    ) -> dict[str, Any]:
        """Create a combined sink for multi-room audio."""
        return await self._request(
            "POST",
            "/api/audio/combined-sink",
            {"name": name, "sinks": sinks},
        )

    async def create_stereo_pair(
        self, name: str, left_sink: str, right_sink: str
    ) -> dict[str, Any]:
        """Create a stereo pair."""
        return await self._request(
            "POST",
            "/api/audio/stereo-pair",
            {"name": name, "left_sink": left_sink, "right_sink": right_sink},
        )

    async def delete_combined_sink(self, sink_name: str) -> dict[str, Any]:
        """Delete a combined sink or stereo pair."""
        encoded_name = quote(sink_name, safe="")
        return await self._request("DELETE", f"/api/audio/combined-sink/{encoded_name}")

    async def get_bluetooth_devices(self) -> dict[str, Any]:
        """Get all Bluetooth devices."""
        return await self._request("GET", "/api/bluetooth/devices")

    async def get_playback_status(self) -> dict[str, Any]:
        """Get current playback state and track information."""
        return await self._request("GET", "/api/playback/status")

    async def play(self) -> dict[str, Any]:
        """Start or resume playback."""
        return await self._request("POST", "/api/playback/play")

    async def pause(self) -> dict[str, Any]:
        """Pause current playback."""
        return await self._request("POST", "/api/playback/pause")

    async def stop(self) -> dict[str, Any]:
        """Stop playback completely."""
        return await self._request("POST", "/api/playback/stop")

    async def next_track(self) -> dict[str, Any]:
        """Skip to the next track."""
        return await self._request("POST", "/api/playback/next")

    async def previous_track(self) -> dict[str, Any]:
        """Go back to the previous track."""
        return await self._request("POST", "/api/playback/previous")

    async def get_radio_streams(self) -> dict[str, Any]:
        """Get all radio streams."""
        return await self._request("GET", "/api/radio/streams")

    async def add_radio_stream(self, name: str, url: str) -> dict[str, Any]:
        """Add a new radio stream."""
        return await self._request("POST", "/api/radio/stream", {"name": name, "url": url})

    async def delete_radio_stream(self, name: str) -> dict[str, Any]:
        """Delete a radio stream."""
        encoded_name = quote(name, safe="")
        return await self._request("DELETE", f"/api/radio/stream/{encoded_name}")

    async def play_radio_stream(self, name: str) -> dict[str, Any]:
        """Play a predefined radio stream."""
        return await self._request("POST", "/api/radio/play", {"stream": name})

    async def play_radio_url(self, url: str) -> dict[str, Any]:
        """Play arbitrary radio URL."""
        return await self._request("POST", "/api/radio/play_url", {"url": url})

    async def scan_bluetooth(self, duration: int = 10) -> dict[str, Any]:
        """Scan for Bluetooth devices."""
        return await self._request("POST", "/api/bluetooth/scan", {"duration": duration})

    async def pair_bluetooth(self, address: str) -> dict[str, Any]:
        """Pair with a Bluetooth device."""
        return await self._request("POST", "/api/bluetooth/pair", {"address": address})

    async def connect_bluetooth(self, address: str) -> dict[str, Any]:
        """Connect to a Bluetooth device."""
        return await self._request("POST", "/api/bluetooth/connect", {"address": address})

    async def disconnect_bluetooth(self, address: str) -> dict[str, Any]:
        """Disconnect from a Bluetooth device."""
        return await self._request("POST", "/api/bluetooth/disconnect", {"address": address})

    async def connect_and_set_default_bluetooth(self, address: str) -> dict[str, Any]:
        """Connect to Bluetooth device and set as default output."""
        return await self._request("POST", "/api/bluetooth/connect-and-set-default", {"address": address})

    # TTS endpoints
    async def speak_tts(self, message: str, language: str = "en") -> dict[str, Any]:
        """Speak text using text-to-speech."""
        return await self._request("POST", "/api/tts/speak", {"message": message, "language": language})


class ApiClientError(Exception):
    """Exception raised for API client errors."""
