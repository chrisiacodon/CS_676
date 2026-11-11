# CS676 Project 2 - PersonaForge
# Tests for the orchestrator and intelligent intent routing.
#
# Baseline: 39 original tests passed.
# Added test_create_persona: PASSED.
# Added test_natural_language_persona_creation: FAILS
# under the original regex-based router.
#
# Goal: Replace regex routing with Claude tool calling.

import copy
import pytest

from personaforge.orchestrator import Orchestrator
from personaforge.llm import DemoLLM


def test_create_persona(tmp_path):
    """Test that the orchestrator creates and saves a persona."""

    # Create an offline model so no API key is needed.
    llm = DemoLLM()

    # Use a temporary directory for test files.
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path
    )

    # Ask the orchestrator to create a patient.
    result = orchestrator.handle(
        "create a persona patient with chronic back pain"
    )

    # Check that the persona was created successfully.
    assert "Created" in result.reply

    # Check that a Markdown file was saved.
    persona_files = list(tmp_path.glob("*.md"))
    assert len(persona_files) == 1



def test_natural_language_persona_creation(tmp_path):
    """Test natural-language creation through Claude-style tool calling."""

    from types import SimpleNamespace

    class FakeNaturalLanguageLLM(DemoLLM):
        def __init__(self):
            super().__init__()
            self.call_count = 0

        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            self.call_count += 1

            if self.call_count == 1:
                return SimpleNamespace(
                    stop_reason="tool_use",
                    content=[
                        SimpleNamespace(
                            type="tool_use",
                            id="tool_ada",
                            name="create_persona",
                            input={
                                "description":
                                    "a skeptical scientist named Ada "
                                    "who questions everything"
                            },
                        )
                    ],
                )

            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(
                        type="text",
                        text="Created a skeptical scientist named Ada.",
                    )
                ],
            )

    llm = FakeNaturalLanguageLLM()

    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    result = orchestrator.handle(
        "Invent a skeptical scientist named Ada who questions everything"
    )

    assert "Created" in result.reply
    assert len(list(tmp_path.glob("*.md"))) == 1
    assert llm.call_count == 2



def test_claude_tool_calling():
    """Verify that Claude receives the available tool definitions."""
    from unittest.mock import MagicMock
    from personaforge.llm import ClaudeLLM

    # Create a fake Claude API client.
    fake_client = MagicMock()
    fake_client.messages.create.return_value.stop_reason = "tool_use"

    # Inject the fake client so no real API call occurs.
    llm = ClaudeLLM(model="test-model")
    llm._client = fake_client

    tools = [
        {
            "name": "create_persona",
            "description": "Create a new persona",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"}
                },
                "required": ["description"]
            }
        }
    ]

    response = llm.complete_with_tools(
        system="You are a persona manager.",
        messages=[
            {
                "role": "user",
                "content": "Invent a scientist named Ada"
            }
        ],
        tools=tools,
    )

    assert response.stop_reason == "tool_use"

    fake_client.messages.create.assert_called_once()

    arguments = fake_client.messages.create.call_args.kwargs
    assert arguments["tools"] == tools
    assert arguments["model"] == "test-model"


def test_orchestrator_executes_tool_call(tmp_path):
    """Test that the orchestrator executes Claude's tool request."""
    from types import SimpleNamespace
    from personaforge.llm import DemoLLM

    class FakeToolLLM(DemoLLM):
        def __init__(self):
            super().__init__()
            self.tool_calls = 0

        def complete_with_tools(self, system, messages, tools, max_tokens=2048):
            self.tool_calls += 1

            if self.tool_calls == 1:
                return SimpleNamespace(
                    stop_reason="tool_use",
                    content=[
                        SimpleNamespace(
                            type="tool_use",
                            id="tool_1",
                            name="create_persona",
                            input={
                                "description": "a skeptical scientist named Ada"
                            },
                        )
                    ],
                )

            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(
                        type="text",
                        text="The scientist persona has been created.",
                    )
                ],
            )

    llm = FakeToolLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    result = orchestrator.handle(
        "Invent a skeptical scientist named Ada who questions everything"
    )

    assert result.reply == "The scientist persona has been created."
    assert len(list(tmp_path.glob("*.md"))) == 1
    assert llm.tool_calls == 2

 
