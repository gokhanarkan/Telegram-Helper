import telebot
import forecastio
import requests
import json
import logger
import feedparser
import time
import pafy
import youtube_dl
import os.path
import asyncio
from telethon import TelegramClient, sync
import telepot
import sqlite3

# ai_lin_bot api token
api_token = "PASTE YOUR TOKEN HERE"
bot = telebot.TeleBot(api_token)
pot = telepot.Bot(api_token)

# database connection
connection = sqlite3.connect('database/groups.db', check_same_thread=False)

reddit = {
    'username': 'USERNAME',
    'password': 'PASSWORD',
    'client_id': 'CLIENT ID',
    'client_secret': 'CLIENT SECRET',
    'user_agent': "INFORMATIVE SENTENCE"
}

api_id = "API ID"
api_hash = "HASH"
imgur_client_id = 'IMGUR CLIENT ID'
imgur_client_secret = 'IMGUR SECRET'
client = TelegramClient("session_name", api_id, api_hash)
client.start(bot_token = "TOKEN")

# initialise asyncio loop to use some functions from core telegram api
loop = asyncio.get_event_loop()

@bot.message_handler(commands=['database'])
def db(message):
    if(message.from_user.id == GROUP_ADMIN): # To prevent to access only the admins can use the database
        try:
            # classic SQLite table creating and putting the relevant information by iterating the members
            cur = connection.cursor()
            cur.execute("""CREATE TABLE groups (group_id integer, people text)""")
            for person in client.iter_participants(message.chat.id):
                if (person.username == YOUR BOTS ID): # personal preference
                    pass
                else:
                    cur.execute("INSERT INTO groups VALUES (?, ?)", (message.chat.id, str(person.username)))
                    bot.send_message(message.chat.id, "{} added.".format(person.username))
            connection.commit()
        except:
            pass
    else:
        bot.send_message(message.chat.id, "Database has been already added. Try to delete it first.")

# Deleting database and reimplementing is in-development

# @bot.message_handler(commands=['deletedatabase'])
# def deletedb(message):
#     try:
#         if(databaseWarning > 0):
#             os.remove('database/groups.db')
#             databaseWarning -= 1
#             bot.send_message(message.chat.id, 'Database deleted.')
#     except:
#         pass

# We play online games together and the group is muted almost always. This command is for in order to breach that mute barrier:
@bot.message_handler(commands=['on'])
def shout(message):
    cur = connection.cursor()
    cur.execute("SELECT * FROM groups WHERE group_id = ?", (message.chat.id,))
    text = "Anyone? "
    for row in cur: # Get the relevant information from the database
        text += '@' + row[1] + ' '
    connection.commit()
    bot.send_message(message.chat.id, text)

# Since the group is muted, urgent messsages go with the all command.
# Little hack is inside. Please don't ban me @Telegram
@bot.message_handler(commands=['all'])
def kom(message):
    msg = message.text.split('/all ') # Gets the message by splitting the command
    # It's possible that only the command is written within the message. This if statement prevents.
    if(len(msg) > 1):
        cur = connection.cursor()
        cur.execute("SELECT * FROM groups WHERE group_id = ?", (message.chat.id,))
        text = ''
        for row in cur: # Again, getting the users from the database.
            text += '@' + row[1] + ' '
        connection.commit()
        # The bot first sends a message with mentioning everyone. Then deletes the user mentions from the message.
        # In my past experience, if you delete those user mentions after the message was sent, the notificaitons is still stuck on the lock page.
        # This is a simple conversion from bug to a feature. It's clean.
        first_message = '{}: {} {}'.format(
            message.from_user.first_name, msg[1], text)
        sent_message = pot.sendMessage(message.chat.id, first_message)
        edited_message = '{}: {}'.format(message.from_user.first_name, msg[1])
        message_variable = telepot.message_identifier(sent_message)
        pot.editMessageText(message_variable, edited_message)

