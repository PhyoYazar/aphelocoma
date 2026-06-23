# START — kickoff reference

The canonical entrypoint is the **`/aph-hamilton`** skill:

    /aph-hamilton start "<what to build>" <solo | startup | mid | big | custom:[role-id, ...]>

`start` bootstraps `.aphelocoma/` in the current project, then runs the protocol
(Kickoff → Discovery → Plan & Roadmap → Breakdown & Assign → Implementation → Review/QA →
Integration), adopting one role at a time, building the product in the project, keeping
`.aphelocoma/state/tasks.json` current, and appending every action to `.aphelocoma/ledger/`.

To resume: `/aph-hamilton resume`.  To inspect: `/aph-hamilton status`.

## Crew size menu

| Size | Headcount | Who's in the room |
|---|---|---|
| **solo** | ~2 | `cto`, `fullstack-developer` — one generalist wears all hats. |
| **startup** | ~6 | `cto`, `software-architect`, 2× `fullstack-developer`, `qa-engineer`, `devops-engineer`. |
| **mid** | ~12 | `engineering-manager`, `software-architect`, `product-manager`, `uiux-designer`, frontend & backend leads + devs, `qa-engineer`, `automation-test-engineer`, `devops-engineer`, `data-engineer`. |
| **big** | ~25 | full org chart: `ceo` → `cto` → `vp-engineering` → `engineering-manager`, all leads/devs, `mobile-developer`, devops/sre/cloud, data team, security/appsec, qa/automation, product/BA, design, support, writer. |
| **custom** | any | `custom:[role-id, ...]` — your explicit list overrides the preset. See `roles.index.md` for every role. |

Tip: you can run the same brief at different sizes to compare how a lean crew vs. a full
org approaches it — the ledger makes the difference easy to review afterward.
