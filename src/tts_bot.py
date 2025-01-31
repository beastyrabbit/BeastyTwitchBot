import io
import os

import obsws_python as obs
import pyaudio
from pydub import AudioSegment
from twitchio.ext import commands

from helperfunc.base_values import CHANNEL_NAME, setup_logger, get_valid_token
from helperfunc.global_methods import get_text_to_spech
from helperfunc.object_manager import UserManager, ObjectManager

_logger = setup_logger(__name__)


class Bot(commands.Bot):
    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        access_token = get_valid_token()
        self.access_token = access_token
        object_manager: ObjectManager = ObjectManager()
        self.user_manager: UserManager = object_manager.user_manager
        self.pyaudio = pyaudio.PyAudio()
        self.audio_device = 23

        self.number_of_send_messages = 0

        # Define connection details
        host = "192.168.160.193"
        port = 4455
        password = os.getenv("OBS_PASSWORD")
        # Connect to OBS
        self.cl = None
        try:
            self.cl = obs.ReqClient(host=host, port=port, password=password, timeout=3)
        except Exception as e:
            _logger.error(f"Failed to connect to OBS: {e}")

        super().__init__(
            token=access_token, prefix="!", initial_channels=[CHANNEL_NAME]
        )

    async def event_command_error(self, context: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.ArgumentParsingFailed):
            await context.send(error.message)

        elif isinstance(error, commands.MissingRequiredArgument):
            await context.send("You're missing an argument: " + error.name)

        elif isinstance(
                error, commands.CheckFailure
        ):  # we'll explain checks later, but lets include it for now.
            await context.send("Sorry, you cant run that command: " + error.args[0])

        #
        # elif isinstance(error, YoutubeConverterError):
        #  await context.send(f'{error.link} is not a valid youtube URL!')

        else:
            _logger.error(error)

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        _logger.info(f"Logged in as | {self.nick}")
        _logger.info(f"User id is | {self.user_id}")
        await self.get_channel(CHANNEL_NAME).send("I can talk for you, Bunny!")

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return
        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    @commands.command(name="tts")
    async def tts_command(self, ctx: commands.Context, *text: str):
        _logger.info(
            f"User {ctx.author.name} is calling the tts command with text: {text}"
        )

        # Get audio bytes (WAV format)
        text_string = " ".join(text)
        audio_bytes = get_text_to_spech(text_string)

        # Decode MP3 to PCM using pydub
        _logger.info("Decoding MP3 audio bytes to PCM")
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")

        # Extract audio details
        channels = audio.channels
        sample_width = audio.sample_width
        frame_rate = audio.frame_rate
        pcm_data = audio.raw_data

        # Open a PyAudio stream for playback
        audio_device = self.audio_device
        stream = self.pyaudio.open(
            format=self.pyaudio.get_format_from_width(sample_width),
            channels=channels,
            rate=frame_rate,
            output=True,
            output_device_index=audio_device,
        )

        # Write PCM data to the stream
        _logger.info(f"Playing the audio")
        stream.write(pcm_data)

        # Close the stream
        stream.stop_stream()
        stream.close()


bot = Bot()
bot.run()
