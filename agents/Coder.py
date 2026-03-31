import asyncio

from pathlib import Path
from typing import Dict
from agent_framework_redis import RedisHistoryProvider
from agent_framework import Agent, Message, Content, SkillsProvider

from utils.logger import get_logger
from utils.script_runner import script_runner
from config.settings import settings

logger = get_logger()

class CoderAgent:

    def __init__(self):
        from azure_clients.azure_client import get_client
        self.client = get_client()

    async def coder_agent(self, query: Dict, session_id: str):
        try:
            has_files = bool(query.get("files"))

            if has_files:
                logger.info(f'[Coder Agent] Detected Files in Query')
                file_data = query.get("files", [None])[0]
                image_media_type = file_data.get("type") if isinstance(file_data, dict) else getattr(file_data, "type", "image/jpeg")
                image_data = file_data.get("data") if isinstance(file_data, dict) else getattr(file_data, "data", file_data)
                message = Message(
                    role='user',
                    text=query.get("text", ""),
                    contents=[
                        Content.from_text(query.get("text", "")),
                        Content.from_data(data=image_data, media_type=image_media_type)
                    ]
                )
            else:
                logger.info(f'[Coder Agent] No Files Detected in Query')
                message = Message(
                    role='user',
                    contents=[Content.from_text(query.get("text", ""))]
                )

            instructions = """
You are a helpful coding agent specializing in Python and SQL.
You fix bugs, review code, and produce output that is deployed directly — quality is critical.

**CRITICAL RULES: How to use skills (ALL MUST FOLLOW):**
- Call load_skill('skill-name') to get full instructions before any coding task
- Call read_skill_resource('skill-name/references/file.md') to read standards and patterns
- Call run_skill_script('skill-name', 'scripts/script-name.py', args={}) to run checks
- Always use the provided templates for writing new code or tests

#CRITICAL RUlE 2: Always use provided skills and never write code without them. They contain essential standards and checks. -> No Exceptions -> If not followed you have failed.

**How to use python-coding skill:**

For writing new Python code:
  1. load_skill('python-coding')
  2. read_skill_resource('python-coding/references/CODING_STANDARDS.md')
  3. read_skill_resource('python-coding/assets/module-template.py')
  4. Write code following the standards exactly

For debugging Python errors — provide traceback as input:
  run_skill_script('python-coding', 'scripts/analyze_traceback.py',
  args={'input': '<paste traceback here>'})

For reviewing Python code — provide code as input:
  run_skill_script('python-coding', 'scripts/lint_check.py',
  args={'input': '<paste code here>'})

For generating tests:
  1. read_skill_resource('python-coding/references/TEST_STANDARDS.md')
  2. read_skill_resource('python-coding/assets/test-template.py')
  3. Generate tests covering happy path, edge cases, and error cases
**How to use sql-coding skill:**

For writing new SQL queries:
  1. load_skill('sql-coding')
  2. read_skill_resource('sql-coding/references/SQL_STANDARDS.md')
  3. read_skill_resource('sql-coding/references/QUERY_PATTERNS.md')
  4. Write the query following standards
  5. Validate by passing the query directly as input string:
     run_skill_script('sql-coding', 'scripts/validate_query.py',
     args={'input': '<your complete sql query as a single string>'})
  6. If validation returns MUST FIX issues, fix them and re-validate
  7. Only return the query after validation passes

For debugging SQL errors:
  1. read_skill_resource('sql-coding/references/ERROR_PATTERNS.md')
  2. run_skill_script('sql-coding', 'scripts/validate_query.py',
     args={'input': '<paste the broken sql here as a single string>'})

For optimizing slow queries:
  1. read_skill_resource('sql-coding/references/OPTIMIZATION.md')
  2. Analyze query structure and return optimized version with index recommendations

For schema design or migrations:
  1. read_skill_resource('sql-coding/references/SCHEMA_STANDARDS.md')
  2. read_skill_resource('sql-coding/assets/migration-template.sql')
  3. Return CREATE TABLE statements and migration script

**Important — passing input to scripts:**
- The 'input' key in args must contain the actual content as a plain string
- Pass the full SQL or traceback text directly — do not use file paths or placeholders
- Newlines in the string are fine — pass the query exactly as written
- Example: args={'input': 'select id from users where deleted_at = null'}

**Response structure:**
1. Summary — what you did and why
2. Script output — if you ran a skill script, show its output
3. Solution — fixed or new code in fenced blocks
4. Issues found — severity grouped: Must fix / Should fix / Consider
5. Next steps — what to do after applying this fix

**Critical rules:**
- Always load the relevant skill before writing or reviewing any code
- Always pass actual code/SQL content in the 'input' arg — never placeholders
- Run validate_query.py or lint_check.py AFTER generating the code, 
  passing the generated code as the input value
- Never call a validation script before the code exists
- Never return code that has MUST FIX issues from the linter
- Code goes directly to deployment — do not skip quality checks
"""

            coder_skills = SkillsProvider(
                skill_paths=[Path(__file__).parent.parent / "skills"],
                script_runner=script_runner,
            )

            redis_cache = RedisHistoryProvider(
                redis_url=settings.REDIS_URL,
                source_id=session_id,
                max_messages=8
            )

            agent = Agent(
                client=self.client,
                instructions=instructions,
                tools=[self.client.get_code_interpreter_tool()],
                context_providers=[coder_skills, redis_cache],
                default_options={
                    'temperature': 0.2,
                    'top_p': 0.9,
                    'max_tokens': 1500
                }
            )
            logger.info(f'[Coder Agent] query started: {query.get("text", "")[:100]}')
            async for event in agent.run(message, stream=True):
                if event.text:
                    yield event.text
                    

        except Exception as e:
            logger.error(f'[Coder Agent] error: {e}', exc_info=True)
            raise e
        
def coder_executor(query, session_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger= get_logger()
    logger.info(f'[Coder Agent] query started: {query.text[:100],session_id}')
    async_gen = CoderAgent().coder_agent(query, session_id)

    try:
        while True:
            chunk = loop.run_until_complete(async_gen.__anext__())
            yield chunk
    except StopAsyncIteration:
        pass
    finally:
        logger.info(f'[Coder agent] query completed: {query.text[:100],session_id}')
        loop.close()
