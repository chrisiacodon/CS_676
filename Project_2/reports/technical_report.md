# PersonaForge: Intelligent Orchestration for Agent-to-Agent Conversations

**CS676 — Algorithms for Data Science**  
**Pace University**  
**Project 2 — Technical Report**

## 1. Introduction

PersonaForge is a Python package that allows users to create fictional personas and simulate conversations between them using large language models (LLMs). Each persona is represented by a Markdown file containing identifying information, background, personality, and behavioral instructions. These files are used to construct prompts that guide the model's behavior during conversations.

The original application used regular expressions to interpret user commands. Although this approach worked for a limited set of predefined phrases, it was inflexible and could not reliably interpret more complex natural-language instructions.

The primary objective of this project was to replace the original command-routing mechanism with an intelligent orchestrator using Anthropic Claude's native tool-calling capabilities.

Rather than attempting to implement every possible extension, I focused on improving the orchestrator, preserving compatibility with the original application, and evaluating its behavior through automated testing and live experiments.

## 2. System Design and Implementation

### 2.1 Original Architecture

PersonaForge consists of several interacting components:

- `persona.py` manages the creation, storage, and retrieval of personas.
- `agent.py` converts persona descriptions into instructions for an LLM.
- `conversation.py` manages turn-taking and records conversations.
- `llm.py` provides the interface to Anthropic Claude and simulated models.
- `orchestrator.py` interprets user requests and coordinates application behavior.
- `cli.py` and `ui.py` provide the terminal interface.

The original orchestrator relied on regular-expression matching. Commands such as "create a persona doctor" could be recognized, but more flexible requests were difficult to interpret.

This design also created ambiguity when a user requested multiple actions in one instruction.

### 2.2 Claude Tool Calling

The principal modification was the introduction of native tool calling.

Three tools were defined:

**create_persona:** Generates and saves a new persona based on a natural-language description.

**list_personas:** Retrieves the personas previously created and stored on disk.

**start_conversation:** Initiates a conversation between selected personas about a specified topic, with an optional number of turns.

Each tool has a JSON schema defining its parameters and expected input types.

The orchestrator sends these definitions to Claude, allowing the model to select an appropriate tool and generate its arguments.

When Claude requests a tool, the orchestrator executes the corresponding Python function and returns the result to Claude. The model can then provide a response to the user or request additional tools.

The implementation supports multiple tool-calling rounds, with a maximum of five rounds per user request.

This design separates natural-language interpretation from the execution of application functions.

### 2.3 Conversation Memory

The original orchestrator maintained limited conversational context.

I introduced a separate history for tool-calling interactions so that the stage manager could retain information about recent user requests, tool calls, and tool results.

This history is limited to the ten most recent interactions to prevent unlimited growth.

The implementation preserves tool requests and their corresponding results together when trimming the history.

This feature provides session-level memory for the orchestrator. It does not provide persistent autobiographical memory for individual personas across separate conversations.

### 2.4 Error Handling and Input Validation

An LLM-based application must handle failures that do not arise in ordinary deterministic programs.

The revised orchestrator includes handling for several categories of API failures:

- Authentication failures caused by invalid credentials.
- API rate-limit errors.
- Connection failures and timeouts.
- Other HTTP errors returned by Anthropic.

Instead of exposing raw API exceptions in these cases, the application returns messages explaining the problem.

Input validation was also added to the conversation tool.

Conversation topics must be nonempty strings, participant names must be supplied in an appropriate list format, and the number of turns must be an integer between 1 and 20.

These safeguards reduce the risk of malformed model-generated tool arguments causing unexpected behavior.

### 2.5 Backward Compatibility

The original regular-expression router was retained for models that do not support native tool calling.

This allows the application to continue operating in offline demonstration mode without requiring an Anthropic API key.

The distinction is important because offline testing and real LLM behavior serve different purposes. Simulated models provide reproducible tests, whereas live model calls are needed to evaluate natural-language interpretation and generated conversations.

## 3. Automated Testing

The original project included 39 passing tests.

After implementing the intelligent orchestrator, additional tests were written to evaluate the new functionality.

The final test suite contained **58 passing tests, with zero failures and zero expected failures**.

The additional tests addressed tool execution, multiple tool requests, invalid arguments, missing personas, conversation history, and API failures.

Tests involving Claude-style tool calls used simulated responses rather than contacting Anthropic's API.

