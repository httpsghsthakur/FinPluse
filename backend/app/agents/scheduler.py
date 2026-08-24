"""
Finpluse v2 -- Agent Scheduler

APScheduler configuration for running autonomous agents on recurring schedules.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
# In production, use RedisJobStore or SQLAlchemyJobStore

logger = logging.getLogger(__name__)

jobstores = {
    'default': MemoryJobStore()
}

executors = {
    'default': {'type': 'asyncio'}
}

job_defaults = {
    'coalesce': False,
    'max_instances': 1
}

scheduler = AsyncIOScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)

def start_scheduler():
    """Initialize and start the agent scheduler."""
    if not scheduler.running:
        scheduler.start()
        logger.info("Agent Scheduler started.")

async def schedule_agent_job(user_id: str, agent_name: str, trigger_data: dict, trigger_type: str = 'interval', **trigger_args):
    """
    Schedule an agent to run for a specific user.
    """
    from .auto_balance_agent import AutoBalanceAgent
    from .subscription_watchdog import SubscriptionWatchdogAgent
    from .bill_negotiation_agent import BillNegotiationAgent
    
    agent_map = {
        "auto_balance": AutoBalanceAgent,
        "subscription_watchdog": SubscriptionWatchdogAgent,
        "bill_negotiation": BillNegotiationAgent
    }
    
    agent_cls = agent_map.get(agent_name)
    if not agent_cls:
        logger.error(f"Agent {agent_name} not found.")
        return
    
    async def run_agent_job():
        logger.info(f"Running scheduled agent {agent_name} for user {user_id}")
        agent = agent_cls()
        await agent.run(user_id, trigger_data)

    job_id = f"{user_id}_{agent_name}"
    
    # Remove existing job if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        
    scheduler.add_job(
        run_agent_job,
        trigger=trigger_type,
        id=job_id,
        replace_existing=True,
        **trigger_args
    )
    logger.info(f"Scheduled {agent_name} for {user_id} with trigger {trigger_type}")

