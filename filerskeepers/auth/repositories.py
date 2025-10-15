from filerskeepers.auth.models import User


class UserRepository:
    async def create(self, email: str, hashed_password: str, api_key: str) -> User:
        user = User(email=email, hashed_password=hashed_password, api_key=api_key)
        await user.insert()
        return user

    async def find_by_email(self, email: str) -> User | None:
        return await User.find_one(User.email == email)

    async def find_by_api_key(self, api_key: str) -> User | None:
        return await User.find_one(User.api_key == api_key)

    async def update(self, user: User) -> User:
        user.update_timestamp()
        await user.save()
        return user
