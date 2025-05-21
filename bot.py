import time
from datetime import datetime
from investing_scraper import get_investing_calendar

def should_fetch_for_tomorrow():
    now = datetime.now()
    return now.hour >= 20

def fetch_calendar_data():
    for_tomorrow = should_fetch_for_tomorrow()
    return get_investing_calendar(for_tomorrow=for_tomorrow)

def print_calendar_summary():
    investing_events = fetch_calendar_data()
    print("📅 Wirtschaftstermine:")
    for event in investing_events:
        print(f"{event['date']} - {event['title']} ({event['country'].title()}) um {event['time']}")
        print(f"  Prognose: {event['forecast']}, Vorher: {event['previous']}, Tatsächlich: {event['actual']}\n")

# 🆕 Neue Funktion für manuellen Abruf
def abrufen():
    print(f"\n🔁 Manueller Abruf am {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print_calendar_summary()

def is_fetch_time(now):
    return now.minute in [0, 30] and now.second < 5

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
    # Abruf-Funktion testweise einmalig ausführen
    abrufen()

    # Danach in den Zeit-basierten Loop wechseln
    wait_until_next_check()
