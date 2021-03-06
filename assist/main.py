# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Sample that implements a gRPC client for the Google Assistant API."""

import concurrent.futures
import json
import logging as lf
import os
import os.path
import pathlib2 as pathlib
import sys
import time
import uuid

import click
import grpc
import google.auth.transport.grpc
import google.auth.transport.requests
import google.oauth2.credentials

from google.assistant.embedded.v1alpha2 import (
    embedded_assistant_pb2,
    embedded_assistant_pb2_grpc
)

from tenacity import retry, stop_after_attempt, retry_if_exception

import platform, importlib

#import snowboydecoder
meta="snowboydecoder"
snowboydecoder = getattr(__import__(format(platform.uname().machine), fromlist=[meta]), meta)

from google.cloud import texttospeech
import requests
import datetime as dt
import integration.darksky as dark

try:
    from googlesamples.assistant.grpc import (
        assistant_helpers,
        browser_helpers,
        device_helpers
    )
except (SystemError, ImportError):
    import assistant_helpers
    import audio_helpers
    import browser_helpers
    import device_helpers

## My patched version
import audio_helpers

ASSISTANT_API_ENDPOINT = 'embeddedassistant.googleapis.com'
END_OF_UTTERANCE = embedded_assistant_pb2.AssistResponse.END_OF_UTTERANCE
DIALOG_FOLLOW_ON = embedded_assistant_pb2.DialogStateOut.DIALOG_FOLLOW_ON
CLOSE_MICROPHONE = embedded_assistant_pb2.DialogStateOut.CLOSE_MICROPHONE
PLAYING = embedded_assistant_pb2.ScreenOutConfig.PLAYING
DEFAULT_GRPC_DEADLINE = 60 * 3 + 5

VOLUME=100

VOWELS = ['a', 'e', 'i', 'o', 'u', 'j', 'h','y']
MIDNIGHT = dt.time(hour=0)
MORNING = dt.timedelta(hours=12)
AFTERNOON = dt.timedelta(hours=17)

lf.basicConfig()
logging = lf.getLogger('assist')

