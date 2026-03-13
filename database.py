from sqlalchemy import create_engine, Column, Integer, String, Text, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///users.db?check_same_thread=False', echo=False )
Base = declarative_base()

inspector = inspect(engine)
if 'users' in inspector.get_table_names():
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'coins' not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0"))
            conn.commit()

Base.metadata.create_all(engine)


Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    coins = Column(Integer, nullable=False, default=0)  # Добавлен default

    def __repr__(self):
        return f"<User(id={self.id}, title='{self.title}', coins={self.coins})>"


def add_user(title, password):
    try:
        task = User(title=title, password=password, coins=0)
        session.add(task)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        return False

def update_balance(user_id: int, coins: int):
    user = session.get(User, user_id)
    if user:
        user.coins += coins
        session.commit()
        print(f"✅ Баланс пользователя {user.title} обновлен")
        return True
    else:
        print(f"❌ Пользователь с id {user_id} не найден")
        return False


def delete_user(id_user):
    try:
        task = session.query(User).get(id_user)
        if task:
            session.delete(task)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        return False


def get_all_users():
    try:
        users = session.query(User).all()
        return users
    except Exception as e:
        return []


def get_user(task_id):
    try:
        return session.query(User).get(task_id)
    except Exception as e:
        return None


def get_user_name(name):
    try:
        user = session.query(User).filter(User.title == name).first()
        if user:
            print(f"🔍 Пользователь {name} найден")
        else:
            print(f"🔍 Пользователь {name} НЕ найден")
        return user
    except Exception as e:
        print(f"❌ Error getting user by name: {e}")
        return None


def log(username: str, password: str):
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if 'users' not in inspector.get_table_names():
            Base.metadata.create_all(engine)

        user = session.query(User).filter(User.title == username).first()

        if user and user.password == password:
            print(f"✅ User {username} logged in successfully")
            return True
        else:
            return False
    except Exception as e:
        return False
