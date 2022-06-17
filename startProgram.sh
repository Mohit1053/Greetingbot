#! bin/sh/
#sudo su ecelab
#raspi-gpio set 4 op
#raspi-gpio set 4 dh
cd Documents/greetingBotVoiceSystem
source venv/bin/activate
export GOOGLE_APPLICATION_CREDENTIALS="/home/yash/Documents/greetingBotVoiceSystem/speechToTextGoogleApiKey.json"
flask run
#raspi-gpio set 4 dl
