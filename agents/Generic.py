from agent_framework_redis import RedisHistoryProvider
from agent_framework import Agent, Message, Content
import asyncio
from utils.logger import get_logger
from config.settings import settings

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
                
                file_data = query.get("files", [None])[0]
                image_media_type = file_data.get("type") if isinstance(file_data, dict) else getattr(file_data, "type", "image/jpeg")
                image_data = file_data.get("data") if isinstance(file_data, dict) else getattr(file_data, "data", file_data)
                
                message=Message(
                    role='user',
                    contents=[
                        Content.from_text(query.get("text", "")),
                        Content.from_data(data=image_data,media_type=image_media_type)
                    ]
                )
            else:
                logger.info(f'[Generic Agent] No Files Detected in Query')
                
                message=Message(
                    role='user',
                    contents=[
                        Content.from_text(query.get("text", ""))
                    ]
                )
            instructions="""Your a Helpful AI assistant 
            - If you have file context information ,analyze the file before answering the query
            - Answer only from the given context, be simple and give accurate information 
            """
            redis_cache=RedisHistoryProvider(redis_url=settings.REDIS_URL,max_messages=8,source_id=session_id)
            logger.info(f'[Generic Agent] Redis Cache Initialized for session_id: {session_id}')
            
            agent=Agent(client=self.client,
                        instructions=instructions,
                        context_provider=[redis_cache]
            )
            
            logger.info(f'[Generic Agent] query started {query.text[:100]}...')

            async for event in agent.run(message,stream=True):
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

    
    