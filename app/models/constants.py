from enum import Enum

class Role(str,Enum):
    USER :str= "user"
    ASSISTANT :str= "assistant"
    SYSTEM :str= "system"

class AgentType(str,Enum):
    CODER :str = "coder"
    GENERIC :str= "generic"
    RESEARCHER :str= "researcher"
    RAG :str= "rag"