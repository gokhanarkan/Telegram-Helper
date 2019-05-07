import csv, os, threading, requests, json, datetime, time

# Bot sends hot reddit media posts casually (regularly) to the group or private chats.
# The timeframe (frequency) can be set after the initial creation. It needs to be divisible by 30.
# A personal reddit account is must. Bot iterates the hot posts from the followed subreddits.
# This is an automated casual bot, for me, it sends new reddit post and media in every 30 minutes. I don't need to click on a link or anything.

try: os.mkdir('database')
except FileExistsError: pass
try: os.mkdir('database/chats')
except FileExistsError: pass

DEFAULT_FREQUENCY_VALUE = 60 # Default frequency value assigned by the time of creation
MINIMUM_FREQUENCY_VALUE = 30 # Minimum frequency value that can be set by users
MAXIMUM_FREQUENCY_VALUE = 1440 # Maximum frequency value that can be set by users
MINIMUM_POST_SCORE = 100 # Posts should have at least this much upvote to be send

script_path = os.path.dirname(os.path.realpath(__file__))
chats_path = script_path + '/database/chats/'

bot_token = 'BOT TOKEN'
URL = "https://api.telegram.org/bot{}/".format(bot_token)

# You should create a reddit app and provide the following informations (username and password belong to your reddit account)
reddit = {
    'username': 'USERNAME',
    'password': 'PASSWORD',
    'client_id': 'CLIENT ID',
    'client_secret': 'CLIENT SECRET',
    'user_agent': "FRIENDLY MESSAGE"
}

# You should create a imgur api client and provide the following informations
imgur_client_id = 'IMGUR ID'
imgur_client_secret = 'CLIENT SEC'

hot_posts_list = []


# Reddit API requires an access token to perform GET and POST requests. This function will return a dict which includes access token and user agent
def access_token(user):
    client_auth = requests.auth.HTTPBasicAuth(user['client_id'], user['client_secret'])
    post_data = {"grant_type": "password", "username": user['username'], "password": user['password']}
    response = requests.post("https://www.reddit.com/api/v1/access_token", auth=client_auth, data=post_data, headers={
        "User-Agent": user['user_agent']
    })
    response_dict = response.json()
    response_dict.update({'user_agent': user['user_agent']})
    return response_dict


# This function returns a list of hot posts using prensented access token, limit determines the amount of post.
def hot_posts(access_token, limit=100):
    headers = {
        "Authorization": "{} {}".format(access_token['token_type'], access_token['access_token']),
        "User-Agent": access_token['user_agent']
    }
    params = {'limit': limit}
    response = requests.get("https://oauth.reddit.com/hot", headers=headers, params=params)
    return response.json()['data']['children']


# Actuates hot_posts() method and appends returned list of posts to 'hot_posts_list'
def fetch_reddit(type='hot', limit=100):
    if type == 'hot':
        global hot_posts_list
        hot_posts_list.clear()
        hot_posts_list = hot_posts(access_token(reddit), limit=limit)


# Creates a folder, a csv file named 'user_info.csv' for desired chat_id and appends default values to it.
def create_account(message, frequency=DEFAULT_FREQUENCY_VALUE, nine_to_five=True):
    chat_id = message['chat']['id']
    if message['from']['id'] not in get_admins(chat_id):
        send_message(chat_id, 'Sorry! Only admins can use this command.', reply_to=message['message_id'])
        return

    fields = ["chat_id", "frequency", 'nine_to_five']
    try:
        os.mkdir('database/chats/{}'.format(chat_id))
    except FileExistsError:
        pass
    try:
        with open('database/chats/{}/chat_info.csv'.format(chat_id), 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields, delimiter=';')
            writer.writeheader()
            writer.writerow({"chat_id": chat_id, "frequency": frequency, 'nine_to_five': nine_to_five})
            csvfile.close()
            send_message(chat_id, 'Account creation is succesfull!\n\n'
                                  'Default frequency value is 60 minutes. Bot sends a new adult content in every 60 minutes.\n\n'
                                  'Admins can change this value with the command /freq = {enter a number between 30 and 1440, number should be divisable by 30}')
    except:
        try:
            send_message(chat_id, "Account creation is unsuccessful, try again.")
            os.remove('database/chats/{}/chat_info.csv'.format(chat_id))
        except:
            pass


