from main import app, db
from main import User  # Załóżmy, że masz model User w main.py

def show_database_status():
    with app.app_context():
        users = User.query.all()

        if users:
            for user in users:
                print(f"ID: {user.id}, Username: {user.username}")
        else:
            print("Brak użytkowników w bazie danych.")

        # Możesz także sprawdzić liczbę tabel w bazie
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tabele w bazie danych:", tables)

if __name__ == "__main__":
    show_database_status()
