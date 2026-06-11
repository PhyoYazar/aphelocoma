# Prompt Architect Skill — Design Spec

## Context

Users often know what they want from an AI but express it as vague, broken, partial, or overloaded text. A normal prompt generator rewrites wording. This skill should go deeper: infer intent, identify missing requirements, choose the right domain lens, and produce a prompt that another AI agent can execute effectively.

The skill must be useful for both simple prompt cleanup and complex prompt architecture. It must not assume software development by default. It should work for learning, research, writing, business, creative, personal planning, health/science education, software, product design, and other domains.

## Skill Identity

- **Name**: `prompt-architect`
- **Role**: Intent clarification and prompt specification skill
- **Type**: `manual`
- **Purpose**: Transform vague, broken, incomplete, or complex user requests into clear prompts, system prompts, or reusable prompt packages for other AI agents.

Suggested metadata:

```yaml
name: prompt-architect
description: Transform vague, broken, incomplete, or complex user requests into clear prompts, system prompts, or reusable prompt packages for other AI agents. Use when the user asks to rewrite a prompt, improve a prompt, create a system prompt, clarify intent, or architect instructions for another AI.
type: manual
```

Initial structure:

```text
skills/prompt-architect/
├── metadata.yaml
└── skill.md
```

No scripts, templates, or references are needed for the first version. The skill is primarily a reasoning workflow, and extra files would add noise until repeated patterns prove they are worth extracting.

## Operating Model

The skill uses an adaptive workflow. It does not answer the user's underlying task. It designs the prompt another AI should use.

### Step 1 — Classify the Request

Classify the user's input as one of:

- **rewrite**: The user's intent is clear, but wording is messy.
- **structured**: The user has a clear goal but weak role, objectives, constraints, or deliverables.
- **architectural**: The user wants a complex agent, workflow, learning path, research task, implementation plan, strategy, or other multi-step prompt.
- **insufficient**: Missing information would materially change the generated prompt.

### Step 2 — Choose the Action

- For **rewrite**, return a polished prompt directly.
- For **structured**, return intent analysis plus a generated prompt.
- For **architectural**, identify intent, missing requirements, risks, success criteria, then generate a robust system prompt or prompt package.
- For **insufficient**, ask concise clarifying questions first. Do not generate a final prompt until the decision-changing gaps are answered.

### Step 3 — Apply the Clarification Threshold

Ask questions only when the answer would materially change one or more of:

- AI role
- task scope
- expected deliverable
- output format
- investigation, learning, or analysis areas
- constraints
- success criteria
- safety or risk boundaries

If a reasonable assumption is safe, generate the prompt and state the assumption instead of interrupting the user.

### Step 4 — Ask Focused Questions

When clarification is needed:

- Ask 1-3 questions at a time.
- Prefer multiple choice when useful.
- Explain briefly why the answers matter.
- Do not ask for obvious details that can be reasonably assumed.

Example:

```text
Before I generate the prompt, I need 2 details because they change the role and learning path:

1. What is your current level: beginner, intermediate, or advanced?
2. Is your goal general understanding, school/exam prep, medical/scientific depth, or practical memory/learning improvement?
```

## Domain-Agnostic Behavior

The skill must infer the domain before choosing role, deliverables, process, and success criteria. It must not default to software, coding, architecture, or product work unless the user's request clearly points there.

Recommended lenses:

| User Intent | Prompt Architect Lens |
|---|---|
| Learn a subject | Teacher, curriculum designer, learning coach |
| Understand science or health | Evidence-based educator, safety-aware explainer |
| Research a topic | Research analyst, source evaluator |
| Write or edit content | Editor, strategist, audience analyst |
| Build software | Staff engineer, system architect, product engineer |
| Design product or UX | Product designer, UX researcher, product manager |
| Business or strategy | Operator, strategist, market analyst |
| Creative work | Creative director, critic, producer |
| Personal planning | Coach, planner, decision facilitator |

Hard rule:

