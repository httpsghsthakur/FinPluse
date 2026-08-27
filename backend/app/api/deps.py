from typing import Annotated
import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models.user import User
from dotenv import load_dotenv

load_dotenv()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-supabase-jwt-secret")

security = HTTPBearer()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_aud": False}
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # Upsert user in db
        user_res = await db.execute(select(User).where(User.id == user_id).limit(1))
        db_user = user_res.scalars().first()
        if not db_user:
            email = payload.get("email", f"{user_id}@example.com")
            name = payload.get("user_metadata", {}).get("full_name", "Finpluse User")
            db_user = User(
                id=user_id,
                email=email,
                name=name,
                currency="INR",
                theme="dark",
            )
            db.add(db_user)
            await db.flush()

        # Ensure user has baseline categories & accounts (checks if already seeded, so safe for existing users)
        try:
            from app.api.v1.admin import seed_database
            await seed_database(db, db_user)
            await db.commit()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"User baseline seed check for {user_id}: {e}")
            
        return db_user
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
