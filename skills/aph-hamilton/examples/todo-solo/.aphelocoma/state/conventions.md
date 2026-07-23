# Conventions

- Product: one self-contained HTML file with no build step or external dependencies.
- Implementation: browser-native HTML, CSS, and JavaScript with small named functions.
- State: in-memory page-session state only.
- Errors: reject empty todo text without changing state.
- Tests/review: exercise add, list, complete, and remove behavior directly in a browser.
