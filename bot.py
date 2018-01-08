import telebot
import config
import aiml
from clarifai.rest import ClarifaiApp

# image tagging side-service
clarifai_api = ClarifaiApp(api_key=config.clarifai_key)
model = clarifai_api.models.get("general-v1.3")

aiml_path_ru = 'aiml-ru/'
aiml_path_en = 'aiml-en/'

kernel = aiml.Kernel()


def load_kernel(learn_file):
    kernel.bootstrap(learnFiles=learn_file, commands="LOAD AIML BOT")


load_kernel(aiml_path_en + "std-startup.xml")
bot = telebot.TeleBot(config.token)

LANG_KEY_CLARIFAI = 'en'


@bot.message_handler(commands=['start'])
def start(message):
    msg = 'Hello, ' + message.from_user.first_name + "\nDefault language is English. Command /switchlang will set it to Russian"
    bot.reply_to(message, msg)


@bot.message_handler(commands=['switchlang'])
def switchlang(message):
    global LANG_KEY_CLARIFAI
    config.lang_en = not config.lang_en
    if config.lang_en:
        load_kernel(aiml_path_en + "std-startup.xml")
        LANG_KEY_CLARIFAI = 'en'
    else:
        load_kernel(aiml_path_ru + "std-startup.xml")
        LANG_KEY_CLARIFAI = 'ru'


    kernel.setPredicate("name", message.from_user.first_name)


@bot.message_handler(func=lambda message: True, content_types=["text"])
def echo(message):
    kernel.setPredicate("name", message.from_user.first_name)
    input_text = message.text
    response = kernel.respond(input_text)
    print("Message:\n{}\nresponse:\n{}".format(input_text, response))
    bot.send_message(message.chat.id, response)


@bot.message_handler(content_types=['photo'])
def picture_handler(message):
    # print('message.photo =', message.photo)
    fileID = message.photo[-1].file_id
    # print('fileID =', fileID)
    file_info = bot.get_file(fileID)
    # print("file info:", file_info)
    file_path = "https://api.telegram.org/file/bot{}/{}".format(config.token, file_info.file_path)

    res = model.predict_by_url(url=file_path, lang=LANG_KEY_CLARIFAI)
    tags = res['outputs'][0]['data']['concepts']
    answer = "Думаю на этой картинке:\n"
    if config.lang_en:
        answer = "I guess here:\n"
    for tag in tags[:5]:
        answer += "{}: {:.2%}\n".format(tag["name"], tag["value"])
    bot.send_message(message.chat.id, answer)


if __name__ == '__main__':
    bot.polling(none_stop=True)
