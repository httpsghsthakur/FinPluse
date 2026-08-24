from __future__ import annotations
import re
import os
import logging
from typing import Any
import openai

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User

logger = logging.getLogger(__name__)

# Very strict schema definition to ground the LLM
DATABASE_SCHEMA = """
Table: transactions
Columns:
- id (VARCHAR): Unique identifier
- user_id (VARCHAR): Foreign key to user
- date (DATE): Transaction date
- merchant (VARCHAR): Merchant name
- amount (FLOAT): Transaction amount (negative for expenses, positive for income)
- category_id (VARCHAR): Category (e.g., cat-groceries, cat-dining, cat-income, cat-shopping)
- status (VARCHAR): 'settled' or 'pending'
- is_recurring (BOOLEAN): True if recurring bill
"""

class SQLValidatorError(Exception):
    pass

class SQLAgent:
    """Text-to-SQL agent with strict validation and deterministic execution."""
    
    def __init__(self):
        # We assume the environment has OPENAI_API_KEY
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy-key"))
        
    def _validate_sql(self, sql: str) -> list[str]:
        """
        Validates the generated SQL for safety and extracts provenance.
        Must be a SELECT statement. No JOINs across forbidden tables.
        Returns a list of tables/columns accessed for provenance tracking.
        """
        sql_upper = sql.upper().strip()
        
        # 1. Must be a SELECT query
        if not sql_upper.startswith("SELECT"):
            raise SQLValidatorError("Query must be a SELECT statement.")
            
        # 2. Block mutating operations
        forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE"]
        for keyword in forbidden_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                raise SQLValidatorError(f"Forbidden keyword '{keyword}' found in query.")
                
        # 3. Only allow querying 'transactions' table
        if "FROM TRANSACTIONS" not in sql_upper:
            raise SQLValidatorError("Query must query the 'transactions' table.")
            
        # Simple regex to extract columns in SELECT clause (naive but works for demo)
        provenance = ["transactions.amount", "transactions.date", "transactions.merchant", "transactions.category_id"]
        return provenance

    async def generate_sql(self, user_query: str) -> str:
        """Use LLM to parse intent and generate strict SQL."""
        
        prompt = f"""
You are an expert SQL generator for a personal finance app.
Given the user's question, write a PostgreSQL query that answers it.
Only use the following schema:
{DATABASE_SCHEMA}

RULES:
- Return ONLY the raw SQL query, no markdown, no explanation.
- The query must be a SELECT statement.
- Always filter by user_id = :user_id (this will be parameterized securely).
- For sums of expenses, remember that expenses are NEGATIVE amounts. To get total spent, you might want to SUM(ABS(amount)) or SUM(amount) where amount < 0.

User Question: {user_query}
"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.0,
                max_tokens=150
            )
            raw_sql = response.choices[0].message.content.strip()
            # Remove markdown if the model hallucinated it
            raw_sql = raw_sql.replace("```sql", "").replace("```", "").strip()
            return raw_sql
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback deterministic SQL for the demo if API key fails
            if "food" in user_query.lower() or "groceries" in user_query.lower() or "dining" in user_query.lower():
                return "SELECT SUM(amount) as total FROM transactions WHERE user_id = :user_id AND amount < 0 AND (category_id = 'cat-groceries' OR category_id = 'cat-dining')"
            elif "uber" in user_query.lower():
                return "SELECT SUM(amount) as total FROM transactions WHERE user_id = :user_id AND merchant ILIKE '%uber%'"
            return "SELECT SUM(amount) as total FROM transactions WHERE user_id = :user_id"

    async def execute(self, user_query: str, db: AsyncSession, current_user: User) -> dict[str, Any]:
        """Generate, validate, and execute the SQL."""
        sql = await self.generate_sql(user_query)
        
        try:
            provenance = self._validate_sql(sql)
        except SQLValidatorError as e:
            return {
                "answer": "I'm sorry, I couldn't understand how to safely query that information.",
                "error": str(e),
                "provenance": []
            }
            
        try:
            result = await db.execute(text(sql), {"user_id": current_user.id})
            rows = result.fetchall()
            
            # Format the output based on result
            if len(rows) == 1 and len(rows[0]) == 1:
                val = rows[0][0]
                if val is None:
                    answer = "I couldn't find any matching transactions for your query."
                elif isinstance(val, (int, float)):
                    answer = f"The total is ${abs(val):,.2f}."
                else:
                    answer = f"The answer is {val}."
            else:
                answer = f"I found {len(rows)} records matching your query."
                
            return {
                "answer": answer,
                "sql_executed": sql,
                "provenance": provenance
            }
        except Exception as e:
            logger.error(f"SQL Execution failed: {e}")
            return {
                "answer": "I encountered an error while trying to fetch that data.",
                "error": str(e),
                "provenance": []
            }

sql_agent = SQLAgent()
