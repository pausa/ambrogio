import snowboydecoder
import pyttsx3

engine = pyttsx3.init()

def detected_callback():
    print ("dica")
    engine.say("dica")
    engine.runAndWait()

detector = snowboydecoder.HotwordDetector("resources/ambrogio.pmdl", sensitivity=0.44, audio_gain=50)
print ("starting detector")
detector.start(detected_callback)