def test_multiple_tool_calls(tmp_path):
    """Test executing two persona creation tools in one response."""
    from types import SimpleNamespace
    from personaforge.llm import DemoLLM

    class FakeMultiToolLLM(DemoLLM):
        def __init__(self):
            super().__init__()
            self.tool_calls = 0

        def complete_with_tools(self, system, messages, tools, max_tokens=2048):
            self.tool_calls += 1

            if self.tool_calls == 1:
                return SimpleNamespace(
                    stop_reason="tool_use",
                    content=[
                        SimpleNamespace(
                            type="tool_use",
                            id="tool_1",
                            name="create_persona",
                            input={"description": "scientist named Ada"},
                        ),
                        SimpleNamespace(
                            type="tool_use",
                            id="tool_2",
                            name="create_persona",
                            input={"description": "doctor named James"},
                        ),
                    ],
                )

            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(
                        type="text",
                        text="Both personas have been created.",
                    )
                ],
            )

    llm = FakeMultiToolLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    result = orchestrator.handle(
        "Create a scientist named Ada and a doctor named James"
    )

    assert result.reply == "Both personas have been created."
    assert len(list(tmp_path.glob("*.md"))) == 2
    assert len(result.events) == 2
    assert llm.tool_calls == 2


def test_unknown_tool(tmp_path):
    """Test that an unknown tool returns an error without crashing."""

    llm = DemoLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    result = orchestrator._execute_tool(
        name="delete_everything",
        arguments={},
    )

    assert result.reply == "Unknown tool: delete_everything"
    assert result.events == []


def test_conversation_with_missing_persona(tmp_path):
    """Test that missing personas produce a helpful error."""

    llm = DemoLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    result = orchestrator._execute_tool(
        name="start_conversation",
        arguments={
            "topic": "the diagnosis",
            "who": ["Dr. Smith", "Patient Jane"],
            "turns": 6,
        },
    )

    assert "couldn't find a persona" in result.reply
    assert result.conversation is None


def test_tool_calling_api_failure(tmp_path):
    """Test that an API failure produces a helpful response."""

    class FailingLLM:
        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            raise ConnectionError("Simulated API connection failure")

    orchestrator = Orchestrator(
        llm=FailingLLM(),
        persona_dir=tmp_path,
    )

    result = orchestrator.handle(
        "Create a scientist named Ada"
    )

    assert "unable to contact" in result.reply.lower()
    assert result.conversation is None

def test_conversation_memory(tmp_path):
    """Verify that previous instructions are remembered."""

    from types import SimpleNamespace
    from personaforge.llm import DemoLLM

    class FakeMemoryLLM(DemoLLM):
        def __init__(self):
            super().__init__()
            self.received_messages = []

        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            # Record the messages received on each call.
            self.received_messages.append(copy.deepcopy(messages))

            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(
                        type="text",
                        text="Understood.",
                    )
                ],
            )

    llm = FakeMemoryLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    # First instruction.
    orchestrator.handle("Create a scientist named Ada")

    # Second instruction.
    orchestrator.handle("Now create someone who disagrees with her")

    # Verify the second request includes the first.
    second_request = llm.received_messages[1]
    print("\nSECOND REQUEST:")
    for index, message in enumerate(second_request):
        print(index, message)

    assert second_request[0] == {
        "role": "user",
        "content": "Create a scientist named Ada",
    }

    assert second_request[-1] == {
        "role": "user",
        "content": "Now create someone who disagrees with her",
    }

    assert len(second_request) == 3


