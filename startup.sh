#! /bin/sh
cd Documents/gitRepo/greetingBotVoiceSystem/
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS="/home/pi/Documents/gitRepo/greetingBotVoiceSystem/speechToTextGoogleApiKey.json"
python voiceRecognize.py
