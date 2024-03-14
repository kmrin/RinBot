from rinbot.base.helpers import load_config, load_lang, format_exception
from rinbot.base.logger import logger
import google.generativeai as genai

config = load_config()
text = load_lang()

safety = [
    {
        "category": "HARM_CATEGORY_DANGEROUS",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]

genai.configure(api_key=config["AI_GEMINI_KEY"])

model = genai.GenerativeModel("gemini-pro", safety_settings=safety)

histories = {}
sessions = {}

def message(user="default", msg=None) -> str:
    if not msg:
        return text["GEMINI_MSG_NOT_PROVIDED"]
    
    if user not in histories.keys():
        histories[user] = []
        logger.info(f"{text['GEMINI_USER_HISTORY_CREATED']} {user}")
    
    if user not in sessions.keys():
        try:
            sessions[user] = model.start_chat(history=histories[user])
            logger.info(f"{text['GEMINI_USER_SESSION_CREATED']} {user}")
        except Exception as e:
            e = format_exception(e)
            logger.error(f"{text['GEMINI_ERROR_CREATING_SESSION']} (user: {user}): {e}")
            return text["GEMINI_ERROR_CREATING_SESSION"]
    
    chat: genai.ChatSession = sessions[user]
    
    try:
        response = chat.send_message(msg)
        histories[user] = chat.history
        return response.text
    except Exception as e:
        e = format_exception(e)
        logger.error(f"{text['GEMINI_RESPONSE_ERROR']}: {e}")
        return text["GEMINI_RESPONSE_ERROR"]

def reset(user):
    if user in histories.keys():
        histories.pop(user)
    if user in sessions.keys():
        sessions.pop(user)