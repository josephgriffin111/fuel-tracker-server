import requests
from bs4 import BeautifulSoup
import sqlite3
import schedule
import time
from flask import Flask, jsonify

# Initialize Flask app
app = Flask(__name__)

# Database setup
DB_NAME = "fuel_prices.db"

def create_database():
    """Creates database if not exists"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS prices (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 station_name TEXT,
                 diesel_price REAL,
                 location TEXT,
                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def fetch_fuel_prices():
    """Scrapes fuel prices from FuelCompare.ie for Cork"""
    url = "https://fuelcompare.ie/cheaper-fuel/cork"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print("Failed to fetch data.")
        return
    
    soup = BeautifulSoup(response.text, "html.parser")
    stations = soup.find_all("div", class_="station-listing")  # Update this if the site structure changes

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM prices")  # Clear old data before inserting new ones

    for station in stations:
        name = station.find("h3").text.strip()
        price = float(station.find("span", class_="price").text.strip().replace("€", ""))
        location = station.find("p", class_="location").text.strip()

        c.execute("INSERT INTO prices (station_name, diesel_price, location) VALUES (?, ?, ?)", 
                  (name, price, location))
    
    conn.commit()
    conn.close()
    print("Fuel prices updated.")

# Schedule daily updates
schedule.every().day.at("06:00").do(fetch_fuel_prices)

@app.route("/prices", methods=["GET"])
def get_prices():
    """API endpoint to get fuel prices"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT station_name, diesel_price, location FROM prices ORDER BY diesel_price ASC")
    data = [{"station": row[0], "price": row[1], "location": row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify(data)

if __name__ == "__main__":
    create_database()
    fetch_fuel_prices()  # Run once on startup
    app.run(host="0.0.0.0", port=5000)