# Returns the active admin list of presented chat_id
def get_admins(chat_id):
    admins = []
    json_data = {
        "chat_id": chat_id
    }
    send_url = URL + 'getChatAdministrators'
    respond = requests.get(send_url, json=json_data)

    if respond.json()['ok'] == False:
        admins.append(chat_id)
        return admins

    for user in respond.json()['result']:
        admins.append(user['user']['id'])
    return admins


# If the user is admin and enters a valid frequency value, that value will be sent to set_frequency() method
def frequency_handler(message):
    def invalid_value():
        send_message(message['chat']['id'],
                     'The value you entered is invalid.\n\nPlease enter a number between 30 and 1440, number should be divisable by 30.\n\n(60 = 60 minutes)',
                     reply_to=message['message_id'])

    def unauthorized_user():
        send_message(message['chat']['id'], 'Sorry! You do not have permission to use this command.',
                     reply_to=message['message_id'])

    def account_not_created():
        send_message(message['chat']['id'], "You don't have an active account.\n\n\
        Please type /create first, then you will be able to change your frequency value.",
                     reply_to=message['message_id'])

    if int(message['from']['id']) not in get_admins(message['chat']['id']):
        unauthorized_user()
        return

    if not os.path.isdir(chats_path + str(message['chat']['id']) + '/'):
        account_not_created()
        return

    try:
        frequency = int(message['text'].split('=').pop())
        if type(
                frequency) == int and frequency >= MINIMUM_FREQUENCY_VALUE and frequency <= MAXIMUM_FREQUENCY_VALUE and frequency % MINIMUM_FREQUENCY_VALUE == 0:
            set_frequency(message['chat']['id'], frequency=frequency)
        else:
            invalid_value()
    except:
        invalid_value()


# Frequency value used to change the previous frequency value in the specified chat's user_info.csv file
def set_frequency(chat_id, frequency):
    fields = ["chat_id", "frequency", 'nine_to_five']
    try:
        info = {}
        with open('database/chats/{}/chat_info.csv'.format(chat_id), 'r') as readcsv:
            reader = csv.DictReader(readcsv, delimiter=';')
            for item in reader:
                for field in fields:
                    info[field] = item.get(field)
            readcsv.close()

        info['frequency'] = frequency

        with open('database/chats/{}/chat_info.csv'.format(chat_id), 'w') as writecsv:
            writer = csv.DictWriter(writecsv, fieldnames=info.keys(), delimiter=';')
            writer.writeheader()
            writer.writerow(info)
            writecsv.close()

        send_message(chat_id, "Frequency value has changed to {} minutes successfuly".format(frequency))
    except:
        pass


# Method for sending message to specified chat_id with specified text, also 'reply_to' parameter can be used to reply a message
def send_message(chat_id, text, reply_to=None):
    json_data = {
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": reply_to
    }
    send_url = URL + 'sendMessage'
    requests.post(send_url, json=json_data)


# Method for deleting the original and the replied message
def delete_message(message):
    if message['from']['id'] not in get_admins(message['chat']['id']):
        send_message(message['chat']['id'], 'Sorry! You do not have permission to use this command.',
                     reply_to=message['message_id'])
        return
    try:
        reply = message['reply_to_message']
        json_data = {
            "chat_id": message['chat']['id'],
            "message_id": reply['message_id'],
        }
        send_url = URL + 'deleteMessage'
        requests.post(send_url, json=json_data)
    finally:
        json_data = {
            "chat_id": message['chat']['id'],
            "message_id": message['message_id'],
        }
        send_url = URL + 'deleteMessage'
        requests.post(send_url, json=json_data)


# Method for sending a message of active bot commands to a chat.
def help(chat):
    msg = '''/create: command to start sapik_bot with default values.

    /freq: command to change frequency, value should be divisable by 30 and cannot exceed 1440 (i.e. 24 hours). (e.g. /freq = 360)

    /del: command to delete a message, reply a message with this command to delete it. (only admins can use this command)

    /help: command to list all active bot commands.'''
    send_message(chat, msg)