@bot.message_handler(commands=['weather'])
def weather(message):
    # This function is pre-programmed just for the members. I am leaving some possible examples here.
    # Basically, the cities are already written for users. If I ask for the weather, the bot responds it with my location only. It varies to the users.
    # Database will be implemented for this feature. It will also be possible to write: "/weather Paris" and the bot will change the location for the specific individual until a new city will be used.
    city = ""
    if message.from_user.id == 123456789: city = 'London'
    elif (message.from_user.id == 123456789): city = 'Istanbul'
    elif (message.from_user.id == 123456789): city = 'Ankara'
    else: bot.send_message(message.chat.id, "I don't think I know you."); return

    open_api = "WEATHER API"
    url = open_api + city
    if city == 'London': city = 'Londra'
    data = requests.get(url).json()
    # I used openweather, the json data was in kelvin. So, conversion it is!
    temp_min = data['main']['temp_min'] - 273.15
    temp_max = data['main']['temp_max'] - 273.15
    weather_message = "In {} the current forecast is:\n" \
                        "\nMinimum: {}°C"\
                        "\nMaximum: {}°C"\
        .format(city, round(temp_min, 1), round(temp_max, 1))
    bot.reply_to(message, weather_message)

# Detailed weather in natural language
@bot.message_handler(commands=['wdetail'])
def weather(message):
    api_key = "WEATHER API FORECASTIO"
    forecast = forecastio.load_forecast(api_key, lat='LAT', lng='LONG')
    # Hourly data point with string manipulation
    j = str(forecast.hourly())
    j = j.replace("<ForecastioDataBlock instance: ", "")
    j = j.replace(" with 49 ForecastioDataPoints>", "")
    # Daily data point with string manipulation
    i = str(forecast.daily())
    i = i.replace("<ForecastioDataBlock instance: ", "")
    i = i.replace(" with 8 ForecastioDataPoints>", "")
    bot.reply_to(message, "Hi,")
    bot.send_message(message.chat.id, j)
    bot.send_message(message.chat.id, i)

# YouTube video downloader
# It might be illegal. I am not responsible.

# Send a message with /yt command and youtube link and it detects, downloads, sends back. If the video is larger than 50mb, it might take a couple minutes.
# The bot detects the best quality of the video. It can be changed from the 'best' variable
@bot.message_handler(commands=['yt'])
def get_url(message):
    y = message.text
    y = y.split()
    if(len(y) > 1): # Bug prevention
        try:
            youtube_link = y[1]
            video = pafy.new(youtube_link)
            best = video.getbest()
            best.download(quiet=True)
            recent_file = os.listdir(os.getcwd())
            newest = max(recent_file, key=os.path.getctime)
            if (best.get_filesize() > 50000000): # I use two different methods here depending on the size of the video.
                sendConfirmation(message, 1)
                loop.run_until_complete(largeFile(message, newest))
            else:
                sendConfirmation(message, 0)
                sendVideo(message, newest)
        except:
            return
    else:
        return
def sendVideo(message, vid):
    try:
        try:
            video = open(vid, "rb")
            bot.send_document(message.chat.id, video)
        finally:
            video.close()
            os.remove(vid)
    except:
        pass
async def largeFile(message, vid):
    try:
        try:
            file = await client.upload_file(vid)
            await client.send_file(message.chat.id, file, force_document=True)
        finally:
            os.remove(vid)
    except:
        pass
def sendConfirmation(message, val):
    if val > 0:
        bot.reply_to(message, "Your video is on the way but it's larger than 50mb, so beware of a couple minutes delay.")
    else:
        bot.reply_to(message, "Video is on the way.")

# I AM ALREADY A CRIMINAL BECAUSE OF THE PREVIOUS FUNCTION. SO WHY NOT CONVERT A YOUTUBE VIDEO TO A MUSIC FILE?
@bot.message_handler(commands=['ytmusic'])
def download_music(message):
    y = message.text
    y = y.split()
    if (len(y) > 1):
        try:
            youtube_link = y[1]
            audio = pafy.new(youtube_link)
            best = audio.getbestaudio(preftype="m4a")
            audioConfirmation(message)
            best.download(quiet=True)
            recent_file = os.listdir(os.getcwd())
            newest = max(recent_file, key=os.path.getctime)
            if (best.get_filesize() > 50000000):
                largeAudio(message)
                return
            sendAudio(message, newest)
        except:
            return
    else:
        return
def sendAudio(message, aud):
    try:
        try:
            audio = open(aud, "rb")
            bot.send_audio(message.chat.id, audio)
        finally:
            audio.close()
            os.remove(aud)
    except:
        pass