This approach provides several advantages. Tests are inexpensive, fast, deterministic, and independent of network availability.

However, simulated tests cannot establish whether Claude will consistently select the correct tool or generate appropriate arguments when presented with unfamiliar natural-language requests.

For that reason, live testing was performed separately.

The final automated test command was:

`uv run pytest -q`

Result:

`58 passed`

## 4. Live Experiment 1: Scientific Reasoning and Discovery

### Objective

The first experiment evaluated whether two personas with contrasting approaches to scientific reasoning could maintain distinct identities during a multi-turn conversation.

### Participants

**Ada Chen:** An evidence-driven, skeptical scientist who emphasizes empirical validation.

**Marcus Wei:** An unconventional scientist who values intuition, speculation, and creative scientific thinking.

### Experimental Setup

Both personas were generated using Claude and stored as Markdown files.

The participants were instructed to discuss the relative importance of intuition and empirical evidence in scientific discovery.

The conversation was conducted using `claude-haiku-4-5` and was limited to six turns.

### Observations

The generated dialogue demonstrated recognizable differences between the two participants.

Ada emphasized evidence, skepticism, and the need to validate scientific claims.

Marcus emphasized creative thinking and the potential importance of intuition in generating new hypotheses.

Both personas responded to points raised by the other participant rather than simply repeating their initial positions.

This suggested that the system could produce conversations with continuity and distinguishable persona behavior.

### Problems Encountered

During this experiment, the stage manager generated an additional version of the debate after the conversation tool had already completed its work.

This created redundant dialogue in the terminal.

The underlying saved conversation transcript was correct, indicating that the problem concerned the stage manager's response after tool execution rather than the conversation-generation process itself.

To address this, the stage-manager instructions were revised to require a brief completion summary rather than another conversation.

A second limitation was the fixed number of conversation turns. The dialogue ended while the participants were still discussing the topic, rather than reaching a natural conclusion.

The saved transcript is available in:

`reports/ada_marcus_debate.md`

## 5. Live Experiment 2: Dinosaur Extinction Debate

### Objective

The second experiment evaluated whether PersonaForge could maintain distinct characters when the participants differed in age, expertise, and the scientific support for their arguments.

### Participants

**Charles Edward Hartwell:** A 50-year-old evolutionary biologist who emphasizes Darwinian selection and established scientific evidence.

**Dylan Marcus Chen:** An 18-year-old paleontology enthusiast who speculates that a viral pandemic contributed to dinosaur extinction.

### Experimental Setup

The participants debated whether dinosaur extinction was caused by an asteroid impact or a viral pandemic.

The conversation used `claude-haiku-4-5` and consisted of six turns.

### Observations

Charles argued from established scientific evidence, including the iridium layer and the Chicxulub impact structure.

Dylan initially emphasized the possibility of a viral pandemic but became increasingly interested in how his hypothesis might be evaluated scientifically.

The participants maintained recognizable differences in their reasoning styles.

The discussion also demonstrated some progression. Rather than simply restating their original positions, the characters engaged with each other's arguments.

### Limitations

Although Charles was portrayed as an experienced scientist, some of his statements were more confident than the available evidence justified.

For example, his discussion of whether a viral pandemic would leave identifiable skeletal abnormalities in fossils oversimplified the difficulties of detecting ancient infectious disease.

This illustrates an important distinction: **a persona can remain internally consistent while still making scientifically questionable claims.**

The dialogue also ended after six turns, leaving Dylan's final question unanswered.

Unlike the first experiment, the stage manager did not generate an additional debate after the conversation tool finished. It returned a short completion message.

This observation was consistent with the revised stage-manager instructions, although one successful run is insufficient to establish that the problem has been eliminated in every situation.

The saved transcript is available in:

`reports/charles_dylan_debate.md`

## 6. Comparative Evaluation

The two experiments tested different aspects of PersonaForge.

| Evaluation criterion | Experiment 1 | Experiment 2 |
|---|---|---|
| Topic | Intuition versus empirical evidence | Dinosaur extinction |
| Participants | Two contrasting scientists | Experienced scientist and young enthusiast |
| Conversation length | Six turns | Six turns |
| Persona consistency | Generally maintained | Generally maintained |
| Engagement with opposing arguments | Observed | Observed |
| Evolution of discussion | Observed | Observed |
| Natural conversation ending | No | No |
| Duplicate stage-manager dialogue | Observed | Not observed |
| Scientific accuracy concerns | Not independently verified | Specific overconfidence identified |

