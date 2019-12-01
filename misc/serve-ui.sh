#!/bin/bash
export DISPLAY=:0.0
cd "`dirname $0`/.."
unclutter -idle 0 &
npm run serve ui/dist &
sleep 2
#sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/'Local State'
#sed -i 's/"exited_cleanly":false/"exited_cleanly":true/; s/"exit_type":"[^"]\+"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences
#chromium-browser --disable-infobars --kiosk 'http://localhost:5000'
cd ui
npm run app
