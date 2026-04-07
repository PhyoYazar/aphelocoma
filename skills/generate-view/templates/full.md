# {{name}}'s Context (generated {{date}})

## About me
{{profile_summary}}

## Preferences
{{preferences_summary}}

## Active projects
{{#each projects}}
### {{name}}
{{overview}}
**Current state**: {{current_state}}
**In progress**: {{in_progress_count}} | **Planned**: {{planned_count}}
{{/each}}

## Open threads
{{#each open_threads}}
- {{this}}
{{/each}}

## Domain expertise
{{#each knowledge_topics}}
- {{topic}}: {{files}}
{{/each}}