Both experiments produced coherent conversations in which the characters displayed distinguishable viewpoints.

However, these experiments were qualitative demonstrations rather than controlled measurements of model performance.

No independent scientific fact-checking system or automated persona-consistency evaluator was implemented.

Consequently, the results support the conclusion that PersonaForge can generate plausible multi-turn interactions, but they do not establish consistent factual accuracy or reliability across repeated trials.

## 7. Failure Analysis and Limitations

### 7.1 Stage-Manager Duplication

The most visible failure occurred when the stage manager generated additional dialogue after the conversation tool had completed its work.

The system was revised to instruct the stage manager to summarize completed conversations rather than recreate them.

The problem was not observed in the second live experiment.

### 7.2 Factual Reliability

The second experiment demonstrated that a convincing persona does not necessarily produce scientifically accurate statements.

Persona instructions influence tone, behavior, and perspective, but they do not independently verify factual claims.

A future version could incorporate retrieval from reliable sources or an independent evaluation agent.

### 7.3 Fixed Turn-Taking

The conversation engine uses a predetermined number of turns and a round-robin speaking order.

This can cause conversations to stop abruptly, even when an important question remains unanswered.

More natural conversations would require a mechanism for deciding when the discussion has reached a useful conclusion.

### 7.4 Limited Memory

The orchestrator retains recent tool-calling history during a session.

However, individual personas do not retain persistent memories of earlier conversations across separate sessions.

Persistent persona memory would require additional storage and retrieval mechanisms.

### 7.5 API Cost and Availability

Live persona generation and conversation turns require Anthropic API calls.

Consequently, system operation depends on valid credentials, network connectivity, API availability, and the user's available API budget.

The project uses `claude-haiku-4-5` for development and live evaluation to reduce costs.

### 7.6 Limited Experimental Sample

Only two live experiments are documented in this evaluation.

Although both produced useful conversations, a larger sample would be necessary to measure reliability, consistency, or performance across different subjects and persona combinations.

## 8. Novelty and Design Decisions

The main contribution of this project is the replacement of deterministic command matching with model-directed tool execution.

This allows users to interact with PersonaForge through more flexible natural-language instructions.

The implementation also retains a useful separation between model reasoning and application execution.

Claude decides which tool to request, while Python functions remain responsible for creating files, retrieving personas, and managing conversations.

Additional design decisions include maintaining an offline fallback, preserving bounded tool-call history, validating conversation parameters, and providing readable API error messages.

The combination of these changes makes the original package more flexible without requiring a complete redesign.

## 9. Future Improvements

Several improvements would be valuable in a subsequent version:

1. Introduce adaptive conversation termination so agents can finish when a discussion reaches a natural stopping point.
2. Add persistent memory for individual personas across conversations.
3. Implement an observer agent that evaluates persona consistency, factual accuracy, and conversation quality.
4. Expand automated testing to cover more combinations of tool calls and failure conditions.
5. Evaluate the system across a larger set of repeated live experiments.

These extensions were intentionally left outside the scope of the present implementation so that development could focus on the intelligent orchestrator and its reliability.

## 10. Conclusion

This project extended PersonaForge from a basic command-driven application into a system that uses Claude's native tool-calling capabilities to interpret user requests and coordinate persona interactions.

The implementation includes structured tool definitions, execution of model-requested actions, bounded session history, input validation, API error handling, and compatibility with the original offline mode.

Automated testing concluded with 58 passing tests.

Two live experiments demonstrated the system's ability to create distinct personas and generate coherent multi-turn conversations.

The experiments also exposed limitations involving stage-manager duplication, factual accuracy, and fixed conversation lengths.

Overall, the project demonstrates both the potential and the engineering challenges of using large language models as orchestrators for multi-agent applications.

The principal lesson is that successful LLM applications require more than generating convincing text. They also require structured interfaces, deterministic execution mechanisms, error handling, reproducible tests, and careful evaluation of model behavior.

---

## Supporting Files

- `reports/ada_marcus_debate.md` — First live conversation transcript.
- `reports/charles_dylan_debate.md` — Second live conversation transcript.
- `reports/live_test_evaluation.md` — Detailed live experiment evaluation.
- `tests/test_orchestrator.py` — Automated tests for the orchestrator.
- `src/personaforge/orchestrator.py` — Main orchestration implementation.
- `src/personaforge/llm.py` — Claude integration and tool-calling support.
