import google.generativeai as genai

class GeminiClient:
    def __init__(self, key: str) -> None:
        genai.configure(api_key=key)
        
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
        
        self.model = genai.GenerativeModel('gemini-pro', safety_settings=safety)
        self.histories = {}
        self.sessions = {}
    
    def message(self, msg: str, user: str = 'default') -> str:
        if user not in self.histories.keys():
            self.histories[user] = []
        
        if user not in self.sessions.keys():
            self.sessions[user] = self.model.start_chat(history=self.histories[user])
        
        chat: genai.ChatSession = self.sessions[user]
        
        response = chat.send_message(msg)
        self.histories[user] = chat.history
        
        return response.text
    
    def reset(self, user: str) -> None:
        if user in self.histories.keys():
            self.histories.pop(user)
        if user in self.sessions.keys():
            self.sessions.pop(user)
