#!/bin/bash
cd "`dirname $0`/../assist"
. env/bin/activate

export GOOGLE_APPLICATION_CREDENTIALS=private/token.json
export PA_ALSA_PLUGHW=1
python main.py
