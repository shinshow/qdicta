"""Tests for audio device enumeration and resolution."""

import unittest
from unittest.mock import patch

from vvrite import audio_devices


class TestAudioDevices(unittest.TestCase):
    def test_list_input_devices_filters_and_marks_default(self):
        devices = [
            {
                "name": "USB Mic",
                "hostapi": 0,
                "max_input_channels": 2,
                "default_samplerate": 48000.0,
            },
            {
                "name": "Output Only",
                "hostapi": 0,
                "max_input_channels": 0,
                "default_samplerate": 44100.0,
            },
            {
                "name": "USB Mic",
                "hostapi": 1,
                "max_input_channels": 1,
                "default_samplerate": 44100.0,
            },
            {
                "name": "Built-in Mic",
                "hostapi": 0,
                "max_input_channels": 1,
                "default_samplerate": 48000.0,
            },
        ]
        hostapis = [
            {"name": "Core Audio"},
            {"name": "Virtual Audio"},
        ]

        with (
            patch.object(audio_devices, "_query_devices", return_value=devices),
            patch.object(audio_devices, "_query_hostapis", return_value=hostapis),
            patch.object(audio_devices, "_get_default_input_index", return_value=3),
            patch.object(
                audio_devices,
                "_supports_input",
                side_effect=lambda index, device: device["max_input_channels"] > 0,
            ),
        ):
            result = audio_devices.list_input_devices()

        self.assertEqual([device.index for device in result], [0, 2, 3])
        self.assertEqual(result[0].device_id, "Core Audio::USB Mic")
        self.assertEqual(result[1].device_id, "Virtual Audio::USB Mic")
        self.assertEqual(result[0].display_name, "USB Mic (Core Audio)")
        self.assertEqual(result[1].display_name, "USB Mic (Virtual Audio)")
        self.assertEqual(result[2].display_name, "Built-in Mic [Default]")

    def test_resolve_input_device_supports_legacy_name(self):
        devices = [
            audio_devices.AudioInputDevice(
                device_id="Core Audio::USB Mic",
                name="USB Mic",
                display_name="USB Mic",
                index=2,
                hostapi_name="Core Audio",
                default_samplerate=48000,
            )
        ]

        resolved = audio_devices.resolve_input_device("USB Mic", devices)

        self.assertIsNotNone(resolved)
        self.assertEqual(resolved.device_id, "Core Audio::USB Mic")

    def test_get_preferred_input_device_falls_back_to_default_then_first(self):
        devices = [
            audio_devices.AudioInputDevice(
                device_id="Core Audio::External Mic",
                name="External Mic",
                display_name="External Mic",
                index=4,
                hostapi_name="Core Audio",
                default_samplerate=48000,
            ),
            audio_devices.AudioInputDevice(
                device_id="Core Audio::Built-in Mic",
                name="Built-in Mic",
                display_name="Built-in Mic [Default]",
                index=5,
                hostapi_name="Core Audio",
                default_samplerate=44100,
            ),
        ]

        with patch.object(audio_devices, "_get_default_input_index", return_value=5):
            preferred = audio_devices.get_preferred_input_device("missing", devices)
            self.assertEqual(preferred.device_id, "Core Audio::Built-in Mic")

        with patch.object(audio_devices, "_get_default_input_index", return_value=None):
            preferred = audio_devices.get_preferred_input_device("missing", devices[:1])
            self.assertEqual(preferred.device_id, "Core Audio::External Mic")

    def test_list_input_devices_can_refresh_portaudio_device_cache(self):
        with (
            patch.object(audio_devices, "refresh_portaudio_device_list") as refresh_mock,
            patch.object(audio_devices, "_query_devices", return_value=[]),
            patch.object(audio_devices, "_query_hostapis", return_value=[]),
            patch.object(audio_devices, "_get_default_input_index", return_value=None),
        ):
            self.assertEqual(audio_devices.list_input_devices(refresh=True), [])

        refresh_mock.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