class SampleAssistant(object):
    """Sample Assistant that supports conversations and device actions.

    Args:
      device_model_id: identifier of the device model.
      device_id: identifier of the registered device instance.
      conversation_stream(ConversationStream): audio stream
        for recording query and playing back assistant answer.
      channel: authorized gRPC channel for connection to the
        Google Assistant API.
      deadline_sec: gRPC deadline in seconds for Google Assistant API call.
      device_handler: callback for device actions.
    """

    def __init__(self, language_code, device_model_id, device_id,
                 conversation_stream, display,
                 channel, deadline_sec, device_handler,speak):
        self.language_code = language_code
        self.device_model_id = device_model_id
        self.device_id = device_id
        self.conversation_stream = conversation_stream
        self.display = display
        self.speak = speak
        self.last_request = None

        # Opaque blob provided in AssistResponse that,
        # when provided in a follow-up AssistRequest,
        # gives the Assistant a context marker within the current state
        # of the multi-Assist()-RPC "conversation".
        # This value, along with MicrophoneMode, supports a more natural
        # "conversation" with the Assistant.
        self.conversation_state = None
        # Force reset of first conversation.
        self.is_new_conversation = True

        # Create Google Assistant API gRPC client.
        self.assistant = embedded_assistant_pb2_grpc.EmbeddedAssistantStub(
            channel
        )
        self.deadline = deadline_sec

        self.device_handler = device_handler

    def __enter__(self):
        return self

    def __exit__(self, etype, e, traceback):
        if e:
            return False

    def is_grpc_error_unavailable(e):
        is_grpc_error = isinstance(e, grpc.RpcError)
        if is_grpc_error and (e.code() == grpc.StatusCode.UNAVAILABLE):
            logging.error('grpc unavailable error: %s', e)
            return True
        return False

    @retry(reraise=True, stop=stop_after_attempt(3),
           retry=retry_if_exception(is_grpc_error_unavailable))
    def assist(self, text_query=None):
        """Send a voice request to the Assistant and playback the response.

        Returns: True if conversation should continue.
        """
        continue_conversation = False
        device_actions_futures = []

        self.conversation_stream.start_recording()
        logging.info('Recording audio request.')

        def iter_log_assist_requests():
            for c in self.gen_assist_requests(text_query):
                assistant_helpers.log_assist_request_without_audio(c)
                yield c
            logging.debug('Reached end of AssistRequest iteration.')

        # This generator yields AssistResponse proto messages
        # received from the gRPC Google Assistant API.
        for resp in self.assistant.Assist(iter_log_assist_requests(),
                                          self.deadline):
            assistant_helpers.log_assist_response_without_audio(resp)
            if resp.event_type == END_OF_UTTERANCE:
                logging.info('End of audio request detected.')
                logging.info('Stopping recording.')
                self.conversation_stream.stop_recording()
            if resp.speech_results:
                logging.info('Transcript of user request: "%s".',
                             ' '.join(r.transcript
                                      for r in resp.speech_results))
            if len(resp.speech_results) == 1 and resp.speech_results[0].stability == 1.0:
                #logging.info('final request: {}'.format(' '.join(r.transcript for r in resp.speech_results)))
                logging.info('final request: {}'.format(resp.speech_results[0].transcript))
                self.last_request = resp.speech_results[0].transcript

            if len(resp.audio_out.audio_data) > 0 and not resp.dialog_state_out.supplemental_display_text:
                if self.last_request:
                    logging.debug('eseguito: {}'.format(self.last_request))
                    self.last_request = None
            if len(resp.audio_out.audio_data) > 0: 
                if not self.conversation_stream.playing:
                    self.conversation_stream.stop_recording()
                    self.conversation_stream.start_playback()
                    logging.info('Playing assistant response.')
                self.conversation_stream.write(resp.audio_out.audio_data)
            if resp.dialog_state_out.supplemental_display_text:
                logging.debug("additional text: {}".format(resp.dialog_state_out.supplemental_display_text))
                self.last_request = None
            if resp.dialog_state_out.conversation_state:
                conversation_state = resp.dialog_state_out.conversation_state
                logging.debug('Updating conversation state.')
                self.conversation_state = conversation_state
            if resp.dialog_state_out.volume_percentage != 0:
                volume_percentage = resp.dialog_state_out.volume_percentage
                logging.info('Setting volume to %s%%', volume_percentage)
                self.conversation_stream.volume_percentage = volume_percentage
            if resp.dialog_state_out.microphone_mode == DIALOG_FOLLOW_ON:
                continue_conversation = True
                logging.info('Expecting follow-on query from user.')
            elif resp.dialog_state_out.microphone_mode == CLOSE_MICROPHONE:
                continue_conversation = False
            if resp.device_action.device_request_json:
                device_request = json.loads(
                    resp.device_action.device_request_json
                )
                fs = self.device_handler(device_request)
                if fs:
                    device_actions_futures.extend(fs)
            if self.display and resp.screen_out.data:
                logging.info(resp.screen_out.data)

        if len(device_actions_futures):
            logging.info('Waiting for device executions to complete.')
            concurrent.futures.wait(device_actions_futures)

        logging.info('Finished playing assistant response.')
        self.conversation_stream.stop_playback()
        return continue_conversation

    def gen_assist_requests(self, text_query=None):
        """Yields: AssistRequest messages to send to the API."""

        audio_in_config=embedded_assistant_pb2.AudioInConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
            ) 
        config = embedded_assistant_pb2.AssistConfig(
            audio_in_config=audio_in_config,
            audio_out_config=embedded_assistant_pb2.AudioOutConfig(
                encoding='LINEAR16',
                sample_rate_hertz=self.conversation_stream.sample_rate,
                #volume_percentage=self.conversation_stream.volume_percentage,
                volume_percentage=0,
            ),
            dialog_state_in=embedded_assistant_pb2.DialogStateIn(
                language_code=self.language_code,
                conversation_state=self.conversation_state,
                is_new_conversation=self.is_new_conversation,
            ),
            device_config=embedded_assistant_pb2.DeviceConfig(
                device_id=self.device_id,
                device_model_id=self.device_model_id,
            ),
            text_query=text_query
        )
        if self.display:
            config.screen_out_config.screen_mode = PLAYING
        # Continue current conversation with later requests.
        self.is_new_conversation = False
        # The first AssistRequest must contain the AssistConfig
        # and no audio data.
        yield embedded_assistant_pb2.AssistRequest(config=config)
        if not text_query:
            for data in self.conversation_stream:
                # Subsequent requests need audio data, but not config.
                yield embedded_assistant_pb2.AssistRequest(audio_in=data)

