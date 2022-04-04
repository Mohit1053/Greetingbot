
import re
import pyttsx3
import speech_recognition as sr
import pyaudio
from pocketsphinx import *
import pvporcupine
import threading
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(4,GPIO.OUT)
"""IMPORTS FOR GOOGLE API"""
from six.moves import queue

from google.cloud import speech
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms
"""==============================="""
import struct

from six.moves import queue
# azure imports-------------------------------------------------------------------
from azure.core.credentials import AzureKeyCredential

from pymongo.server_api import ServerApi

from azure.ai.language.questionanswering import QuestionAnsweringClient

endpoint = "https://voicenlp.cognitiveservices.azure.com/"
credential = AzureKeyCredential("d50a821ee99141a9a841efffeeae28dc")
knowledge_base_project = "questionDataBase"
deployment = "production"

# ---------------------------------------------------------------------------------------------------------------

# mongo db initialization
from pymongo import MongoClient
import pymongo
pa=pyaudio.PyAudio()

client = MongoClient(
   "mongodb+srv://ecelab:GreetingBot101@cluster0.dcma0.mongodb.net/QueryLog?retryWrites=true&w=majority")
queryList = client['QueryLog']
queriesCollection = queryList["queries"]
# query = {
#            "Question": "start Test",
#            "Answer": "working"
#        }
# queriesCollection.insert_one(query)
# -----------------------------------------------------------------------------------------------------------------

# from gpiozero import MotionSensor
#  from picotts import PicoTTS
# pir= MotionSensor(4)

notUnderstood = "I am not sure if I understood that correctly"
porcupine = pvporcupine.create(
    access_key="zUOJpu87sR4uSIQj/fH9XFzHz1rla68/m642B3GygFDN36cB6fYvdA==",
    keywords=['picovoice', 'bumblebee']
)


"""USING GOOGLE SPEECH TO TEXT
---------------------THE CODE START FROM HERE------------------------"""
class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


"""================================================================================================================"""
"""   USING GOOGLE TEXT TO SPEECH CONVERSION"""
from google.cloud import texttospeech

# Instantiates a client
client = texttospeech.TextToSpeechClient()

def speakGoogleText(text):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-IN", ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open("output.mp3", "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')
    os.system("mpg123 output.mp3")




"""====================================================================================================================="""

def speakText(text):
    # # for windows
    # engine = pyttsx3.init("espeak")
    # engine.setProperty("rate", 175)
    # engine.say(text)
    # engine.runAndWait()
    # print(text)

    #for rpi
    cmd='pico2wave -l en-US -w hello.wav "'+ text+'"'
    os.system(cmd)
    os.system("aplay hello.wav")


def generateResponse(userQuestion):
    """Generates response from the given user question and outputs the speech converted"""
    client = QuestionAnsweringClient(endpoint, credential)
    with client:
        question = userQuestion
        output = client.get_answers(
            # confidence_threshold=0.4,
            question=question,
            project_name=knowledge_base_project,
            deployment_name=deployment
        )
    print("Q: {}".format(question))
    print("A: {}".format(output.answers[0].answer))
    print("Confidence Score: {}".format(output.answers[0].confidence))

    if (output.answers[0].confidence < 0.37):
       query = {
           "Question": question,
           "Answer": output.answers[0].answer
       }
       queriesCollection.insert_one(query)
       speakGoogleText(notUnderstood)
    else:
        speakGoogleText(output.answers[0].answer)


