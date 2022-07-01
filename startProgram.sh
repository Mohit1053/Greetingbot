#! bin/sh/
#sudo su ecelab
#raspi-gpio set 4 op
#raspi-gpio set 4 dh
cd Documents/greetingBotVoiceSystem
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS="/home/ecelab/Documents/greetingBotVoiceSystem/speechToTextGoogleApiKey.json"
flask run &
sleep 2
chromium-browser http://127.0.0.1:5000/tv &
#raspi-gpio set 4 dl
