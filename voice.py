import pyttsx3
import threading
import queue

class VoiceAssistant:
    def __init__(self):
        self.audio_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()

    def _tts_worker(self):
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        while True:
            text = self.audio_queue.get()
            if text is None: break
            engine.say(text)
            engine.runAndWait()
            self.audio_queue.task_done()

    def powiedz(self, tekst):
        self.audio_queue.put(tekst)