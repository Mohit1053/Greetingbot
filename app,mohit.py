
from pyexpat import model
import time
import webbrowser
from threading import Timer
from flask import Flask, render_template
from flask_socketio import SocketIO
#importing translator library
from googletrans import Translator
import speech_recognition as sr
import pyaudio
from pocketsphinx import *
import pvporcupine
import threading
import RPi.GPIO as GPIO
translator = Translator()  #initiliazing translator
wake = True
inHindi = False
GPIO.setmode(GPIO.BCM)
GPIO.setup(4,GPIO.OUT)
#GPIO.setup(27, GPIO.OUT)
"""IMPORTS FOR GOOGLE API"""
from six.moves import queue

from google.cloud import speech
RATE = 32000
CHUNK = 200  # 100ms
"""==============================="""
import struct

from six.moves import queue
# azure imports-------------------------------------------------------------------
# from azure.core.credentials import AzureKeyCredential

def _get_server_api(server_api_version):
    try:
        server_api = ServerApi(server_api_version)
    except ValueError:
        raise ConnectionError(
            "Unsupported server_api_version: {}".format(server_api_version))
    return server_api

# from azure.ai.language.questionanswering import QuestionAnsweringClient

endpoint = "https://voicenlp.cognitiveservices.azure.com/"
credential = AzureKeyCredential("d50a821ee99141a9a841efffeeae28dc")
knowledge_base_project = "questionDataBase"
deployment = "production"

import os
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer

import time
time.clock = time.time # type: ignore
def answer(question):


    # ---------------------------------------------------------------------------------------------------------------
    # mongo db initialization
    from pymongo import MongoClient
    import pymongo
    client = MongoClient(
    "mongodb+srv://ecelab:GreetingBot101@cluster0.dcma0.mongodb.net/QueryLog?retryWrites=true&w=majority")
    queryList = client['QueryLog']
    queriesCollection = queryList["queriesPostMount"]
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
    keyword_paths=['/home/ecelab/Documents/greetingBotVoiceSystem/Mister-Diode_en_raspberry-pi_v2_1_0.ppn','/home/ecelab/Documents/greetingBotVoiceSystem/Mister-Circuit_en_raspberry-pi_v2_1_0.ppn' ],
    keywords=['bumblebee']
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
            chunk = self._buff.get(timeout = 5)
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False,timeout = 5)
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


def speakGoogleText(text, speakHindi):
    #  recognize the text language and program accordingly.
    if speakHindi:
        text_to_translate = translator.translate(text,src= 'en',dest= 'hi')
        text = text_to_translate.text
    socketio.emit('command', text)
    client = texttospeech.TextToSpeechClient()
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, select the language code ("en-US") and the ssml
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="hi-IN", ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )

    # Perform the text-to-speech request on the text input with the selected
    # voice parameters and audio file type
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open("output.wav", "wb") as out:
        # Write the response to the output file.
        out.write(response.audio_content)
        print('Audio content written to file "output.wav"')
    os.system("aplay output.wav")
    os.system('rm output.wav')



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
    #if in hindi, convert to english and then send to azure
    #use translator.detect
    print(f"============================Question by user: {userQuestion}==================")
    if text == "":
        print("Text is None")
        return
    if text.isspace():
        return
    lang  = translator.detect(userQuestion)
    speakHindi = False
    if(lang.lang == 'hi'):
        speakHindi = True
        englishText = translator.translate(userQuestion, source = 'hi', dest = 'en')
        userQuestion = englishText.text
    """Generates response from the given user question and outputs the speech converted"""
    # client = QuestionAnsweringClient(endpoint, credential)
    # with client:
    question = userQuestion
    chatbot = ChatBot('CyFuse')

    trainer = ChatterBotCorpusTrainer(chatbot)

    trainer.train("chatterbot.corpus.english")

    trainer.train("chatterbot.corpus.english.greetings")

    trainer.train("chatterbot.corpus.english.conversations")

    trainer.train("chatterbot.corpus.english.ai")

    while True:
        with open("Greeting Bot ECE labs - Sheet1.txt", "r") as f:
            for line in f:
                trainer.train(line.split("!@#$%^&*()"))

        question = input("What is your question? ")
        output = str(chatbot.get_response(question))
        print(output)

        ans = input("\nDid I answer correctly? : ")
        if ans.capitalize() == "Yes":
            trainer.train([question, output])
            # store the question-answer pair in a file
            with open("question-answer.txt", "a") as f:
                f.write(question + "!@#$%^&*()" + output + "\n")
            
        else:
            print("\nSorry")

        answer = input("\nCan I help you with anything else? : ")
        if answer.lower() == "no":
            break



    print("Q: {}".format(question))
    print("A: {}".format(output))
    # print("Confidence Score: {}".format(output.confidence))

    # if (output.answers[0].confidence < 0.37):
    #    query = {
    #        "Question": question,
    #        "Answer": output.answers[0].answer
    #    }
    #    queriesCollection.insert_one(query)
    #    speakGoogleText(notUnderstood, speakHindi)
    # else:
    #    speakGoogleText(output.answers[0].answer, speakHindi)
    speakGoogleText(output, speakHindi)

def return_transcribed_word(responses):
    if responses == None:
        return ""
    """returns the transcribed text from speech in String"""
    num_chars_printed = 0
    for response in responses:
        if(response ==None):
            continue
        print("======IN RESPONSE=============")
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
        if(transcript == None):
            return transcript
        global isListening
        isListening = True
        socketio.emit('command', transcript)
        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = " " * (num_chars_printed - len(transcript))
        print(transcript)
        
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