def largeAudio(message):
    bot.reply_to(message, "Sorry, I can't send a music file larger than 50mb at the moment.")
def audioConfirmation(message):
    bot.reply_to(message, "Your music is on the way.\nIt might take a few minutes.")

# Below, there are functions always working in the background and only be triggered if the specific words is used.
# Don't need to command anything the bot will complete you flawlessly.
def methodExecution(message):
    key_words = {"gbp", "pound", "GBP", "POUND", "eur", "euro", "EUR", "EURO", "usd", "dolar", "USD", "dollars", "dollar", "pounds", "POUNDS", "euros", "EUROS"} # I will change this with only lowercases in the future.
    try:
        for key in key_words:
            if key in message.text:
                return True
        return False
    except:
        pass
def currency(message):
    currency_api = "CURRENCY API"
    currencies = "CURRENCIES"
    url = "I USED FIXER.IO HERE. RECOMMENDED." + currency_api + currencies
    num = requests.get(url).json()
    # Below the values; euros, pounds, dollars are converted to turkish liras. I am keeping them as a reference. Since the service is free, the api only converts things to euro; so from that point you're responsible to convert to another currency.
    eur2try = num['rates']['TRY']
    usd2try = eur2try / num['rates']['USD']
    gbp2try = eur2try / num['rates']['GBP']
    euro = ['eur', 'euro', 'avro', 'evro']
    pound = ['gbp', 'pound', 'sterlin']
    dolar = ['dolar', 'dollar', 'usd']

    words = message.text.split()
    answers = []

    for word in words:
        if words.index(word) == 0:
            continue
        elif word.lower() in pound:
            try:
                amount = float(words[words.index(word) - 1])
                answers.append(gbp(amount, amount * gbp2try))
                words.remove(words[words.index(word)])
            except:
                pass
        elif word.lower() in euro:
            try:
                amount = float(words[words.index(word) - 1])
                answers.append(eur(amount, amount * eur2try))
                words.remove(words[words.index(word)])
            except:
                pass
        elif word.lower() in dolar:
            try:
                amount = float(words[words.index(word) - 1])
                answers.append(usd(amount, amount * usd2try))
                words.remove(words[words.index(word)])
            except:
                pass

# Below are one line answers. I am keeping the turkish lira conversion message as a reference.
    one_line_answer = ''
    if len(answers) > 0:
        for answer in answers:
            one_line_answer += answer + "\n"
        bot.reply_to(message, one_line_answer)
def gbp(amount, converted_amount):
    return "£{} approximately equals to {}₺.".format(round(amount, 2), round(converted_amount, 2))
def eur(amount, converted_amount):
    return "€{} approximately equals to {}₺.".format(round(amount, 2), round(converted_amount, 2))
def usd(amount, converted_amount):
    return "${} approximately equals to {}₺.".format(round(amount, 2), round(converted_amount, 2))


# Reddit Media Grabber
# Takes the media embedded within the post and sends to the group chat within 1 to 3 seconds.
# So participants of the message group don't need to switch between apps or click on the link.
# Check the readme file for an example gif.
# Below there are methods. The bot grabs everything smaller than 50mb. From Reddit, imgur, gfycat whatever you need.

# Being lazy to comment things right now, that doesn't mean I code without comments, the comments were in my native tongue and I deleted it. I will add the english ones soon.
def access_token(user):
    client_auth = requests.auth.HTTPBasicAuth(user['client_id'], user['client_secret'])
    post_data = {"grant_type": "password", "username": user['username'], "password": user['password']}
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers={
        "User-Agent": user['user_agent']
    })
    response_dict = response.json()
    response_dict.update({'user_agent': user['user_agent']})
    return response_dict
def is_reddit_link(message):
    if message.entities:
        for entity in message.entities:
            if entity.type == 'url':
                url = message.text[entity.offset: entity.offset+entity.length]
                if 'www.reddit.com' in url.split('/'):
                    send_media_to(message.chat.id, reddit_post(url, access_token=access_token(reddit)), with_caption=True)
