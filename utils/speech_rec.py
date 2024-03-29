# SPEECH RECOGNITION
"""
- install speech recognition library from https://pypi.python.org/pypi/SpeechRecognition/
- install pyaudio via instructions on webpage above
- install "flac" if do not have

pip install SpeechRecognition
brew install portaudio
pip install pyaudio
brew install flac

"""


import speech_recognition as sr
import parser

def recognize_command():
    # obtain audio from the microphone
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say command like '5 inches to the left of the car'!")
        audio = r.listen(source, timeout = 5)

    # recognize speech using Google Speech Recognition
    try:
        # for testing purposes, we're just using the default API key
        # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
        # instead of `r.recognize_google(audio)`
        command = r.recognize_google(audio)
        print("Google Speech Recognition thinks you said " + command)

        # HERE WE PARSE COMMAND
        p = parser.parse(command)
        print p
        return p # FOR USE IN ALGORITHM
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))

if __name__ == '__main__':
    recognize_command()
