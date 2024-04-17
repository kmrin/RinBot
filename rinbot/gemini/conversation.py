import google.generativeai as genai

from rinbot.base import log_exception
from rinbot.base import logger
from rinbot.base import text, conf

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

genai.configure(api_key=conf["AI_GEMINI_KEY"])

model = genai.GenerativeModel("gemini-pro", safety_settings=safety)

histories = {}
sessions = {}

def message(user="default", msg: str=None) -> str:    
    if user not in histories.keys():
        histories[user] = []
        logger.info(f"{text['GEMINI_USER_HISTORY_CREATED']} {user}")
    
    if user not in sessions.keys():
        try:
            sessions[user] = model.start_chat(history=histories[user])
            logger.info(f"{text['GEMINI_USER_SESSION_CREATED']} {user}")
        except Exception as e:
            log_exception(e)
            return text["GEMINI_ERROR_CREATING_SESSION"]
    
    chat: genai.ChatSession = sessions[user]
    
    try:
        response = chat.send_message(msg)
        histories[user] = chat.history
        return response.text
    except Exception as e:
        log_exception(e)
        return text["GEMINI_RESPONSE_ERROR"]

def reset(user):
    if user in histories.keys():
        histories.pop(user)
    if user in sessions.keys():
        sessions.pop(user)
