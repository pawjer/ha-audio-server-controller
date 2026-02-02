"""API client for Linux Audio Server."""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any
from urllib.parse import quote

import aiohttp
from aiohttp import ClientError

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 20  # Increased from 10 to handle intermittent backend slowdowns
BLUETOOTH_TIMEOUT = 30  # Bluetooth operations can take longer
MAX_RETRIES = 2  # Number of retries for failed requests
RETRY_DELAY = 1.0  # Initial delay between retries in seconds


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
        timeout: float = DEFAULT_TIMEOUT,
        retry: bool = True,
    ) -> dict[str, Any]:
        """Make a request to the API with automatic retry on timeout."""
        last_error = None
        retries = MAX_RETRIES if retry else 0

        for attempt in range(retries + 1):
            if attempt > 0:
                delay = RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                _LOGGER.warning(
                    "Retrying request to %s (attempt %d/%d) after %.1fs delay",
                    endpoint, attempt + 1, retries + 1, delay
                )
                await asyncio.sleep(delay)

            try:
                return await self._do_request(method, endpoint, data, timeout)
            except ApiClientError as err:
                last_error = err
                if attempt < retries:
                    # Only retry on timeout errors, not on other errors
                    if "Timeout" in str(err):
                        continue
                    else:
                        # Don't retry non-timeout errors
                        raise

        # All retries exhausted
        raise last_error

    async def _do_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Execute a single request to the API (internal method)."""
        url = f"{self._base_url}{endpoint}"
        start_time = time.time()

        # Log connection pool status if available
        if hasattr(self._session.connector, '_conns'):
            conn_info = f"Pool: {len(self._session.connector._conns)} conns"
        else:
            conn_info = "Pool: unknown"

        _LOGGER.debug(
            "API request starting: %s %s (timeout: %ss, %s)",
            method, endpoint, timeout, conn_info
        )

        try:
            async with asyncio.timeout(timeout):
                connect_start = time.time()

                if method == "GET":
                    async with self._session.get(url) as response:
                        connect_time = time.time() - connect_start
                        read_start = time.time()
                        response.raise_for_status()
                        result = await response.json()
                        read_time = time.time() - read_start
                        total_time = time.time() - start_time

                        _LOGGER.debug(
                            "API request completed: %s %s (connect: %.3fs, read: %.3fs, total: %.3fs)",
                            method, endpoint, connect_time, read_time, total_time
                        )
                        return result

                elif method == "POST":
                    async with self._session.post(url, json=data) as response:
                        connect_time = time.time() - connect_start
                        read_start = time.time()
                        response.raise_for_status()
                        result = await response.json()
                        read_time = time.time() - read_start
                        total_time = time.time() - start_time

                        _LOGGER.debug(
                            "API request completed: %s %s (connect: %.3fs, read: %.3fs, total: %.3fs)",
                            method, endpoint, connect_time, read_time, total_time
                        )
                        return result

                elif method == "DELETE":
                    async with self._session.delete(url) as response:
                        connect_time = time.time() - connect_start
                        read_start = time.time()
                        response.raise_for_status()
                        result = await response.json()
                        read_time = time.time() - read_start
                        total_time = time.time() - start_time

                        _LOGGER.debug(
                            "API request completed: %s %s (connect: %.3fs, read: %.3fs, total: %.3fs)",
                            method, endpoint, connect_time, read_time, total_time
                        )
                        return result

        except asyncio.TimeoutError as err:
            elapsed = time.time() - start_time
            _LOGGER.error(
                "Timeout after %.3fs connecting to %s (timeout setting: %ss, %s)",
                elapsed, url, timeout, conn_info
            )
            raise ApiClientError(f"Timeout connecting to {url}") from err
        except (aiohttp.ContentTypeError, json.JSONDecodeError) as err:
            elapsed = time.time() - start_time
            _LOGGER.error(
                "Invalid JSON response from %s after %.3fs: %s",
                url, elapsed, err
            )
            raise ApiClientError(f"Invalid JSON response from {url}") from err
        except ClientError as err:
            elapsed = time.time() - start_time
            _LOGGER.error(
                "Error communicating with %s after %.3fs: %s (type: %s, %s)",
                url, elapsed, err, type(err).__name__, conn_info
            )
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

    async def move_all_streams(self, sink_name: str) -> dict[str, Any]:
        """Move all active streams to a specific sink (follow me)."""
        return await self._request(
            "POST",
            "/api/audio/move-all",
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

        # Try combined-sink endpoint first
        try:
            return await self._request("DELETE", f"/api/audio/combined-sink/{encoded_name}")
        except ApiClientError:
            # If that fails, try stereo-pair endpoint
            try:
                return await self._request("DELETE", f"/api/audio/stereo-pair/{encoded_name}")
            except ApiClientError as err:
                # If both fail, raise the error
                raise ApiClientError(f"Failed to delete '{sink_name}' as combined sink or stereo pair") from err

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

    async def play_sink(self, sink_name: str) -> dict[str, Any]:
        """Start or resume playback on a specific sink."""
        encoded_name = quote(sink_name, safe="")
        return await self._request("POST", f"/api/playback/sink/{encoded_name}/play")

    async def pause_sink(self, sink_name: str) -> dict[str, Any]:
        """Pause playback on a specific sink."""
        encoded_name = quote(sink_name, safe="")
        return await self._request("POST", f"/api/playback/sink/{encoded_name}/pause")

    async def stop_sink(self, sink_name: str) -> dict[str, Any]:
        """Stop playback on a specific sink."""
        encoded_name = quote(sink_name, safe="")
        return await self._request("POST", f"/api/playback/sink/{encoded_name}/stop")

    async def next_track_sink(self, sink_name: str) -> dict[str, Any]:
        """Skip to next track on a specific sink."""
        encoded_name = quote(sink_name, safe="")
        return await self._request("POST", f"/api/playback/sink/{encoded_name}/next")

    async def previous_track_sink(self, sink_name: str) -> dict[str, Any]:
        """Go back to previous track on a specific sink."""
        encoded_name = quote(sink_name, safe="")
        return await self._request("POST", f"/api/playback/sink/{encoded_name}/previous")

    async def pause_all(self) -> dict[str, Any]:
        """Pause all Mopidy players."""
        return await self._request("POST", "/api/playback/pause-all")

    async def stop_all(self) -> dict[str, Any]:
        """Stop all Mopidy players."""
        return await self._request("POST", "/api/playback/stop-all")

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

    async def update_radio_stream(self, name: str, url: str) -> dict[str, Any]:
        """Update a radio stream URL."""
        encoded_name = quote(name, safe="")
        return await self._request("PUT", f"/api/radio/stream/{encoded_name}", {"url": url})

    async def play_radio_stream(self, name: str, sink: str | None = None) -> dict[str, Any]:
        """Play a predefined radio stream."""
        data = {"stream": name}
        if sink:
            data["sink"] = sink
        return await self._request("POST", "/api/radio/play", data)

    async def play_radio_url(self, url: str, sink: str | None = None) -> dict[str, Any]:
        """Play arbitrary radio URL."""
        data = {"url": url}
        if sink:
            data["sink"] = sink
        return await self._request("POST", "/api/radio/play_url", data)

    async def scan_bluetooth(self, duration: int = 10) -> dict[str, Any]:
        """Scan for Bluetooth devices."""
        return await self._request("POST", "/api/bluetooth/scan", {"duration": duration})

    async def pair_bluetooth(self, address: str) -> dict[str, Any]:
        """Pair with a Bluetooth device."""
        return await self._request("POST", "/api/bluetooth/pair", {"address": address}, timeout=BLUETOOTH_TIMEOUT)

    async def connect_bluetooth(self, address: str) -> dict[str, Any]:
        """Connect to a Bluetooth device."""
        return await self._request("POST", "/api/bluetooth/connect", {"address": address}, timeout=BLUETOOTH_TIMEOUT)

    async def disconnect_bluetooth(self, address: str) -> dict[str, Any]:
        """Disconnect from a Bluetooth device."""
        return await self._request("POST", "/api/bluetooth/disconnect", {"address": address})

    async def connect_and_set_default_bluetooth(self, address: str) -> dict[str, Any]:
        """Connect to Bluetooth device and set as default output."""
        return await self._request("POST", "/api/bluetooth/connect-and-set-default", {"address": address}, timeout=BLUETOOTH_TIMEOUT)

    # TTS endpoints
    async def speak_tts(self, message: str, language: str = "en", sinks: list[str] | None = None) -> dict[str, Any]:
        """Speak text using text-to-speech."""
        data = {"message": message, "language": language}
        if sinks:
            data["sinks"] = sinks
        return await self._request("POST", "/api/tts/speak", data)

    async def get_tts_settings(self) -> dict[str, Any]:
        """Get TTS default speaker settings."""
        return await self._request("GET", "/api/tts/settings")

    async def set_tts_settings(self, default_sinks: list[str]) -> dict[str, Any]:
        """Set TTS default speaker settings."""
        return await self._request("POST", "/api/tts/settings", {"default_sinks": default_sinks})

    # Bluetooth Keep-Alive endpoints
    async def start_keep_alive(self) -> dict[str, Any]:
        """Start Bluetooth keep-alive to prevent auto-disconnect."""
        return await self._request("POST", "/api/bluetooth/keep-alive/start")

    async def stop_keep_alive(self) -> dict[str, Any]:
        """Stop Bluetooth keep-alive."""
        return await self._request("POST", "/api/bluetooth/keep-alive/stop")

    async def get_keep_alive_status(self) -> dict[str, Any]:
        """Get keep-alive status."""
        return await self._request("GET", "/api/bluetooth/keep-alive/status")

    async def set_keep_alive_interval(self, interval: int) -> dict[str, Any]:
        """Set keep-alive interval in seconds (30-600)."""
        return await self._request("POST", "/api/bluetooth/keep-alive/interval", {"interval": interval})

    async def enable_keep_alive_for_sink(self, sink_name: str) -> dict[str, Any]:
        """Enable keep-alive for a specific sink."""
        return await self._request("POST", "/api/bluetooth/keep-alive/sink", {"sink_name": sink_name})

    async def disable_keep_alive_for_sink(self, sink_name: str) -> dict[str, Any]:
        """Disable keep-alive for a specific sink."""
        return await self._request("DELETE", "/api/bluetooth/keep-alive/sink", {"sink_name": sink_name})

    # Multi-Player Management endpoints
    async def get_players(self) -> dict[str, Any]:
        """Get status of all Mopidy player instances (player1-4)."""
        return await self._request("GET", "/api/players")

    async def get_player_assignments(self) -> dict[str, Any]:
        """Get current player-to-sink assignments."""
        return await self._request("GET", "/api/players/assignments")

    async def assign_player(self, player_name: str, sink_name: str) -> dict[str, Any]:
        """Assign a specific player to a sink."""
        return await self._request("POST", "/api/players/assign", {"player": player_name, "sink": sink_name})

    async def connect_websocket(self, on_message_callback):
        """Connect to WebSocket event stream for real-time updates."""
        ws_url = f"ws://{self._host}:{self._port}/api/events/ws"
        _LOGGER.info(f"Connecting to WebSocket: {ws_url}")

        try:
            # Set generous timeout for WebSocket connection (60s total, 30s for socket connect)
            timeout = aiohttp.ClientTimeout(total=60, sock_connect=30, sock_read=None)
            _LOGGER.debug(f"WebSocket timeout config: {timeout}")

            async with self._session.ws_connect(
                ws_url,
                timeout=timeout,
                heartbeat=30  # Send ping every 30s to keep connection alive
            ) as ws:
                _LOGGER.info("WebSocket connected successfully")

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            await on_message_callback(data)
                        except json.JSONDecodeError as e:
                            _LOGGER.error(f"Failed to parse WebSocket message: {e}")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        _LOGGER.error(f"WebSocket error: {ws.exception()}")
                        break
                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                        _LOGGER.warning("WebSocket connection closed")
                        break

        except aiohttp.ClientError as e:
            _LOGGER.error(f"WebSocket connection error: {e}")
            raise ApiClientError(f"WebSocket connection failed: {e}") from e


class ApiClientError(Exception):
    """Exception raised for API client errors."""
