from agent_framework import HostedCodeInterpreterTool,ChatAgent,ChatMessageStore,ChatMessage,Role,DataContent
from agent_framework.redis import RedisChatMessageStore
from utils.logger import get_logger
import asyncio


logger=get_logger()


class Codeagent:
    
    def __init__(self):
        from azure_clients.azure_client import get_client
        self.client=get_client()
        self.instructions=self._get_instruction()
        
        
    async def coder_agent(self,query,session_id):
        
        try:
            is_files= bool(query.files) if hasattr(query, 'files') else False
            
            if is_files:
                logger.info(f'[Coder Agent] Detected Files in Query')
                
                file_data=query.files[0]
                image_data=file_data.read()
                
                if file_data.type.startswith("text/"):
                    
                    store=lambda:RedisChatMessageStore(
                        redis_url="redis://localhost:6379",
                        max_messages=5,
                        thread_id=f"session_{session_id}")
                    
                    logger.info(f'[Coder Agent] Redis Message Store Initialised with thread_id:{f"session_{session_id}"}')
                    
                    code = image_data.decode("utf-8")
                    
                    message=ChatMessage(
                        role=Role.USER,
                        text=f"Query: {query.text}, ```python\n{code}\n```"
                    )
                    
                else:
                    logger.info(f'[Coder Agent] No Files Detected in Query')
                    store=lambda:ChatMessageStore()
                    logger.info(f'[Coder Agent] ChatMessage Store Initialised')
                    
                    media_type = file_data.type
                    message=ChatMessage(
                        role=Role.USER,
                        text=query.text,
                        contents=[DataContent(
                            media_type=media_type,
                            data=image_data
                        )
                        ]
                    )
            else:
                store=lambda:RedisChatMessageStore(
                    redis_url="redis://localhost:6379",
                    max_messages=5,
                    thread_id=f"session_{session_id}"
                )
                message=ChatMessage(
                    role=Role.USER,
                    text=query.text
                )
            
            agent=ChatAgent(chat_client=self.client,
                            instructions=self.instructions,
                            tools=[HostedCodeInterpreterTool()],
                            chat_message_store_factory=store)
            
            logger.info(f'[Coder Agent] query received: {query.text[:100]}')
            
            async for event in agent.run_stream(message):
                if hasattr(event, 'delta') and event.delta:
                    yield event.delta
                elif hasattr(event, 'content') and event.content:
                    yield event.content
                elif hasattr(event, 'text') and event.text:
                    yield event.text
        
        except Exception as e:
            logger.error(f"[Coder Agent] error : {e}")

    def _get_instruction(self):
        instructions= """You are a helpful AI coding assistant with access to a code interpreter.

    ## Response Structure:
    Format your responses with clear sections using markdown headers:

    1. **Summary**: Brief explanation of what you did
    2. **Code Analysis**: If analyzing code, list findings with severity levels
    3. **Solution**: Provide code fixes in ```python blocks
    4. **Execution**: Show any code execution results in ``` blocks
    5. **Next Steps**: Suggest improvements or further actions

    ## Formatting Rules:
    - Use `inline code` for variable names, function names, and short snippets
    - Use ```python blocks for code that spans multiple lines
    - Use **bold** for important warnings or critical issues
    - Use bullet points for lists of issues or recommendations
    - Use > blockquotes for important notes or warnings

    ## Tool Usage:
    - Use HostedCodeInterpreterTool to execute code when:
    - User asks to run/test code
    - You need to verify a solution works
    - Analysis requires runtime information (e.g., performance testing)

    ## Behavior:
    - If file provided: Analyze it thoroughly before responding
    - If query + file: Use file as context but answer the specific query
    - If only file: Provide comprehensive analysis without being asked
    """
        return instructions
    
def coder_executor(query, session_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger= get_logger()
    logger.info(f'[Coder Agent] query started: {query.text[:100],session_id}')
    async_gen = Codeagent().coder_agent(query, session_id)

    try:
        while True:
            chunk = loop.run_until_complete(async_gen.__anext__())
            yield chunk
    except StopAsyncIteration:
        pass
    finally:
        logger.info(f'[Coder agent] query completed: {query.text[:100],session_id}')
        loop.close()