def reddit_post(url, access_token):
    headers = {
        "Authorization": "{} {}".format(access_token['token_type'], access_token['access_token']),
        "User-Agent": access_token['user_agent']
    }
    params = {'id': 't3_' + url.split('/')[6]}
    response = requests.get("https://oauth.reddit.com/api/info", headers=headers, params=params)
    if response.status_code == 200 and len(response.json()['data']['children']) > 0:
        return response.json()['data']['children'][0]
def send_media_to(chat_id, post, with_caption = False):
    try:
        if post['data']['domain'] == 'i.redd.it':
            extension = post['data']['url'].split('.').pop()
            url = post['data']['url']

            if extension == 'jpg' or extension == 'png':
                if with_caption:
                    caption = '{} - {}'.format(post['data']['subreddit_name_prefixed'],
                                                             post['data']['title'])
                    bot.send_photo(chat_id, url, caption=caption)
                else:
                    bot.send_photo(chat_id, url)
                return True
            elif extension == 'gif':
                if with_caption:
                    caption = '{} - {}'.format(post['data']['subreddit_name_prefixed'],
                                               post['data']['title'])
                    bot.send_video(chat_id, url, caption=caption)
                else:
                    bot.send_video(chat_id, url)
                return True

        elif post['data']['domain'] == 'gfycat.com':
            splitted_url = post['data']['url'].split('/')
            url, is_good = get_gfycat_link(splitted_url.pop())
            if is_good:
                if with_caption:
                    caption = '{} - {}'.format(post['data']['subreddit_name_prefixed'],
                                               post['data']['title'])
                    bot.send_video(chat_id, url, caption=caption)
                else:
                    bot.send_video(chat_id, url)
                return True

            else:
                return False

        elif post['data']['domain'] == 'i.imgur.com':
            extension = post['data']['url'].split('.').pop()
            hash = post['data']['url'].split('/').pop().split('.')[0]
            url = 'https://api.imgur.com/3/image/' + hash
            payload = {}
            headers = {
                'Authorization': 'Client-ID ' + imgur_client_id
            }
            response = requests.request('GET', url, headers=headers, data=payload, allow_redirects=False)
            data = response.json()['data']

            if extension == 'jpg' or extension == 'png':
                image_size = data['size']
                if image_size < 4999999:
                    if with_caption:
                        caption = '{} - {}'.format(post['data']['subreddit_name_prefixed'],
                                                   post['data']['title'])
                        bot.send_photo(chat_id, url, caption=caption)
                    else:
                        bot.send_photo(chat_id, url)
                    return True
                else:
                    return False

            elif 'gif' in extension:
                if data['mp4_size'] < 19000000:
                    url = data['mp4']
                    if with_caption:
                        caption = '{} - {}'.format(post['data']['subreddit_name_prefixed'],
                                                   post['data']['title'])
                        bot.send_video(chat_id, url, caption=caption)
                    else:
                        bot.send_video(chat_id, url)
                    return True
                else:
                    return False

        elif post['data']['domain'] == 'v.redd.it':
            url = post['data']['media']['reddit_video']['fallback_url']
            if with_caption:
                caption = '{} - {}'.format(post['data']['subreddit_name_prefixed'],
                                           post['data']['title'])
                bot.send_video(chat_id, url, caption=caption)
            else:
                bot.send_video(chat_id, url)
            return True
        else:
            return False
    except:
        return False
def get_gfycat_link(url_id):
    url = 'https://api.gfycat.com/v1/gfycats/' + url_id
    r = requests.get(url)
    data = r.json()['gfyItem']
    if data['mp4Size'] < 19000000:
        return data['mp4Url'], True
    elif data['content_urls']['mobile']['size'] < 19000000:
        return data['content_urls']['mobile']['url'], True
    else:
        return data['mobileUrl'], False

# Bot takes literally EVERY messages in the last 24 hours. I fixed that with the time object below.
# It (she) only takes the last 10 minutes when she is booted.
@bot.message_handler(func=lambda msg: True)
def timeCheck(message):
    projectedTime = int(round(time.time())) + 600
    actualTime = message.json['date']
    if(projectedTime > actualTime):
        message_handler(message)
    else:
        pass
def message_handler(message):
    if methodExecution(message):
        currency(message)
    try:is_reddit_link(message)
    except:pass

bot.polling()