# Method for returning the gfycat link of the video and a bool value, which is 'True' for sizes below 20mb, 'False' for above
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


# Method for sending the media in specified post, returns 'True' if process is succesfull
def send_post_to(chat_id, post):
    try:
        if post['data']['domain'] == 'i.redd.it':
            extension = post['data']['url'].split('.').pop()

            if extension == 'jpg' or extension == 'png':
                json_data = {
                    "chat_id": chat_id,
                    "photo": post['data']['url'],
                }
                send_url = URL + 'sendPhoto'
                requests.post(send_url, json=json_data)
                return True
            elif extension == 'gif':
                json_data = {
                    "chat_id": chat_id,
                    "video": post['data']['url'],
                }
                send_url = URL + 'sendVideo'
                requests.post(send_url, json=json_data)
                return True

        elif post['data']['domain'] == 'gfycat.com':
            splitted_url = post['data']['url'].split('/')
            mobile_url, is_good = get_gfycat_link(splitted_url.pop())
            if is_good:
                json_data = {
                    "chat_id": chat_id,
                    "video": mobile_url,
                }
                send_url = URL + 'sendVideo'
                requests.post(send_url, json=json_data)
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
                    json_data = {
                        "chat_id": chat_id,
                        "photo": post['data']['url'],
                    }
                    send_url = URL + 'sendPhoto'
                    requests.post(send_url, json=json_data)
                    return True
                else:
                    return False

            elif 'gif' in extension:
                if data['mp4_size'] < 19000000:
                    json_data = {
                        "chat_id": chat_id,
                        "video": data['mp4'],
                    }
                    send_url = URL + 'sendVideo'
                    requests.post(send_url, json=json_data)
                    return True
                else:
                    return False

        elif post['data']['domain'] == 'v.redd.it':
            url = post['data']['media']['reddit_video']['fallback_url']
            json_data = {
                "chat_id": chat_id,
                "video": url,
            }
            send_url = URL + 'sendVideo'
            requests.post(send_url, json=json_data)
            return True

        else:
            return False
    except:
        return False


# Method for fetching a unique post from 'get_unique_post_for()' method. Post id gets appended to 'not_unique_post.csv' file and sent to 'send_post_to()' method
def send_unique_post(chat, this_time):
    unique_post = get_unique_post_for(chat)
    if unique_post:
        append_to_used_posts(chat, unique_post, this_time)
        if not send_post_to(chat, unique_post):
            send_unique_post(chat, this_time)
    else:
        pass  # for now, fill this line later.


# Method for appending parameters of the post to specified chat's 'not_unique_posts.csv' file
def append_to_used_posts(chat, post, this_time):
    fields = ["post_id", "sub_name", "reddit_link", "time"]
    with open('database/chats/{}/not_unique_posts.csv'.format(chat), 'a') as append_csv:
        appender = csv.DictWriter(append_csv, fieldnames=fields, delimiter=';')
        appender.writerow({"post_id": post['data']['id'], "sub_name": post['data']['subreddit'],
                           "reddit_link": 'https://www.reddit.com' + post['data']['permalink'],
                           "time": this_time})
    append_csv.close()


# Method for returning a unique post for the chat
def get_unique_post_for(chat):
    fields = ["post_id", "sub_name", "reddit_link", "time"]
    sent_post_ids = []
    if os.path.isfile('database/chats/{}/not_unique_posts.csv'.format(chat)):
        with open('database/chats/{}/not_unique_posts.csv'.format(chat), 'r') as posts_csv:
            reader = csv.DictReader(posts_csv, delimiter=';')
            for item in reader:
                sent_post_ids.append(item.get('post_id'))
        posts_csv.close()
    else:
        with open('database/chats/{}/not_unique_posts.csv'.format(chat), 'w') as created_csv:
            writer = csv.DictWriter(created_csv, fieldnames=fields, delimiter=';')
            writer.writeheader()
        created_csv.close()
        return hot_posts_list[0]

    for post in hot_posts_list:
        if post['data']['score'] < MINIMUM_POST_SCORE or str(post['data']['id']) in sent_post_ids:
            continue
        else:
            return post

    return None


