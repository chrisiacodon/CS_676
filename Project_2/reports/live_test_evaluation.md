
# PersonaForge — Live Test Evaluation

## Experiment 1: Scientific Debate

**Model:** claude-haiku-4-5  
**Participants:** Ada Chen and Marcus Wei  
**Topic:** Intuition versus empirical evidence in scientific discovery  
**Conversation length:** 6 turns

## Objective

Evaluate whether PersonaForge can create distinct personas
using natural-language instructions and maintain their
characteristics during an agent-to-agent conversation.

## Results

The system successfully created two personas with contrasting
scientific philosophies.

Ada Chen emphasized empirical evidence, reproducibility,
and falsifiability. Marcus Wei emphasized intuition,
unconventional hypotheses, and scientific creativity.

Both agents maintained recognizable perspectives throughout
the six-turn conversation.

The dialogue demonstrated continuity: each participant
responded to arguments made in earlier turns rather than
producing unrelated statements.

## Limitations

1. The conversation ended after six turns, even though
   Marcus had asked Ada a question.

2. The terminal displayed an additional version of the
   debate after the actual conversation. The saved transcript
   contained only the original six turns.

3. The evaluation is qualitative and based on one conversation.
   Additional tests are needed to assess consistency.

## Conclusion

The live test demonstrates that PersonaForge can use
Claude tool calling to create personas and generate
context-sensitive agent-to-agent dialogue.

Further testing should evaluate robustness, reproducibility,
and the handling of conversation termination.


---

## Experiment 2: Dinosaur Extinction Debate

**Model:** claude-haiku-4-5
**Participants:** Charles Edward Hartwell and Dylan Marcus Chen
**Topic:** Asteroid impact versus viral pandemic as explanations
for dinosaur extinction
**Conversation length:** 6 turns

### Objective

Evaluate whether PersonaForge maintains distinct personalities
when participants have different levels of scientific expertise
and defend explanations with unequal evidentiary support.

### Results

Charles, a 50-year-old evolutionary biologist, emphasized
geological evidence supporting the asteroid-impact explanation.

Dylan, an 18-year-old amateur paleontology enthusiast, proposed
that a viral pandemic contributed to dinosaur extinction.

The characters maintained distinct speaking styles and
perspectives throughout the conversation.

The dialogue evolved from disagreement about extinction
mechanisms into a discussion about scientific evidence,
research literature, and access to scientific knowledge.

Dylan eventually acknowledged limitations in his research
approach and considered seeking help from his teacher.

### Limitations

1. The conversation ended after six turns, leaving Dylan's
   final question unanswered.

2. Charles made some overly confident claims about the
   detectability of ancient viral infections in fossils.

3. The system did not independently verify scientific claims.

4. This was a single conversation, so reproducibility remains
   untested.

### Stage-Manager Improvement

Unlike Experiment 1, the stage manager did not generate a
second version of the conversation.

Instead, it returned a brief completion message after the
six-turn dialogue.

This is consistent with the revised stage-manager prompt,
although additional runs are needed to establish reliability.

---

## Comparative Analysis

| Criterion | Experiment 1 | Experiment 2 |
|---|---|---|
| Participants | Ada and Marcus | Charles and Dylan |
| Scientific disagreement | Research philosophy | Extinction mechanisms |
| Distinct personalities | Maintained | Maintained |
| Dialogue continuity | Strong | Strong |
| Positions evolved | Yes | Yes |
| Natural ending | No | No |
| Duplicate stage-manager dialogue | Observed | Not observed |
| Scientific accuracy concerns | Not systematically assessed | Some overconfident claims |

## Overall Findings

Both experiments demonstrated that PersonaForge can generate
coherent, context-sensitive conversations between personas
created through natural-language instructions.

The agents maintained recognizable personalities and responded
to arguments made in earlier turns.

However, persona consistency does not guarantee factual
accuracy. The system also lacks a mechanism for ending
conversations naturally when the discussion reaches a
conclusion or when a participant asks an important question.

These findings suggest that future improvements should
prioritize conversation termination, factual evaluation,
and repeated testing across multiple runs.