class Fulfillment():
    def __init__ (self, text, publishing=None):
        self.text = text
        self.publishing = publishing
        
class EchoEffect():
    pass

@click.command()
@click.option('--api-endpoint', default=ASSISTANT_API_ENDPOINT)
@click.option('--credentials',
              default=os.path.join(click.get_app_dir('google-oauthlib-tool'),
                                   'credentials.json'))
@click.option('--project-id',
              metavar='<project id>',
              help=('Google Developer Project ID used for registration '
                    'if --device-id is not specified'))
@click.option('--device-model-id',
              metavar='<device model id>',
              help=(('Unique device model identifier, '
                     'if not specifed, it is read from --device-config')))
@click.option('--device-id',
              metavar='<device id>',
              help=(('Unique registered device instance identifier, '
                     'if not specified, it is read from --device-config, '
                     'if no device_config found: a new device is registered '
                     'using a unique id and a new device config is saved')))
@click.option('--device-config', show_default=True,
              metavar='<device config>',
              default=os.path.join(
                  click.get_app_dir('googlesamples-assistant'),
                  'device_config.json'),
              help='Path to save and restore the device configuration')
@click.option('--lang', show_default=True,
              metavar='<language code>',
              default='it-IT',
              help='Language code of the Assistant')
@click.option('--verbose', '-v', is_flag=True, default=False,
              help='Verbose logging.')
@click.option('--audio-sample-rate',
              default=audio_helpers.DEFAULT_AUDIO_SAMPLE_RATE,
              metavar='<audio sample rate>', show_default=True,
              help='Audio sample rate in hertz.')
@click.option('--audio-sample-width',
              default=audio_helpers.DEFAULT_AUDIO_SAMPLE_WIDTH,
              metavar='<audio sample width>', show_default=True,
              help='Audio sample width in bytes.')
@click.option('--audio-iter-size',
              default=audio_helpers.DEFAULT_AUDIO_ITER_SIZE,
              metavar='<audio iter size>', show_default=True,
              help='Size of each read during audio stream iteration in bytes.')
@click.option('--audio-block-size',
              default=audio_helpers.DEFAULT_AUDIO_DEVICE_BLOCK_SIZE,
              metavar='<audio block size>', show_default=True,
              help=('Block size in bytes for each audio device '
                    'read and write operation.'))
@click.option('--audio-flush-size',
              default=audio_helpers.DEFAULT_AUDIO_DEVICE_FLUSH_SIZE,
              metavar='<audio flush size>', show_default=True,
              help=('Size of silence data in bytes written '
                    'during flush operation'))
@click.option('--grpc-deadline', default=DEFAULT_GRPC_DEADLINE,
              metavar='<grpc deadline>', show_default=True,
              help='gRPC deadline in seconds')
