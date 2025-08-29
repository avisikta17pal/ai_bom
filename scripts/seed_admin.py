import asyncio

from sqlalchemy import select

from ai_bom.core.config import get_settings
from ai_bom.core.security import get_password_hash
from ai_bom.db.models import User
from ai_bom.db.session import AsyncSessionLocal, init_models


async def main():
    await init_models()
    async with AsyncSessionLocal() as session:
        settings = get_settings()
        result = await session.execute(select(User).where(User.email == settings.admin_email))
        user = result.scalar_one_or_none()
        if user:
            print("Admin already exists")
            return
        admin = User(email=settings.admin_email, password_hash=get_password_hash(settings.admin_password), is_admin=True)
        session.add(admin)
        await session.commit()
        print(f"Created admin {settings.admin_email}")


if __name__ == "__main__":
    asyncio.run(main())