def test_tool_result_memory(tmp_path):
    """Verify that tool requests and results persist across instructions."""

    from types import SimpleNamespace
    from personaforge.llm import DemoLLM

    class FakeToolMemoryLLM(DemoLLM):
        def __init__(self):
            super().__init__()
            self.requests = []

        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            import copy
            self.requests.append(copy.deepcopy(messages))

            if len(self.requests) == 1:
                return SimpleNamespace(
                    stop_reason="tool_use",
                    content=[
                        SimpleNamespace(
                            type="tool_use",
                            id="tool_ada",
                            name="create_persona",
                            input={"description": "scientist named Ada"},
                        )
                    ],
                )

            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(
                        type="text",
                        text="Understood.",
                    )
                ],
            )

    llm = FakeToolMemoryLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    # First instruction creates Ada.
    orchestrator.handle("Create a scientist named Ada")

    # Second instruction refers to the earlier action.
    orchestrator.handle("Now create someone who disagrees with her")

    # The third API request should include the first tool exchange.
    history = llm.requests[2]

    tool_requests = [
        block
        for message in history
        if message["role"] == "assistant"
        and isinstance(message["content"], list)
        for block in message["content"]
        if getattr(block, "type", None) == "tool_use"
    ]

    tool_results = [
        block
        for message in history
        if message["role"] == "user"
        and isinstance(message["content"], list)
        for block in message["content"]
        if isinstance(block, dict)
        and block.get("type") == "tool_result"
    ]

    assert len(tool_requests) == 1
    assert tool_requests[0].name == "create_persona"

    assert len(tool_results) == 1
    assert tool_results[0]["tool_use_id"] == "tool_ada"


def test_history_limit(tmp_path):
    """Keep only the 10 most recent complete interactions."""

    from types import SimpleNamespace
    from personaforge.llm import DemoLLM

    class FakeHistoryLLM(DemoLLM):
        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(
                        type="text",
                        text="Understood.",
                    )
                ],
            )

    llm = FakeHistoryLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    # Send 15 separate user instructions.
    for i in range(15):
        orchestrator.handle(f"Instruction {i}")

    # Extract the user instructions retained in history.
    user_messages = [
        message["content"]
        for message in orchestrator.tool_history
        if message["role"] == "user"
        and isinstance(message["content"], str)
    ]

    assert len(user_messages) == 10
    assert user_messages[0] == "Instruction 5"
    assert user_messages[-1] == "Instruction 14"


def test_history_trimming_preserves_tool_pairs(tmp_path):
    """Ensure trimming keeps tool requests with their results."""

    from types import SimpleNamespace
    from personaforge.llm import DemoLLM

    class FakeToolHistoryLLM(DemoLLM):
        def __init__(self):
            super().__init__()
            self.call_count = 0

        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            self.call_count += 1

            # Request a tool on every odd-numbered API call.
            if self.call_count % 2 == 1:
                return SimpleNamespace(
                    stop_reason="tool_use",
                    content=[
                        SimpleNamespace(
                            type="tool_use",
                            id=f"tool_{self.call_count}",
                            name="list_personas",
                            input={},
                        )
                    ],
                )

            return SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    SimpleNamespace(
                        type="text",
                        text="Personas listed.",
                    )
                ],
            )

    llm = FakeToolHistoryLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    # Run 15 complete interactions.
    for i in range(15):
        orchestrator.handle(f"List personas, request {i}")

    history = orchestrator.tool_history

    # Collect tool request IDs.
    request_ids = [
        block.id
        for message in history
        if message["role"] == "assistant"
        and isinstance(message["content"], list)
        for block in message["content"]
        if getattr(block, "type", None) == "tool_use"
    ]

    # Collect corresponding tool result IDs.
    result_ids = [
        block["tool_use_id"]
        for message in history
        if message["role"] == "user"
        and isinstance(message["content"], list)
        for block in message["content"]
        if isinstance(block, dict)
        and block.get("type") == "tool_result"
    ]

    assert len(request_ids) == 10
    assert request_ids == result_ids


def test_stage_manager_prompt_prevents_duplicate_dialogue():
    """Check that the stage manager is instructed not to repeat dialogue."""

    from personaforge.orchestrator import _STAGE_MANAGER_SYSTEM

    prompt = _STAGE_MANAGER_SYSTEM.lower()

    assert "do not generate another" in prompt
    assert "conversation" in prompt
    assert "short summary" in prompt


