from main import *

def show_database_status():
    with app.app_context():
        users = User.query.all()

        if users:
            for user in users:
                print(f"ID: {user.id}, Username: {user.username}, Password: {user.password}")
        else:
            print("Brak użytkowników w bazie danych.")

        markes= Marker.query.all()
        if markes:
            for marker in markes:
                print(f"ID: {marker.id}, User ID: {marker.user_id}, Name: {marker.name}, Latitude: {marker.latitude}, Longitude: {marker.longitude}, Description: {marker.description}")
        else:
            print("Brak znaczników w bazie danych.")

        routes = Route.query.all()
        if routes:
            for route in routes:
                print(f"ID: {route.id}, User ID: {route.user_id}, Name: {route.name}, Description: {route.description}, Waypoints: {route.waypoints}")
        else:
            print("Brak tras w bazie danych.")

        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("Tabele w bazie danych:", tables)

if __name__ == "__main__":
    show_database_status()
