# Building a Deterministic Text-to-SQL Engine with LLMs

As LLMs become more integrated into product features, managing their non-deterministic nature becomes the primary engineering challenge. In financial applications, telling a user "You spent $400 on dining" when they actually spent $450 is a catastrophic failure of trust. Hallucinations are unacceptable.

In this post, we'll explore how Finpluse implements a "Text-to-SQL with Guardrails" pattern to deliver an AI Copilot that perfectly understands natural language but mathematically guarantees its answers.

## The Architecture: Generation + Validation

Instead of asking the LLM to generate the final answer directly, we use the LLM solely as an intent-parsing and translation layer. 

1. **Strict Schema Prompting**: The LLM is provided with a tightly scoped, whitelisted schema (e.g., just the `transactions` table).
2. **SQL Generation**: It translates the user's natural language question (e.g., "How much did I spend on Uber this month?") into a pure PostgreSQL query.
3. **The Verification Layer (The Guardrail)**: Before execution, a deterministic validator intercepts the generated SQL. It verifies:
   - The query is a read-only `SELECT` statement.
   - No forbidden keywords (`DROP`, `UPDATE`, `INSERT`) are present.
   - The query only accesses whitelisted tables.
4. **Deterministic Execution**: The validated query is executed safely by the application logic, ensuring the numbers returned are identical to what the user would see in their dashboard.

## Why This Matters

This hybrid approach leverages the strength of LLMs (flexible natural language understanding) while isolating their weakness (hallucinations/math errors). By decoupling intent parsing from data calculation, we provide an enterprise-grade AI experience that is both magical and mathematically sound.