# Checks whether the chat needs an update
def chat_needs_update(chat, this_time):
    freq = 0
    last_time = 0

    with open('database/chats/{}/chat_info.csv'.format(chat), 'r') as chat_csv:
        reader = csv.DictReader(chat_csv, delimiter=';')
        for item in reader:
            freq = int(item.get('frequency'))
        chat_csv.close()

    if os.path.isfile('database/chats/{}/not_unique_posts.csv'.format(chat)):
        with open('database/chats/{}/not_unique_posts.csv'.format(chat), 'r') as posts_csv:
            reader = csv.DictReader(posts_csv, delimiter=';')
            for item in reader:
                last_time = int(item.get('time'))
        posts_csv.close()

    if this_time - last_time >= (freq - 1) * 60:
        return True
    else:
        return False


# Method for handling entities in the message, if there is any
def entity_handler(message):
    for entity in message['entities']:
        if entity['type'] == 'bot_command':
            command = message['text'][entity['offset']:entity['offset'] + entity['length']]
            if command == '/create':
                create_account(message)
            elif command == '/freq':
                frequency_handler(message)
            elif command == '/del':
                delete_message(message)
            elif command == '/help':
                help(message['chat']['id'])


# Method for handling all kind of messages and routing them to correct method
def message_handler(message):
    if 'entities' in message.keys():
        entity_handler(message)


# Runs 'chat_needs_update()' method for every single chat created in database, if returns 'True', runs 'send_unique_post()' method
def update_handler():
    update_times = [0, 30]
    date = datetime.datetime.now()
    epoch = round(time.time())

    if date.minute in update_times:
        fetch_reddit()
        for chat in os.listdir(chats_path):
            try:
                path = chats_path + chat + '/'
                if os.path.isdir(path):
                    if chat_needs_update(chat, epoch):
                        send_unique_post(chat, epoch)
            except:
                pass
        time.sleep(60)


# Returns the last update id processed in the database
def update_id_handler(update_id=None):
    def set_update_id():
        if os.path.isfile('database/main_updates.csv'):
            if get_last_update_id() > update_id:
                return
            with open('database/main_updates.csv', 'a') as writecsv:
                writer = csv.DictWriter(writecsv, fieldnames=['update_id', 'date'], delimiter=';')
                writer.writerow({'update_id': update_id, 'date': datetime.datetime.now()})
                writecsv.close()
        else:
            with open('database/main_updates.csv', 'w') as writecsv:
                writer = csv.DictWriter(writecsv, fieldnames=['update_id', 'date'], delimiter=';')
                writer.writeheader()
                writer.writerow({'update_id': update_id, 'date': datetime.datetime.now()})
                writecsv.close()

    def get_last_update_id():
        last_update_id = 0
        with open('database/main_updates.csv', 'r') as readcsv:
            reader = csv.DictReader(readcsv, delimiter=';')
            for item in reader:
                last_update_id = int(item.get('update_id'))
            readcsv.close()
        return int(last_update_id)

    if update_id is not None:
        set_update_id()
    elif update_id is None:
        return get_last_update_id()


# Method for getting updates for bot, and sending the text in it to 'message_handler()' method. Also, updates the last update id
def get_updates():
    json_data = {
        "offset": update_id_handler() + 1,
    }
    send_url = URL + 'getUpdates'
    updates_bytes = requests.get(send_url, json=json_data)
    update_string = updates_bytes.content.decode('utf8')
    updates = json.loads(update_string)

    if updates['ok']:  # there is a new update or updates
        if len(updates['result']) > 0:
            for update in updates['result']:
                message_handler(update['message'])
                update_id_handler(update['update_id'])

    update_handler()  # check if it is time to update someone
    threading.Timer(1.0, get_updates).start()


if not os.path.isfile('database/main_updates.csv'):
    update_id_handler(0)
get_updates()