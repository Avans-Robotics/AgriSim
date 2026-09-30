## 2026-09-30 Reset main and start fresh branch
### Goal & outcome
Clean local main and start the project from scratch. Local main now matches origin/main (LICENSE only); new branch feat/fresh-start created from it.
### Decisions & why
- Old local main (bb04a4c) had unrelated history to origin/main and only a toy corn field prototype; discarded via hard reset.
- No archive tag: bb04a4c is the parent of fix/field-freeze-makefile, which still preserves the old work locally and on origin.
- Uncommitted CLAUDE.md edits dropped; CLAUDE.md to be rewritten during new project design.
### Lessons / gotchas
- Old CLAUDE.md referenced 'omni.physx.graph.nodes.PPointInstancer', which does not look like a real API; UsdGeom.PointInstancer is the real instancing prim.
- Old .gitignore listed sim/*.py files that were committed anyway, so the ignore had no effect.
### State
Branch feat/fresh-start at ce39370, clean tree. Validated via git status/log. Not pushed (user pushes).
### Open items
- Decide whether to delete fix/field-freeze-makefile (local + remote).
- Design new project structure and CLAUDE.md.