def takeCommand(langHindi):
    """"takes the command and generates speech from the command generated"""
    if(langHindi == False):
        language_code = "en-IN"  # a BCP-47 language tag
    else:
        language_code = "hi-IN"  # a BCP-47 language tag
    
    # project_id = 'qna-bot-343107'
    # location = 'global'
    
    # adaptation_client = speech.AdaptationClient()
    # parent = f"projects/{project_id}/locations/{location}"
    # adaptation_client.create_custom_class(
    #     {
    #         "parent": parent,
    #         "custom_class_id": custom_class_id,
    #         "custom_class": {
    #             "items": [
    #                 {"value": "sushido"},
    #                 {"value": "altura"},
    #                 {"value": "taneda"},
    #             ]
    #         },
    #     }
    # )
    # custom_class_name = (
    #     f"projects/{project_id}/locations/{location}/customClasses/{custom_class_id}"
    # )
    # phrase_set_response = adaptation_client.create_phrase_set(
    #     {
    #         "parent": parent,
    #         "phrase_set_id": phrase_set_id,
    #         "phrase_set": {
    #             "boost": 10,
    #             "phrases": [
    #                 {"value": f"Visit restaurants like ${{{custom_class_name}}}"}
    #             ],
    #         },
    #     }
    # )
    # phrase_set_name = phrase_set_response.name
    # speech_adaptation = speech.SpeechAdaptation(phrase_set_references=[phrase_set_name])
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
        use_senhanced = True,
        model = 'latest_short',
        speech_contexts = [{'phrases':["shannon"], 'boost':18}, {'phrases':["channel"], 'boost':4}],
        profanity_filter = True
        # speech.SpeechContext(phrases=["ece", "shannon", "lab", "labs", "RF"])
        
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True, single_utterance = True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )
        try:
            responses = client.streaming_recognize(streaming_config, requests)
        except:
            print("Request timeout")
            responses = None
        #TODO Check the streaming_recongize library to terminate the listening when no sound
        print("------============RESPONSES GENERATED============================")
        # Now, put the transcription responses to use.
        return return_transcribed_word(responses)

def listenHotword():
    pa=pyaudio.PyAudio()
    r = sr.Recognizer()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        # input_device_index=1,
        frames_per_buffer=porcupine.frame_length)
    global inHindi
    while True:
        pcm = audio_stream.read(porcupine.frame_length)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        keyword_index = porcupine.process(pcm)
        #0 for diode, 1 for circuit
        if keyword_index == 0:
            print("English Hotword Detected")
            inHindi = False
            audio_stream.close()
            pa.terminate()
            return True

        if keyword_index == 1:
            print("Hindi Hotword Detected")
            
            inHindi = True
            audio_stream.close()
            pa.terminate()
            return True
            


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



# wakeMotion=threading.Thread(target=detectMotion)
# print("program initiated..............")
# GPIO.output(4,GPIO.LOW)
# while(True):
#    # GPIO.output(27,GPIO.HIGH)
#     if listenHotword():
#         GPIO.output(4,GPIO.HIGH)
#         takeCommand()
#         GPIO.output(4,GPIO.LOW)
#two threads were used for using the hotword and the pir sensor
# wakeMotion.start()




app = Flask(__name__)
app.config['SECRET_KEY'] = "secret"
socketio = SocketIO(app)
#@app.route('/screen')
#def showScreen():
#    return render_template('index.html')

@app.route('/screen')
def showTvScreen():
    th =threading.Thread(target = startRecognition, args=())
    th.start()
    return render_template('index.html')

text = ""
@socketio.on('connect')
def onConnect():
    print("program initiated..............")
    GPIO.output(4,GPIO.LOW)
    socketio.send('start')



def startRecognition():
    counterFile = open('counter.txt', 'r')
    counter = counterFile.read()
    counter = int(counter)
    print(f"==============counter: {counter}==================")
    counterFile.close()    
    print("=======starting the loop===========")
    time.sleep(2)
    socketio.emit('counterUpdate', counter)
    testActive = True
    while(True):
    # GPIO.output(27,GPIO.HIGH)
        if listenHotword():
            testActive = False
            socketio.emit('command', 'Speak Now')
            socketio.emit('ImageBox','../static/listening_mode.png')

            GPIO.output(4,GPIO.HIGH)
            global text
            
        
            print(f"The language is hindi: {inHindi}")
            text = takeCommand(inHindi)
            
                # text = ""

            # for Images generate a function here

            generateResponse(text)
            counterFile = open('counter.txt', 'w')
            counter+=1
            counterFile.write(str(counter))
            counterFile.close()
            socketio.emit('command', """<p style= "text-align: center"> Hi! You can ask me any question related to ECE Labs <br> Try Saying <i> "Mr. Diode, Who are you"</i> </p><br><br>
        <b>Instructions to use:</b><br>
               &emsp;&emsp;1) Please say “Mr. Diode (Mr. Circuit to talk in Hindi)”.<br>
               &emsp;&emsp;2)LED will glow in red color.<br>
               &emsp;&emsp;3)Please ask your question related to ECE Labs.<br>
               &emsp;&emsp;4)Once the question is answered the LED will turn off. <br>
               &emsp;&emsp;5)Repeat from step 1 for subsequent query. <br>
               <br><br><br><br>""")
            socketio.emit('counterUpdate', counter)
            GPIO.output(4,GPIO.LOW)
            socketio.emit('ImageBox','../static/botFace.png')
            # GPIO.output(4,GPIO.LOW)
    


if __name__ == '__main__':
    # Timer(3, open_browser).start()
    socketio.run(app)
