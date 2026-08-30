# app/llm/message_mapper.py

from typing import Any

from app.models.messages import Message, MessageRole


def to_llm_message(
    messages: list[Message],
) -> list[dict[str, Any]]:
    """
    Преобразует сообщения из БД в формат OpenAI-compatible Chat Completions API.

    Ожидается, что Message.tools_calls загружен через selectinload().
    """

    result: list[dict[str, Any]] = []

    for message in messages:
        if message.role == MessageRole.SYSTEM:
            result.append(
                {
                    "role": "system",
                    "content": message.content or "",
                }
            )
            continue

        if message.role == MessageRole.USER:
            result.append(
                {
                    "role": "user",
                    "content": message.content or "",
                }
            )
            continue

        if message.role == MessageRole.ASSISTANT:
            if message.tools_calls:
                tool_calls: list[dict[str, Any]] = []

                for tool_call in message.tools_calls:
                    tool_call_data: dict[str, Any] = {
                        "id": tool_call.tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function_name,
                            "arguments": tool_call.arguments,
                        },
                    }

                    if tool_call.thought_signature:
                        tool_call_data["extra_content"] = {
                            "google": {
                                "thought_signature": tool_call.thought_signature,
                            }
                        }

                    tool_calls.append(tool_call_data)

                result.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": tool_calls,
                    }
                )
            else:
                result.append(
                    {
                        "role": "assistant",
                        "content": message.content or "",
                    }
                )

            continue

        if message.role == MessageRole.TOOL:
            if not message.tool_call_id:
                raise ValueError(
                    f"TOOL message {message.id} does not have tool_call_id"
                )

            result.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content or "",
                }
            )

            continue

        raise ValueError(f"Unsupported message role: {message.role}")

    return result