def test_anthropic_authentication_error(tmp_path):
    """Verify that an invalid API key produces a helpful message."""

    import httpx
    from anthropic import AuthenticationError

    class FailingAuthLLM:
        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            request = httpx.Request(
                "POST",
                "https://api.anthropic.com/v1/messages",
            )

            response = httpx.Response(
                status_code=401,
                request=request,
                json={
                    "error": {
                        "type": "authentication_error",
                        "message": "invalid x-api-key",
                    }
                },
            )

            raise AuthenticationError(
                "Invalid API key",
                response=response,
                body=response.json(),
            )

    orchestrator = Orchestrator(
        llm=FailingAuthLLM(),
        persona_dir=tmp_path,
    )

    result = orchestrator.handle(
        "Create a scientist named Ada"
    )

    assert "authentication failed" in result.reply.lower()
    assert "api key" in result.reply.lower()
    assert result.conversation is None


def test_anthropic_rate_limit_error(tmp_path):
    """Verify that API rate limits produce a helpful message."""

    import httpx
    from anthropic import RateLimitError

    class FailingRateLimitLLM:
        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            request = httpx.Request(
                "POST",
                "https://api.anthropic.com/v1/messages",
            )

            response = httpx.Response(
                status_code=429,
                request=request,
                json={
                    "error": {
                        "type": "rate_limit_error",
                        "message": "Rate limit exceeded",
                    }
                },
            )

            raise RateLimitError(
                "Rate limit exceeded",
                response=response,
                body=response.json(),
            )

    orchestrator = Orchestrator(
        llm=FailingRateLimitLLM(),
        persona_dir=tmp_path,
    )

    result = orchestrator.handle(
        "Create a scientist named Ada"
    )

    assert "rate limit" in result.reply.lower()
    assert "wait" in result.reply.lower()
    assert result.conversation is None


def test_anthropic_connection_error(tmp_path):
    """Verify that an Anthropic connection failure is handled."""

    import httpx
    from anthropic import APIConnectionError

    class FailingConnectionLLM:
        def complete_with_tools(
            self, system, messages, tools, max_tokens=2048
        ):
            request = httpx.Request(
                "POST",
                "https://api.anthropic.com/v1/messages",
            )

            raise APIConnectionError(
                message="Connection failed",
                request=request,
            )

    orchestrator = Orchestrator(
        llm=FailingConnectionLLM(),
        persona_dir=tmp_path,
    )

    result = orchestrator.handle(
        "Create a scientist named Ada"
    )

    assert "unable to connect" in result.reply.lower()
    assert "internet connection" in result.reply.lower()
    assert result.conversation is None


def test_invalid_conversation_turns(tmp_path):
    """Reject a conversation request with zero turns."""

    llm = DemoLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    result = orchestrator._execute_tool(
        name="start_conversation",
        arguments={
            "topic": "scientific discovery",
            "turns": 0,
        },
    )

    assert "turns must be between 1 and 20" in result.reply.lower()
    assert result.conversation is None


def test_invalid_participant_names(tmp_path):
    """Reject participant names supplied in the wrong format."""

    llm = DemoLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    result = orchestrator._execute_tool(
        name="start_conversation",
        arguments={
            "topic": "scientific discovery",
            "who": "Ada Chen",
            "turns": 6,
        },
    )

    assert "participants must be a list" in result.reply.lower()
    assert result.conversation is None


def test_invalid_conversation_topic(tmp_path):
    """Reject an empty conversation topic."""

    llm = DemoLLM()
    orchestrator = Orchestrator(
        llm=llm,
        persona_dir=tmp_path,
    )

    result = orchestrator._execute_tool(
        name="start_conversation",
        arguments={
            "topic": "",
            "turns": 6,
        },
    )

    assert "topic must be a non-empty string" in result.reply.lower()
    assert result.conversation is None