# def askingCapacity(textArray):
#     question="what is the seating capacity of"
#     question=question.split(" ")
#     askedQuestion=textArray[0:6]
#     if askedQuestion==question :
#         #capacity question Detected
#         var=textArray[6:]
#         if var == ["shannon" ,"lab"]:
#             #asking about shanon labs
#             speakText("The sitting capacity of Shannon lab is 46")
#             return True
#         elif var == ["labs"]:
#             #total labs
#             speakText("On average, all the labs can accommodate at least 45 students in each lab. However, you may ask an individual lab sitting space")
#             return True
#         elif var == ["circuits", "and" ,"innovation", "lab"]:
#             speakText("The sitting capacity of Circuit and Innovation lab is 50")
#             return True
#         elif var == ["basic", "electronics", "lab"]:
#             speakText("The sitting capacity of Basic Electronic lab is 50")
#             return True
#         elif var == ["rf","and","applied","electromagnetics","lab"]:
#             speakText("The sitting capacity of RF and Applied Electromagnetics lab is 40")
#             return True
#         else:
#             speakText(notUnderstood)
#             return False
# def askingCourses(textArray):
#     question="what all courses are conducted in"
#     question=question.split(" ")
#     askedQuestion=textArray[0:6]
#     if askedQuestion==question :
#         #capacity question Detected
#         var=textArray[6:]
#         if var == ["shannon" ,"lab"]:
#             #asking about shanon labs
#             speakText("All the Basic and Advanced digital and optical communication courses like Wireless System Implementation, Digital Hardware Design, Digital Communication System, Wireless communication, Embedded logic design, Advanced Embedded logic design, Optical communication system, etc. The lab is also accessed by Interns/RAs and PhDs for their research work.")
#             return True
#         elif var == ["lab"] or var == ["ece","lab"]:
#             #total labs
#             speakText("Please rephrase your statement with the individual lab name.")
#             return True
#         elif var == ["circuits", "and" ,"innovation", "lab"]:
#             speakText("Courses like Circuit Theory and Devices, Digital Circuits, Basic Electronics, Introduction to Engineering Design, integrated electronics, Advanced Embedded logic design, etc.")
#             return True
#         elif var == ["basic", "electronics", "lab"]:
#             speakText("Course like Circuit Theory and Devices, Digital Circuits, Basic Electronics, Introduction to Engineering Design, integrated electronics, Advanced Embedded logic design, etc.")
#             return True
#         elif var == ["rf","and","applied","electromagnetics","lab"]:
#             speakText("All the Basic and Advanced RF test and measurement courses like RF Circuit Design, Antenna Theory and Design, Radar Systems, Wireless System Implementation, Advanced Embedded logic design, etc. The lab is also accessed by Interns/RAs and PhDs for their research work.")
#             return True
#         else:
#             speakText(notUnderstood)
#             return False
# def commonCheck(textArray):
#     #check for sitting capacity
#     if(askingCapacity(textArray)):
#         return True;
#     elif(askingCourses(textArray)):
#         return True;
#     else:
#         return False;
#
# def takeCommand(r,audio_stream):
#     with sr.Microphone() as source:
#             print("speak now")
#             audio_text = r.listen(source,timeout=7,phrase_time_limit=7)
#     print("timeout complete")
#     try:
#         text=r.recognize_google(audio_text,language="en-IN")
#         text=text.lower()
#         print(text)
#         textArray= text.split(" ")
#         generateResponse(textArray)
#     except:
#         print("Error")

def return_transcribed_word(responses):
    """returns the transcribed text from speech in String"""
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            # sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            num_chars_printed = len(transcript)

        else:
            return transcript + overwrite_chars
            break

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                break

            num_chars_printed = 0


def takeCommand():
    """"takes the command and generates speech from the command generated"""
    language_code = "en-IN"  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        generateResponse(return_transcribed_word(responses))


def listenHotword():
    r = sr.Recognizer()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length)
    while True:
        pcm = audio_stream.read(porcupine.frame_length)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("Hotword Detected")
            GPIO.output(4,GPIO.HIGH)
            takeCommand()
            GPIO.output(4,GPIO.LOW)


# def detectMotion():
#     r=sr.Recognizer()
#     audio_stream = pa.open(
#                 rate=porcupine.sample_rate,
#                 channels=1,
#                 format=pyaudio.paInt16,
#                 input=True,
#                 frames_per_buffer=porcupine.frame_length)
#     while True:
#         pir.wait_for_motion()
#         print("Movement detected")
#         speakText("Hello, I am ready to listen")
#         takeCommand(r,audio_stream)
#         pir.wait_for_no_motion()
#         print("motion reset")


wakeHotword = threading.Thread(target=listenHotword)
# wakeMotion=threading.Thread(target=detectMotion)
print("prgogram initiated..............")
wakeHotword.start()
# wakeMotion.start()
