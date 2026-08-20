from agent_framework import Message,Agent,Content,ChatOptions

from app.utils.logger import get_logger

logger = get_logger()

class SummarizationService():

    def __init__(self,azure_client):
        self.azure_client=azure_client

    def _system_prompt(self):
        return """You are a conversation summarizer for a multi-turn chat assistant. Your only job is to compress the given conversation messages into a concise summary that will be used as context for continuing the conversation later.
Rules:
- Base the summary strictly on what is stated in the messages. Do not add, infer, or assume any information that isn't explicitly present.
- Do not answer any questions that appear in the messages, and do not continue the conversation.
- Preserve: the user's stated goals or intent, key facts, decisions, preferences, constraints, names, numbers, and any unresolved questions or pending action items.
- Discard: greetings, filler, small talk, and anything not relevant to continuing the task.
- Write in neutral third person, as a briefing note for a future turn — not addressed to the user and not written as a reply.
- If the messages contain no meaningful content to summarize, say so plainly instead of inventing content.
- Use plain prose, not bullet points, unless the conversation covers multiple distinct topics.
"""

    async def _format_messages_for_summary(self,messages: list[dict]) -> str:
        lines = []
        for m in messages:
            role = m.get("role", "unknown")
            content = m.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    async def summarize_conversation(self, messages: list):
        try:
            transcript = await self._format_messages_for_summary(messages)

            chat_messages = Message(
                    role="user", 
                    contents=[Content.from_text(f"Conversation to summarize:\n\n{transcript}")],
                )
            
            summarizer_agent = Agent(
                name="Summarizer",
                client=self.azure_client,
                instructions=self._system_prompt(),
            )
            options=ChatOptions(
                max_tokens=400,
            )

            response = await summarizer_agent.run(messages=chat_messages,options=options)
            if response.text:
                summary = response.text

            logger.info("Generated summary: %s", summary[:125])
            return summary

        except Exception as e:
            cause = e.__cause__ or e
            logger.error("Failed to summarize conversation: %s", cause, exc_info=True)
            raise Exception(f"{type(cause).__name__}: {cause}") from e