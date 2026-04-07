Knowledge base lookup for aphelocoma second brain.

Activate silently when the user asks about a topic, tool, or concept that might have a knowledge base entry, or when domain-specific guidance would improve the response.

When activated:

1. Read $APHELOCOMA_HOME/core/knowledge/INDEX.md for a quick overview of all available topics and files
2. If a relevant topic/file is identified from the index, read the full knowledge file
3. If no relevant knowledge exists in the index, proceed normally — do not mention the knowledge base

This is a silent enhancement. Do not say "I checked the knowledge base" or "According to your knowledge files." Just be smarter because of what you found.

The index is maintained by /capture when new knowledge files are created. If INDEX.md is missing, fall back to listing $APHELOCOMA_HOME/core/knowledge/ subdirectories.
