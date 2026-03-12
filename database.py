from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///todos.db?check_same_thread=False', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

Base.metadata.create_all(engine)
print("✅ Таблицы созданы или уже существуют")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False, unique=True)
    password = Column(Text, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, title='{self.title}')>"


def add_user(title, password):
    try:
        task = User(title=title, password=password)
        session.add(task)
        session.commit()
        print(f"✅ Пользователь {title} добавлен")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error adding user: {e}")
        return False


def delete_user(id_user):
    try:
        task = session.query(User).get(id_user)
        if task:
            session.delete(task)
            session.commit()
            print(f"✅ Пользователь {id_user} удален")
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"❌ Error deleting user: {e}")
        return False


def get_all_users():
    try:
        users = session.query(User).all()
        print(f"📊 Найдено пользователей: {len(users)}")
        return users
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        return []


def get_user(task_id):
    try:
        return session.query(User).get(task_id)
    except Exception as e:
        print(f"❌ Error getting user: {e}")
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
            print("❌ Таблица users не существует! Создаем...")
            Base.metadata.create_all(engine)

        user = session.query(User).filter(User.title == username).first()

        if user and user.password == password:
            print(f"✅ User {username} logged in successfully")
            return True
        else:
            print(f"❌ Failed login attempt for {username}")
            return False
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return False
