from constants import FEED_CHANNEL_ID, FEED_CHAT_ID
from form import FormToRequestString

def send_form_to_channel(bot, form):
    text = FormToRequestString(form)
    print(text)
    message = bot.send_photo(FEED_CHANNEL_ID, photo=open("public/OpenRequestPepe.jpg", 'rb'), caption=text, parse_mode="Markdown")
    return message
    #bot.send_message(FEED_CHAT_ID, "Если вы готовы взяться за эту задачу, напишите /takeon", reply_to_message_id=request.id)
