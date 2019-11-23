#!/bin/bash
cd "`dirname $0`/../assist"
. env/bin/activate

export PA_ALSA_PLUGHW=1
python main.py
