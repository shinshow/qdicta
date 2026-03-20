"""Tests for recorder module."""

import unittest
from unittest.mock import MagicMock, patch

import numpy as np

from vvrite.recorder import Recorder


class TestRecorder(unittest.TestCase):
    def test_start_uses_device_default_samplerate(self):
        preferred_device = MagicMock(index=7, default_samplerate=48000)
        stream = MagicMock()

        with (
            patch("vvrite.recorder.get_preferred_input_device", return_value=preferred_device),
            patch("vvrite.recorder.sd.InputStream", return_value=stream) as input_stream,
        ):
            recorder = Recorder()
            recorder.start(device="Core Audio::USB Mic")

        input_stream.assert_called_once_with(
            samplerate=48000,
            channels=1,
            dtype="int16",
            device=7,
            callback=recorder._callback,
        )
        stream.start.assert_called_once()

    def test_start_raises_when_no_usable_device_exists(self):
        with patch("vvrite.recorder.get_preferred_input_device", return_value=None):
            recorder = Recorder()
            with self.assertRaisesRegex(RuntimeError, "No usable microphone input device found"):
                recorder.start(device="missing")

    def test_start_refreshes_device_list_and_falls_back_after_unavailable_device(self):
        stale_device = MagicMock(index=7, default_samplerate=48000)
        default_device = MagicMock(index=5, default_samplerate=44100)
        stream = MagicMock()

        with (
            patch(
                "vvrite.recorder.get_preferred_input_device",
                side_effect=[stale_device, default_device],
            ),
            patch("vvrite.recorder.refresh_portaudio_device_list") as refresh_mock,
            patch(
                "vvrite.recorder.sd.InputStream",
                side_effect=[Exception("device unavailable"), stream],
            ) as input_stream,
        ):
            recorder = Recorder()
            recorder.start(device="Core Audio::USB Mic")

        refresh_mock.assert_called_once_with()
        self.assertEqual(input_stream.call_count, 2)
        _, second_kwargs = input_stream.call_args_list[1]
        self.assertEqual(second_kwargs["samplerate"], 44100)
        self.assertEqual(second_kwargs["device"], 5)
        stream.start.assert_called_once()

    def test_stop_writes_audio_with_actual_stream_samplerate(self):
        recorder = Recorder()
        recorder._frames = [np.array([[1], [2], [3]], dtype=np.int16)]
        recorder._stream_samplerate = 48000

        with (
            patch("vvrite.recorder.tempfile.mkstemp", return_value=(10, "/tmp/test.wav")),
            patch("vvrite.recorder.os.close"),
            patch("vvrite.recorder.sf.write") as write_mock,
        ):
            path = recorder.stop()

        self.assertEqual(path, "/tmp/test.wav")
        write_mock.assert_called_once()
        args = write_mock.call_args[0]
        self.assertEqual(args[0], "/tmp/test.wav")
        self.assertEqual(args[2], 48000)
        self.assertEqual(write_mock.call_args.kwargs["subtype"], "PCM_16")


if __name__ == "__main__":
    unittest.main()
