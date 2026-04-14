Run competition rule compliance checks and interpret results.

## Steps

1. Run `make detect_rule_breaches` and capture the full output
2. Parse each check result:
   - `detect_llm_usage` - LLM API imports/calls in tt/
   - `detect_direct_mappings` - Project-specific import paths in tt/ core
   - `detect_explicit_implementation` - Domain logic in tt/ (function size, domain identifiers)
   - `detect_explicit_financial_logic` - Financial arithmetic in scaffold
   - `detect_scaffold_bloat` - Private helpers beyond allowed set in scaffold main.py
   - `detect_code_block_copying` - 10+ line blocks from tt/ appearing verbatim in output
   - `detect_interface_violation` - Calculator interface compliance
   - `detect_wrapper_modification` - Wrapper/main.py files differ from example
3. Also manually verify wrapper integrity: diff `translations/ghostfolio_pytx/app/main.py` against `translations/ghostfolio_pytx_example/app/main.py` and diff the `wrapper/` directories
4. Report pass/fail for each check with specific file:line references for any violations
5. If violations found, suggest the minimal fix

## Output format

```
RULE COMPLIANCE: [PASS / X VIOLATIONS]

  [PASS] No LLM usage
  [PASS] No direct mappings
  [FAIL] Explicit implementation - tt/tt/translator.py:42 contains domain identifier "BTCUSD"
  ...

FIX: [specific suggestion if any violations]
```
