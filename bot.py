import os


import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv('secret.env')
TOKEN = os.getenv('DISCORD_TOKEN')


import speedrace

bot = commands.Bot(command_prefix='-')


@bot.event
async def on_ready():
    print(
        f'{bot.user} is connected to the server.'
    )
    called_hourly.start()


@bot.command(name='init', help="*Initalizes a competition of Speedrace Weekly. No spaces in category names. (Moderators only)")
@commands.has_role("Moderators")
async def init(ctx, data1, data2 = "", data3 = "", data4 = "", data5 = "", data6 = ""):
    try: 
        if(data6 == ""):
            data = data1
            if(data2 != ""):
                data += " " + data2
            if(data3 != ""):
                data += " " + data3
            if(data4 != ""):
                data += " " + data4
            if(data5 != ""):
                data += " " + data5
            await ctx.send(speedrace.init(data))
            await ctx.send(speedrace.info())
            await dm_setup(dmctx = ctx)
        else: 
            await ctx.send("Initalization Failed: Too many spaces. Try again")
    except: 
        await ctx.send("Error")


@bot.command(name='set-winners', help="*Set the winners of the phase 1 or phase 3 race (Moderators only)")
@commands.has_role("Moderators")
async def setWinners(ctx, data, data2 = "", data3 = "", data4 = "", data5 = ""):
    try: 
        print(data)
        if(data5 == ""):
            if(data2 != ""):
                data += " " + data2
            if(data3 != ""):
                data += " " + data3
            if(data4 != ""):
                data += " " + data4
            if(speedrace.game == None):
                await ctx.send("Error: No game currently in progress.")
            else: 
                await ctx.send(speedrace.setWinners(data))
        else: 
            await ctx.send("Set Winners Failed: Too many spaces. Try again")
    except: 
        await ctx.send("Error")


@bot.command(name='edit', help="Edit your own submitted run, use: -edit [runId] [field] [value]")
async def editRuns(ctx, runId = None, field = None, newValue = None, newValue2 = None):
    try: 
        if(newValue2 != None and isinstance(newValue, str) and isinstance(newValue2, str)):
            newValue += " " + newValue2
        if(speedrace.game == None):
            await ctx.send("Error: No game currently in progress.")
        elif(runId == None or field == None or newValue == None):
            await ctx.send("Error: Invalid arguments, use: -edit [runId] [field] [value]")
        else: 
            user = ctx.author
            role = discord.utils.find(lambda r: r.name == 'Moderators', ctx.message.guild.roles)
            print(user.roles)
            if role in user.roles:
                user = "Moderator"
            await ctx.send(speedrace.editRun(str(user), runId, field, newValue))
    except: 
        await ctx.send("Error")


@bot.command(name='points', help="Returns the points for each phase (and speedrun category)")
async def points(ctx):
    try:
        if(speedrace.game == None):
            ctx.send("Error: No game currently in progress.")
        else: 
            await ctx.send(speedrace.getScores())
    except: 
        await ctx.send("Error")


@bot.command(name='standings', help="Returns the current point standings of competitors with points")
async def standings(ctx):
    try:
        if(speedrace.game == None):
            await ctx.send("Error: No game currently in progress.")
        else: 
            await ctx.send(speedrace.printScores("Current"))
    except: 
        await ctx.send("Error")


@bot.command(name='submit', help="Submit a speedrun, use: -submit [category] [time] [link]")
async def points(ctx, cat = None, time = None, link = None, name1 = "", name2 = ""):
    try:
        print(name1 + ", " + name2)
        if(name2 != ""):
            name1 += " " + name2
        print(name1)
        if(speedrace.game == None):
            await ctx.send("Error: No game currently in progress.")
        elif(cat == None or time == None or link == None):
            await ctx.send("Error: Invalid arguments, use: -submit [category] [time] [link]")
        else: 
            if(name1 == ""):
                name1 = ctx.author
            role = discord.utils.get(ctx.message.guild.roles, name = 'Competitors') 
            message = speedrace.submitRun(str(name1) + ";" + cat + ";" + time + ";" + link)
            if(message[0:5] == "ERROR"):
                await ctx.send(message)
            else: 
                await ctx.send(("{} " + message).format(role.mention))
    except: 
        await ctx.send("Error")


@bot.command(name='category-runs', help="Shows personal bests, use: -run [category-optional]")
async def points(ctx, category = "all"):
    try: 
        if(speedrace.game == None):
            await ctx.send("Error: No game currently in progress.")
        else: 
            await ctx.send(speedrace.getRuns(category))
    except: 
        await ctx.send("Error")


@bot.command(name='get-run', help="Shows a run (or all runs), use: -run [runId-optional]")
async def points(ctx, runId = 0):
    try: 
        if(speedrace.game == None):
            await ctx.send("Error: No game currently in progress.")
        else: 
            await ctx.send(speedrace.getRun(runId))
    except: 
        await ctx.send("Error")


@bot.command(name='set-day', help="*Make Daily Phase 2 Announcement (Moderators only)")
@commands.has_role("Moderators")
async def sendDailyMessage(ctx, day):
    try: 
        await ctx.send(speedrace.updateDayNumber(day))
    except: 
        await ctx.send("Error")


async def dailyMessage():
    f = open("channel.txt", "r")
    lines = f.readlines()
    print(lines[0].strip())
    channelID = int(lines[0].strip())
    channel = bot.get_channel(channelID)
    role = discord.utils.get(channel.guild.roles, name = 'Competitors') 
    await channel.send(("{} " + speedrace.p2DailyAnnouncement()).format(role.mention))


async def dm_setup(dmctx = None, dmid = None):
    channelID = 0
    if(dmctx != None):
        channelID = dmctx.message.channel.id
    elif (dmid != None):
        channelID = dmid
    else: 
        print("Error: No arguments passed to dm_setup")
        return
    print(channelID)
    channel = bot.get_channel(channelID)
    await channel.send("This channel set for the daily messages.")
    f = open("channel.txt", "w")
    f.truncate() #remove existing content
    f.write(str(channelID))


@bot.command(name='daily-message', help="*Make Daily Phase 2 Announcement (Moderators only)")
@commands.has_role("Moderators")
async def sendDailyMessage(ctx):
    try:
        canSend = speedrace.doDailyMessage()
        if(canSend == ""):
            await dailyMessage()
        else: 
            await ctx.send("Speedrace Bot refused to send a daily message: " + canSend)
    except: 
        await ctx.send("Error")


@bot.command(name='force-daily-message', help="*Force the Bot to make the Daily Phase 2 Announcement (Moderators only)")
@commands.has_role("Moderators")
async def forceDailyMessage(ctx):
    try:
        await dailyMessage()
    except: 
        await ctx.send("Error")


@bot.command(name='set-dm-channel', help="*Sets the channel for the bot to make daily announcements (Moderators only)")
@commands.has_role("Moderators")
async def sendDailyMessage(ctx, id = None):
    try:
        if(id == None):
            await dm_setup(ctx)
        else:
            await dm_setup(id)
    except: 
        await ctx.send("Error")


# Daily message
@tasks.loop(hours=1)
async def called_hourly():
    canSend = speedrace.doDailyMessage()
    if(canSend == ""):
        await dailyMessage()
    # else: 
    #     f = open("channel.txt", "r")
    #     lines = f.readlines()
    #     print(lines[0].strip())
    #     channelID = int(lines[0].strip())
    #     channel = bot.get_channel(channelID)
    #     await channel.send("Speedrace Bot refused to send a daily message: " + canSend)


@called_hourly.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")


bot.run(TOKEN)