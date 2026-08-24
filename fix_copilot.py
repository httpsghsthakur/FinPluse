import re

with open(r'backend\app\api\v1\copilot.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add SQL agent import
old_import = "from app.ml.classifiers.intent_classifier import intent_classifier"
new_import = '''from app.ml.classifiers.intent_classifier import intent_classifier
from app.ml.copilot.sql_agent import sql_agent'''
text = text.replace(old_import, new_import)

# Replace the chat streaming logic to invoke SQLAgent
# We need to find the @router.post("/chat") endpoint logic
old_chat = '''@router.post("/chat")
async def chat_stream(
    request: CopilotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Handle chat interactions using SSE (Server-Sent Events) to simulate typing.
    Currently uses local classifier + deterministic logic.
    """
    query = request.message
    intent, confidence = intent_classifier.predict(query)

    fin_data = await _compute_financials(db, current_user)
    
    # Simple deterministic matching matching frontend's mock aiEngine logic
    query_lower = query.lower()
    
    response_text = ""
    if "food" in query_lower or "groceries" in query_lower or "dining" in query_lower:
        response_text = f"You've spent **{_format_currency(fin_data['dining_total'])}** on food and dining so far this month."
        if fin_data['dining_total'] > fin_data['dining_budget']:
            response_text += f" This is currently over your planned budget of **{_format_currency(fin_data['dining_budget'])}**."
    elif "save" in query_lower or "saving" in query_lower:
        response_text = f"You currently have **{_format_currency(fin_data['savings'])}** in your savings account."
    elif "budget" in query_lower:
        response_text = "Your budget is looking healthy, but watch your dining expenses which have trended higher recently."
    elif "hello" in query_lower or "hi" in query_lower:
        response_text = "Hello! I'm Finpilot, your AI financial assistant. How can I help you understand your money today?"
    else:
        response_text = f"I categorized your intent as **{intent}** (confidence: {confidence:.2f}). To help answer your specific question, I would typically analyze your transactions, but my advanced response generation is pending the Phase 7 LLM upgrade."

    async def event_generator():
        # Simulate thinking delay
        await asyncio.sleep(0.5)
        
        words = response_text.split(" ")
        for i, word in enumerate(words):
            chunk = {
                "id": str(int(time.time() * 1000)),
                "content": word + (" " if i < len(words) - 1 else ""),
                "role": "assistant"
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.02)
            
        # Final end message
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")'''

new_chat = '''@router.post("/chat")
async def chat_stream(
    request: CopilotRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Handle chat interactions using SSE (Server-Sent Events) to simulate typing.
    Uses SQLAgent (Text-to-SQL LLM) for accurate data querying.
    """
    query = request.message
    
    # Execute SQL Agent
    result = await sql_agent.execute(query, db, current_user)
    
    response_text = result.get("answer", "I could not process your request.")
    provenance = result.get("provenance", [])
    
    if provenance:
        response_text += "\n\n*(Sources: " + ", ".join(provenance) + ")*"

    async def event_generator():
        # Simulate thinking delay
        await asyncio.sleep(0.2)
        
        words = response_text.split(" ")
        for i, word in enumerate(words):
            chunk = {
                "id": str(int(time.time() * 1000)),
                "content": word + (" " if i < len(words) - 1 else ""),
                "role": "assistant"
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0.02)
            
        # Final end message
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")'''

text = text.replace(old_chat, new_chat)

with open(r'backend\app\api\v1\copilot.py', 'w', encoding='utf-8') as f:
    f.write(text)