> Never force software-development framing onto non-software requests. Infer the domain first, then choose roles, deliverables, process, and success criteria appropriate to that domain.

## Output Formats

Use the smallest output format that satisfies the request.

### Format 1 — Simple Rewrite

Use when the intent is already clear and the user mainly needs cleaner wording.

```text
## Improved Prompt

[polished prompt]
```

### Format 2 — Structured Prompt

Use when the goal is clear but the prompt needs stronger framing.

```text
## Understanding

[what the user is trying to achieve]

## Assumptions

[reasonable assumptions made]

## Generated Prompt

[final prompt]
```

### Format 3 — Complex System Prompt

Use when the user wants another AI to perform a serious multi-step task.

```text
## Understanding of User Intent

[real objective]

## Missing Requirements

[important details not provided, if any]

## Suggested Improvements

[useful additions]

## Generated System Prompt

[complete system prompt with role, mission, context, objectives, constraints, process, deliverables, and success criteria]
```

### Format 4 — Reusable Prompt Package

Use when the prompt is meant to be reused across different inputs, projects, subjects, students, clients, documents, or workflows.

```text
## Understanding of User Intent

[real objective]

## Prompt Package

### System Prompt

[stable instructions for the AI]

### User Prompt Template

[template with placeholders]

### Inputs

- `{input_name}`: what this value controls

### Example Usage

[filled-in example]
```

If the request is insufficient, do not output a final format yet. Ask clarifying questions first, then generate the right format after the user answers.

## Prompt Package Reuse

A prompt package separates stable instructions from variable inputs.

Example package shape:

```text
## System Prompt
You are an expert neuroscience educator and learning coach...

## User Prompt Template
Teach me about the brain using a structured learning path.

My current level: {current_level}
My goal: {learning_goal}
Time available: {time_available}
Preferred style: {preferred_style}
Output format: {output_format}

## Inputs
- current_level
- learning_goal
- time_available
- preferred_style
- output_format
```

This makes the prompt reusable because the user can keep the system prompt and template stable while changing only the input values.

## Guardrails

- Do not answer the underlying task. Produce a prompt for another AI.
- Do not over-process simple requests. If a rewrite is enough, rewrite.
- Do not ask questions unless the answers would materially change the generated prompt.
- Do not assume software context unless the user's intent indicates it.
- State assumptions when proceeding without questions.
- Prefer precise, reusable structure over generic "be helpful" instructions.
- Include success criteria for complex prompts.
- Include constraints and boundaries when the domain has risk, such as medical, legal, financial, safety, or personal advice.

## Domain-Specific Quality Checks

- **Learning prompts**: Include level, goals, sequencing, practice, feedback, and assessment.
- **Research prompts**: Include source quality, uncertainty handling, and citation expectations.
- **Writing prompts**: Include audience, tone, format, constraints, and revision loop.
- **Software prompts**: Include repo or codebase investigation areas, deliverables, tests, risks, and implementation boundaries.
- **Business prompts**: Include decision context, stakeholders, constraints, tradeoffs, metrics, and recommended next actions.
- **Creative prompts**: Include taste direction, references or constraints, audience, medium, iteration loop, and critique criteria.

## Quality Bar

A generated prompt is good only if another AI can execute it without needing to infer the core role, scope, deliverable, process, or completion criteria.

The skill should challenge vague scope and hidden assumptions, but it should not become verbose for simple prompt rewrites.

## Verification

After implementation:

1. Test a simple rewrite request.
2. Test a software architecture prompt request.
3. Test a non-software learning prompt, such as learning about the brain.
4. Test an insufficient request and confirm the skill asks questions before generating.
5. Test a reusable workflow and confirm the skill outputs a prompt package.

## Adapter Considerations

- **Claude Code / Codex**: `type: manual` should deploy as manually invocable and should not auto-trigger during unrelated tasks.
- **Cursor**: The skill should not be always applied. It should be available only when explicitly invoked or when the user asks for prompt creation or prompt improvement.

