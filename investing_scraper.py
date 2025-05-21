import time
from datetime import datetime
from investing_scraper import get_investing_calendar

# 🕒 Entscheide anhand der Uhrzeit, ob morgen angezeigt werden soll
def should_fetch_for_tomorrow():
    now = datetime.now()
    return now.hour >= 20  # Nach 20:00 Uhr wird für morgen vorbereitet

# 📋 Holen der Kalenderdaten mit Vorschau-Logik
def fetch_calendar_data():
    for_tomorrow = should_fetch_for_tomorrow()
    investing_events = get_investing_calendar(for_tomorrow=for_tomorrow)
    return investing_events

# 🖨️ Ausgabe formatieren
def print_calendar_summary():
    investing_events = fetch_calendar_data()

    print("📅 Wirtschaftstermine:")
    for event in investing_events:
        print(f"{event['date']} - {event['title']} ({event['country'].title()}) um {event['time']}")
        print(f"  Prognose: {event['forecast']}, Vorher: {event['previous']}, Tatsächlich: {event['actual']}\n")

# 🕓 Zeitfenster prüfen (volle und halbe Stunde)
def is_fetch_time(now):
    return now.minute in [0, 30] and now.second < 5  # innerhalb der ersten 5 Sekunden

# 🔁 Hauptloop
def wait_until_next_check():
    already_fetched = False
    print("🚀 Starte Kalender-Überwachung ...")
    while True:
        now = datetime.now()

        if is_fetch_time(now):
            if not already_fetched:
                print(f"\n⏰ Datenabruf um {now.strftime('%H:%M:%S')}")
                print_calendar_summary()
                already_fetched = True
        else:
            already_fetched = False

        time.sleep(1)

if __name__ == "__main__":
    wait_until_next_check()
