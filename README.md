# Avalanche Risk Map

This web application provides a comprehensive toolset for mountain hikers and tourists to assess and manage avalanche risks. By integrating weather data, digital elevation models (DEM), and user-provided inputs, the app creates interactive risk maps, suggests safe routes, and displays key meteorological factors affecting avalanche danger.

## Key Features

*   **Interactive Avalanche Risk Map:** Visualizes potential avalanche danger zones based on terrain slope, aspect, and current weather conditions (e.g., snow depth, wind, temperature).
*   **Weather Integration:** Fetches real-time and forecasted weather data via the Open-Meteo API to dynamically adjust risk levels.
*   **Custom Route Planning:** Users can create, save, and visualize their hiking routes. The application cross-references these routes with potential risk areas.
*   **User Markers & Alerts:** Authenticated users can place custom markers on the map, including specific avalanche warnings, to share real-time field observations.
*   **Avalanche Statistics:** Calculates distances to known avalanche points and assesses the number of avalanches within a specific radius of a given location.

## Technologies Used

*   **Backend:** Python 3, Flask
*   **Database:** SQLite, SQLAlchemy (ORM)
*   **Geospatial & Data Processing:** Rasterio (DEM processing), Pandas, NumPy
*   **APIs:** Open-Meteo API (weather), OpenStreetMap API (map)
*   **Frontend:** HTML, CSS, JavaScript (Leaflet.js for interactive maps)

## Setup & Installation

To run this application locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd PythonLawiny
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the environment variables:**
    Copy the example environment file and customize it with your own values (especially important for production):
    ```bash
    cp .env.example .env
    ```

5.  **Set up the Database:**
    The application will automatically initialize the SQLite database on the first run.

6.  **Run the application:**
    ```bash
    python main.py
    ```

7.  **Access the application:**
    Open your web browser and navigate to `http://127.0.0.1:5000/`

## Project Structure Highlights

*   `main.py`: The entry point of the Flask application.
*   `__init__.py`: Application factory, configuration setup, and database initialization. Loads settings from `.env`.
*   `routes.py`, `flask_routes/`: Contains all routing logic for web pages, map data, and user accounts.
*   `models.py`: Defines the SQLAlchemy database models (`User`, `Route`, `Marker`).
*   `avalanche_danger.py`: Core logic for calculating avalanche risks based on weather and terrain data.
*   `constants.py`: Centralized file storing hyperparameters and physical constants used in risk calculations.
*   `static/`: Contains CSS, JavaScript, generated map images (`risk_map.png`), and GeoJSON data for hiking trails.
*   `templates/`: Contains HTML templates for the frontend.

## Configuration & Environment Variables

This project follows the 12-Factor App methodology for configuration. All sensitive data and environment-specific settings (like database URIs and secret keys) are loaded from environment variables using `os.environ`. 

For local development, these can be placed in a `.env` file (see `.env.example`). The application gracefully falls back to sensible defaults (like a local SQLite database) if these variables are not provided, ensuring a smooth developer experience.