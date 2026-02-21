from agent_framework import ChatAgent,ChatMessage, DataContent ,Role,ChatMessageStore
from agent_framework.redis import RedisChatMessageStore
import asyncio
from utils.logger import get_logger

logger=get_logger()

class Genericagent:
    def __init__(self):
        from azure_clients.azure_client import get_client
        self.client=get_client()
        
    async def generic_agent(self,query,session_id):
        
        try:
            has_files = bool(query.files) if hasattr(query,'files') else False
            
            if has_files:
                logger.info(f'[Generic Agent] Detected Files in Query')
                
                file_data=query.files[0]
                image_data=file_data.read()
                store=lambda:ChatMessageStore()
                logger.info(f'[Generic Agent] ChatMessage Store Initialised')
                
                message=ChatMessage(
                    role=Role.USER,
                    text=query.text,
                    contents=[DataContent(
                        media_type =file_data.type,
                        data=image_data
                    )]
                )
            else:
                logger.info(f'[Generic Agent] No Files Detected in Query')
                
                store=lambda:RedisChatMessageStore(
                    thread_id=f"session_{session_id}",
                    redis_url="redis://localhost:6379",
                    max_messages=5
                )
                
                logger.info(f'[Generic Agent] Redis Message Store Initialised with thread_id:{f"session_{session_id}"}')
                
                message=ChatMessage(
                    role=Role.USER,
                    text=query.text
                )
            instructions="""Your a Helpful AI assistant 
            - If you have file context information ,analyze the file before answering the query
            - Answer only from the given context, be simple and give accurate information 
            """
            agent=ChatAgent(chat_client=self.client,
                            instructions=instructions,
                            chat_message_store_factory=store)
            
            logger.info(f'[Generic Agent] query started {query.text[:100]}...')

            async for event in agent.run_stream(message):
                if hasattr(event, 'text') and event.text:
                    yield event.text
                    
        except Exception as e:
            logger.error(f'[Generic Agent] error: {e}')

def generic_executor(query, session_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async_gen = Genericagent().generic_agent(query, session_id)
    
    logger.info(f'[Generic Agent] query received {query.text[:100],session_id}...')

    try:
        while True:
            chunk = loop.run_until_complete(async_gen.__anext__())
            yield chunk
    except StopAsyncIteration:
        pass
    finally:
        
        logger.info(f'[Generic Agent] query completed {query.text[:100],session_id}...')
        loop.close()

    
    