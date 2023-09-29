"""
RinBot v1.5.1 (GitHub release)
made by rin
"""

# Imports
from typing import Any, Dict, List
from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage, ChatMessage

# Receives a base message then converts everything into individual strings representing two sides, 'Human' and 'AI'
def get_buffer_string(
    messages: List[BaseMessage], human_prefix: str = "Human", ai_prefix: str = "AI"
) -> str:
    string_messages = []
    
    # Iterates through a message list and adds them to the new strings list with a prefix
    for m in messages:
        if isinstance(m, HumanMessage):
            role = human_prefix
        elif isinstance(m, AIMessage):
            role = ai_prefix
        elif isinstance(m, SystemMessage):
            role = "System"
        elif isinstance(m, ChatMessage):
            role = m.role
        else:
            raise ValueError(f"Tipo de mensagem não suportada: {m}")
        if role == human_prefix:
            string_messages.append(f"{m.content}")
        else:
            string_messages.append(f"{role}: {m.content}")
    return "\n".join(string_messages)

# Creates a buffer window for the chatbot
class CustomBufferWindowMemory(BaseChatMemory):
    ai_prefix: str = "AI"        # AI prefix (what appears on the messages)
    memory_key: str = "history"  # Key to store the history in memory
    k: int = 5                   # Buffer size

    @property
    def buffer(self) -> List[BaseMessage]:
        return self.chat_memory.messages

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]

    # Adds a human input to memory
    def add_input_only(self, input_str: str) -> None:
        self.chat_memory.messages.append(HumanMessage(content=input_str))

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        buffer: Any = self.buffer[-self.k * 2 :] if self.k > 0 else []
        buffer = get_buffer_string(
            buffer,
            human_prefix="",
            ai_prefix=self.ai_prefix,)
        return {self.memory_key: buffer}