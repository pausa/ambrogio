import snowboydecoder
from subprocess import Popen, PIPE

def detected_callback():
    print ("dica")
    #mixer.init()
    #mixer.music.load('resources/dica.mp3')
    #mixer.music.play()
    p = Popen(["/usr/bin/mpg123", "resources/dica.mp3"], stdout=PIPE, stderr=PIPE)
    p.communicate()
    print ("fine")

detector = snowboydecoder.HotwordDetector("resources/ambrogio.pmdl", sensitivity=0.44, audio_gain=50)
print ("starting detector")
detector.start(detected_callback)