def main(api_endpoint,
    credentials,
    project_id,
    device_model_id,
    device_id,
    device_config,
    lang,
    verbose,
    audio_sample_rate,
    audio_sample_width,
    audio_iter_size,
    audio_block_size,
    audio_flush_size,
    grpc_deadline,
    *args,
    **kwargs):
    """Samples for the Google Assistant API.

    Examples:
      Run the sample with microphone input and speaker output:

        $ python -m googlesamples.assistant

      Run the sample with file input and speaker output:

        $ python -m googlesamples.assistant -i <input file>

      Run the sample with file input and output:

        $ python -m googlesamples.assistant -i <input file> -o <output file>
    """
    # Setup logging.
    logging.setLevel(lf.DEBUG if verbose else lf.INFO)

    # Load OAuth 2.0 credentials.
    try:
        with open(credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
            http_request = google.auth.transport.requests.Request()
            credentials.refresh(http_request)
    except Exception as e:
        logging.error('Error loading credentials: %s', e)
        logging.error('Run google-oauthlib-tool to initialize '
                      'new OAuth 2.0 credentials.')
        sys.exit(-1)

    # Create an authorized gRPC channel.
    grpc_channel = google.auth.transport.grpc.secure_authorized_channel(
        credentials, http_request, api_endpoint)
    logging.info('Connecting to %s', api_endpoint)


    if not device_id or not device_model_id:
        try:
            with open(device_config) as f:
                device = json.load(f)
                device_id = device['id']
                device_model_id = device['model_id']
                logging.info("Using device model %s and device id %s",
                             device_model_id,
                             device_id)
        except Exception as e:
            logging.warning('Device config not found: %s' % e)
            logging.info('Registering device')
            if not device_model_id:
                logging.error('Option --device-model-id required '
                              'when registering a device instance.')
                sys.exit(-1)
            if not project_id:
                logging.error('Option --project-id required '
                              'when registering a device instance.')
                sys.exit(-1)
            device_base_url = (
                'https://%s/v1alpha2/projects/%s/devices' % (api_endpoint,
                                                             project_id)
            )
            device_id = str(uuid.uuid1())
            payload = {
                'id': device_id,
                'model_id': device_model_id,
                'client_type': 'SDK_SERVICE'
            }
            session = google.auth.transport.requests.AuthorizedSession(
                credentials
            )
            r = session.post(device_base_url, data=json.dumps(payload))
            if r.status_code != 200:
                logging.error('Failed to register device: %s', r.text)
                sys.exit(-1)
            logging.info('Device registered: %s', device_id)
            pathlib.Path(os.path.dirname(device_config)).mkdir(exist_ok=True)
            with open(device_config, 'w') as f:
                json.dump(payload, f)

    # Configure audio source and sink.
    audio_device = audio_helpers.SoundDeviceStream(
                sample_rate=audio_sample_rate,
                sample_width=audio_sample_width,
                block_size=audio_block_size,
                flush_size=audio_flush_size)

    # Create conversation stream with the given audio source and sink.
    conversation_stream = audio_helpers.ConversationStream(
        source=audio_device,
        sink=audio_device,
        iter_size=audio_iter_size,
        sample_width=audio_sample_width,
        volume=VOLUME
    )

    tts_client = texttospeech.TextToSpeechClient()
    tts_voice = texttospeech.types.VoiceSelectionParams(language_code='it-IT', 
            ssml_gender=texttospeech.enums.SsmlVoiceGender.MALE, 
            name="it-it-Wavenet-D")
    tts_config = texttospeech.types.AudioConfig(audio_encoding=texttospeech.enums.AudioEncoding.LINEAR16, 
            sample_rate_hertz=16000,
            pitch=-2.50,
            speaking_rate=1.0,
            effects_profile_id=['small-bluetooth-speaker-class-device'])



    device_handler = device_helpers.DeviceRequestHandler(device_id)
    fulfillments = []
    #TODO find a better way, is a bit too tangled
    echo_effect = EchoEffect()
    
    def speak(text, publishing=None):
        publisher = lambda: publish(publishing['resource'], publishing['payload']) if publishing else None
        use_echo(text, publisher)

    def use_tts(text, publisher=lambda: True):
        text=text.replace("\\n", ". ")
        text=text.replace("\\t", ". ")
        text=text.replace(" h ", " ore ")
        text=text.replace("1 ore ", "1 ora ")
        text=text.replace(" per da ", " per ")
        order = texttospeech.types.SynthesisInput(text=text)
        logging.info('saying: {}'.format(order))
        response = tts_client.synthesize_speech(order, tts_voice, tts_config)
        conversation_stream.start_playback()
        publisher()
        conversation_stream.write(response.audio_content)
        conversation_stream.stop_playback()

    def use_echo(text, publisher):
        echo_effect.action = publisher
        assistant.assist("pappagallo {}".format(text))


    @device_handler.command('ambrogio.TEST')
    def order(number):
        ful = Fulfillment('ordine: {} eseguito'.format(number))
        fulfillments.append(ful)

    def weather(place_name, place, date_name, date):
        place_name=nvl(place_name, 'Haarlem')
        def_coordinates={'latitude': 52.3873878, 'longitude': 4.6462194}
        place=nvl(place, def_coordinates, lambda x: x['coordinates'])
        date_name=nvl(date_name, 'oggi')
        date=nvl(date, None, lambda x: dt.date(**x))
        logging.info("date: {}".format(date))

        params = dict() 
        params.update(place)
        params.update({'day': date})
        wreq = dark.WeatherRequest(**params)
        wres = dark.call_api(wreq)

        prop = 'a'
        if place_name[0].lower() in VOWELS:
            prop = 'ad'

        to_speak='{} {} {} è {} con una temperatura percepita di {} gradi'.format(
                    date_name,
                    prop,
                    place_name,
                    wres.summaryHuman,
                    round(wres.tempFelt)
                )
        to_publish={
                'min' : round(wres.tempLowFelt),
                'max' : round(wres.tempHighFelt),
                'temp' : round(wres.tempFelt),
                'icon' : wres.summary
                }

        publishing = {
                'resource' : 'weather',
                'payload' : to_publish
                }

        ful = Fulfillment(to_speak, publishing)
        fulfillments.append(ful)

    @device_handler.command('ambrogio.WEATHER')
    def weather_action(place_name, place, date_name, date):
        weather(place_name, place, date_name, date)

    @device_handler.command('ambrogio.ECHO')
    def echo_action(txt):
        logging.info("echoing: {}".format(txt))
        if echo_effect.action:
            echo_effect.action()
            echo_effect.action = None


    @device_handler.command('ambrogio.GREET')
    def morning(nope):
        greet = 'salve'
        base = dt.datetime.combine(dt.date.today(), MIDNIGHT)
        now = dt.datetime.now()

        if now < base + MORNING:
            greet = 'buongiorno'
        elif now < base + AFTERNOON:
            greet = 'buon pomeriggio'
        else:
            greet = 'buona sera'

        ful = Fulfillment(greet)
        fulfillments.append(ful)
        weather(None,None,None,None)
        weather('amsterdam',{'coordinates':{'latitude':52.3667,'longitude':4.8945}},None,None)

    with SampleAssistant(lang, device_model_id, device_id,
                         conversation_stream, None,
                         grpc_channel, grpc_deadline,
                         device_handler, speak) as assistant:
        def do_assist():
            logging.info("ambrogio engaging")
            ding(conversation_stream)

            continue_conversation = assistant.assist()
            while continue_conversation:
                continue_conversation = assistant.assist()
            while len(fulfillments) > 0:
                ful = fulfillments.pop(0)
                speak(ful.text, ful.publishing)
            logging.info("ambrogio out")

            ding(conversation_stream)

        logging.info("initializing snowboydetector")
        ding(conversation_stream)
        detector = snowboydecoder.HotwordDetector("resources/ambrogio.pmdl", sensitivity=0.40, audio_gain=0.50)
        logging.info("starting snowboydetector")
        detector.start(do_assist)
        logging.info("terminating snowboydetector")
        detector.terminate()
        print ("terminated snowboy")
        
def ding(conversation_stream=None):
    wf = open("resources/ding.wav", "rb")
    conversation_stream.start_playback()
    conversation_stream.write(wf.read())
    conversation_stream.stop_playback()
    wf.close()


def nvl(value, ifNone, tr=lambda x: x):
    if value is None:
        return ifNone
    if len(value) == 0:
        return ifNone
    return tr(value)

def publish(resource, payload):
    requests.post(
            'http://localhost:3000/{}'.format(resource),
            payload
            )

if __name__ == '__main__':
    main()
# Copyright (C) 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
