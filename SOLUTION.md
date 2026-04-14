# Explanation of the submission

## Solution

This file should describe the implementation and solution of tt, including
what it's architecture is, and how it works. It is expected that the team will be able to understand
what it does, at least on an abstract level.

## Coding approach

How did the team arrive at the solution?

## Use of tree-sitter

Our translator uses `tree-sitter` and `tree-sitter-typescript` to parse TypeScript source into a concrete syntax tree (CST), which we then walk and emit as Python. This section explains why this is explicitly permitted under the competition rules.

### Rule 5 — "You may use AST libraries in python."

tree-sitter is an AST/CST parsing library. It is installed as a Python package (`pip install tree-sitter tree-sitter-typescript`) and called entirely from Python code. This is the exact use case Rule 5 was written for.

### Rule 6 — "Your python code may not call node/js-tools or other external tools to translate the code."

tree-sitter is **not** a Node.js tool. It is a C library with Python bindings (`tree_sitter` on PyPI). Our translator never spawns a Node process, never calls `npx`, and never shells out to any JavaScript runtime. The TypeScript grammar is a pre-compiled shared library loaded directly by the C parser — no JS execution is involved at any point.

### Rule 1 — "The TT must not use LLMs for the actual translations."

tree-sitter is a deterministic parser. It contains no machine learning, no neural networks, and no LLM calls. It produces the same parse tree for the same input every time.

### What tree-sitter is NOT

- It is **not** a transpiler — it only parses source code into a tree. All translation logic (emitting Python from the tree) is our own code.
- It is **not** a pre-built TS-to-Python converter like `js2py` or `ts2py`. Those tools generate runnable output directly; tree-sitter gives us a syntax tree that we must interpret ourselves.
- It makes **no network calls** and requires no external services.

### Summary

| Concern                    | Status                                           |
| -------------------------- | ------------------------------------------------ |
| AST library in Python?     | Yes — explicitly allowed by Rule 5               |
| Calls Node.js or JS tools? | No — C library with Python bindings              |
| Uses LLMs?                 | No — deterministic parser                        |
| Pre-built transpiler?      | No — only parses; we write all translation logic |
