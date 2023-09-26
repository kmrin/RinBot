"""
RinBot v1.4.3
feita por rin
"""

# Imports
from typing import Any, Dict, List
from langchain.memory.chat_memory import BaseChatMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage, ChatMessage

# Recebe uma mensagem base e converte em strings, representando uma conversa entre 'Humano' e 'IA'
def get_buffer_string(
    messages: List[BaseMessage], human_prefix: str = "Human", ai_prefix: str = "AI"
) -> str:
    string_messages = []
    
    # Itera sob a lista de mensagens e adiciona elas na lista de strings
    # adicionando um prefixo
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

# Cria uma janela de buffer personalizada para o chatbot
class CustomBufferWindowMemory(BaseChatMemory):
    ai_prefix: str = "AI"        # Prefixo da IA
    memory_key: str = "history"  # Chave para guardar o histórico na memória
    k: int = 5                   # Tamanho do buffer

    @property
    def buffer(self) -> List[BaseMessage]:
        return self.chat_memory.messages

    @property
    def memory_variables(self) -> List[str]:
        return [self.memory_key]

    # Adiciona uma entrada humana na memória
    def add_input_only(self, input_str: str) -> None:
        self.chat_memory.messages.append(HumanMessage(content=input_str))

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        buffer: Any = self.buffer[-self.k * 2 :] if self.k > 0 else []
        buffer = get_buffer_string(
            buffer,
            human_prefix="",
            ai_prefix=self.ai_prefix,)
        return {self.memory_key: buffer}