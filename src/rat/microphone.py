from . import fs
from .debug import message as debug_message

def record_microphone(path, seconds: int = 1) -> None:
    """ Records microphone. """

    try:
        import pyaudio  # pylint: disable=import-outside-toplevel
        import wave  # pylint: disable=import-outside-toplevel
    except ImportError:
        debug_message("[Microphone] Recording microphone is not supported on selected PC! "
                      "(opencv-python (CV2) module is not installed)")
        return

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, frames_per_buffer=1024, input=True)
    frames = []

    for _ in range(0, int(44100 / 1024 * int(seconds))):
        data = stream.read(1024)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    fs.build_path(path)
    file = wave.open(path, 'wb')
    file.setnchannels(1)
    file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
    file.setframerate(44100)
    file.writeframes(b''.join(frames))
    file.close()
