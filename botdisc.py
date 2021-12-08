    #!./.venv/bin/python
     
    import discord      # base discord module
    import code         # code.interact
    import os           # environment variables
    import inspect      # call stack inspection
    import random       # dumb random number generator
    import youtube_dl
    from discord.utils import get
    from discord import FFmpegPCMAudio
    from discord.ext import commands,tasks    # Bot class and utils
     
    ################################################################################
    ############################### HELPER FUNCTIONS ###############################
    ################################################################################
     
    # log_msg - fancy print
    #   @msg   : string to print
    #   @level : log level from {'debug', 'info', 'warning', 'error'}
    def log_msg(msg: str, level: str):
        # user selectable display config (prompt symbol, color)
        dsp_sel = {
            'debug'   : ('\033[34m', '-'),
            'info'    : ('\033[32m', '*'),
            'warning' : ('\033[33m', '?'),
            'error'   : ('\033[31m', '!'),
        }
     
        # internal ansi codes
        _extra_ansi = {
            'critical' : '\033[35m',
            'bold'     : '\033[1m',
            'unbold'   : '\033[2m',
            'clear'    : '\033[0m',
        }
     
        # get information about call site
        caller = inspect.stack()[1]
     
        # input sanity check
        if level not in dsp_sel:
            print('%s%s[@] %s:%d %sBad log level: "%s"%s' % \
                (_extra_ansi['critical'], _extra_ansi['bold'],
                 caller.function, caller.lineno,
                 _extra_ansi['unbold'], level, _extra_ansi['clear']))
            return
     
        # print the damn message already
        print('%s%s[%s] %s:%d %s%s%s' % \
            (_extra_ansi['bold'], *dsp_sel[level],
             caller.function, caller.lineno,
             _extra_ansi['unbold'], msg, _extra_ansi['clear']))
     
    ################################################################################
    ############################## BOT IMPLEMENTATION ##############################
    ################################################################################
    # bot instantiation
    bot = commands.Bot(command_prefix='!')
     
    # on_ready - called after connection to server is established
    @bot.event
    async def on_ready():
        log_msg('logged on as <%s>' % bot.user, 'info')
     
    # on_message - called when a new message is posted to the server
    #   @msg : discord.message.Message
    @bot.event
    async def on_message(msg):
        # filter out our own messages
        if msg.author == bot.user:
            return
     
        log_msg('message from <%s>: "%s"' % (msg.author, msg.content), 'debug')
     
        # overriding the default on_message handler blocks commands from executing
        # manually call the bot's command processor on given message
        await bot.process_commands(msg)
     
    # roll - rng chat command
    #   @ctx     : command invocation context
    #   @max_val : upper bound for number generation (must be at least 1)
    @bot.command(brief='Generate random number between 1 and <arg>')
    async def roll(ctx, max_val: int):
        # argument sanity check
        if max_val < 1:
            raise Exception('argument <max_val> must be at least 1')
     
        await ctx.send(random.randint(1, max_val))
     
    # roll_error - error handler for the <roll> command
    #   @ctx     : command that crashed invocation context
    #   @error   : ...
    @roll.error
    async def roll_error(ctx, error):
        await ctx.send(str(error))
    
        youtube_dl.utils.bug_reports_message = lambda: ''

    ytdl_format_options = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
    }

    ffmpeg_options = {
        'options': '-vn'
    }
    
    discord.opus.load_opus
    
    ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

    class YTDLSource(discord.PCMVolumeTransformer):
        def __init__(self, source, *, data, volume=0.5):
            super().__init__(source, volume)
            self.data = data
            self.title = data.get('title')
            self.url = ""

        @classmethod
        async def from_url(cls, url, *, loop=None, stream=False):
            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            if 'entries' in data:
                # take first item from a playlist
                data = data['entries'][0]
            filename = data['title'] if stream else ytdl.prepare_filename(data)
            return filename
 
    @bot.command(name='join', help='Tells the bot to join the voice channel')
    async def join(ctx):
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        else:
            channel = ctx.message.author.voice.channel
        await channel.connect()

    @bot.command(name='scram', help='To make the bot leave the voice channel')
    async def leave(ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
        else:
            await ctx.send("The bot is not connected to a voice channel.")
    
    @bot.command(name='play', help='To play song')
    async def play(ctx,url):
        channel = ctx.message.author.voice.channel
        await channel.connect()  
        server = ctx.message.guild
        voice_channel = server.voice_client 
        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=filename))
        await ctx.send('Playing: {}'.format(filename))


    @bot.command(name='pause', help='This command pauses the song')
    async def pause(ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
        else:
            await ctx.send("The bot is not playing anything at the moment.")
    
    @bot.command(name='resume', help='Resumes the song')
    async def resume(ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()
        else:
            await ctx.send("The bot was not playing anything before this. Use play_song command")
        
    @bot.command(name='stop', help='Stops the song')
    async def stop(ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.stop()
        else:
            await ctx.send("The bot is not playing anything at the moment.")
     
    ################################################################################
    ############################# PROGRAM ENTRY POINT ##############################
    ################################################################################
     
    if __name__ == '__main__':
        # check that token exists in environment
        if 'BOT_TOKEN' not in os.environ:
            log_msg('save your token in the BOT_TOKEN env variable!', 'error')
            exit(-1)
     
        # launch bot (blocking operation)
        bot.run(os.environ['BOT_TOKEN'])


