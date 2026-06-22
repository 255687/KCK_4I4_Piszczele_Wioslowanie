import threading
import queue
import pythoncom
import win32com.client


class VoiceAssistant:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()

    def _tts_worker(self):
        pythoncom.CoInitialize()
        speaker = win32com.client.Dispatch("SAPI.SpVoice")

        while True:
            text = self.audio_queue.get()
            if text is None:
                break

            speaker.Speak(text)
            self.audio_queue.task_done()

    def powiedz(self, tekst):
        self.audio_queue.put(tekst)