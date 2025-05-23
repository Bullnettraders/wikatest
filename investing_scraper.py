import requests
from bs4 import BeautifulSoup
from datetime import datetime

def get_investing_calendar():
    url = "https://www.investing.com/economic-calendar/"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "lxml")

    table = soup.find("table", id="economicCalendarData")
    rows = table.find_all("tr", class_="js-event-item")

    events = []

    for row in rows:
        country = row.get("data-country")
        time = row.get("data-event-datetime")  # ISO-Zeitformat
        importance = len(row.select(".grayFullBullishIcon"))  # Sterne zählen

        title = row.get("data-event-name")
        forecast = row.get("data-event-forecast")
        previous = row.get("data-event-previous")
        actual = row.get("data-event-actual")

        events.append({
            "country": country.lower() if country else "unknown",
            "time": datetime.fromisoformat(time).strftime("%H:%M") if time else "",
            "title": title.strip() if title else "",
            "forecast": forecast or "",
            "previous": previous or "",
            "actual": actual or "",
            "importance": importance
        })

    return events
