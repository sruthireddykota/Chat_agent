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
    
class WorkflowType(str,Enum):
    SEQUENTIAL : str = "sequential"
    CONCURRENT : str = "concurrent"
    HANDOFF : str = "handoff"
    GROUPCHAT: str = "groupchat"

class Status(str,Enum):
    SUCCESS : str = "success"
    FAIL : str = "failed"
    NOTSTARTED : str = "notstarted"