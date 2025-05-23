import json
import os
from datetime import date, timedelta
from ai_utils import extract_macro_event_time

POSTED_EVENTS_FILE = "posted_events.json"

def load_posted():
    if os.path.exists(POSTED_EVENTS_FILE):
        with open(POSTED_EVENTS_FILE, "r") as f:
            return set(tuple(x) for x in json.load(f))
    return set()

def save_posted(posted_events):
    with open(POSTED_EVENTS_FILE, "w") as f:
        json.dump(list(posted_events), f)

posted_events = load_posted()

def add_posted_event(identifier):
    posted_events.add(identifier)
    save_posted(posted_events)

def get_investing_calendar(for_tomorrow=False):
    dummy_data = [
        {
            'title': 'Verbraucherpreisindex (VPI)',
            'country': 'germany',
            'time': '08:00',
            'actual': '',
            'forecast': '6.1%',
            'previous': '6.5%',
        },
        {
            'title': 'Non-Farm Payrolls',
            'country': 'united states',
            'time': '14:30',
            'actual': '',
            'forecast': '180k',
            'previous': '175k',
        }
    ]
    target_date = date.today() + timedelta(days=1 if for_tomorrow else 0)
    date_str = target_date.strftime("%d.%m.%Y")
    for event in dummy_data:
        event['date'] = date_str
        if not event['time']:
            event['time'] = extract_macro_event_time(event['title'], country=event['country'])
    return dummy_data

async def post_today_events(bot, channel_id, test_mode=False):
    events = get_investing_calendar()
    channel = bot.get_channel(channel_id)

    # Sortiere nach Uhrzeit
    def parse_time(e):
        try:
            h, m = map(int, e['time'].split(":"))
            return h * 60 + m
        except:
            return 9999
    events.sort(key=parse_time)

    date_str = events[0]['date'] if events else date.today().strftime("%d.%m.%Y")
    header = f"📅 Kommende Wirtschaftstermine ({date_str})"
    message_lines = []

    flag_map = {
        'germany': '🇩🇪',
        'united states': '🇺🇸'
    }

    for event in events:
        identifier = (event['title'], event['date'], event['country'])
        if test_mode or identifier not in posted_events:
            emoji = flag_map.get(event['country'].lower(), '🌍')
            line = (
                f"{emoji} {event['time']} - {event['title']}\n"
                f"    Prognose: {event['forecast']} | Vorher: {event['previous']}"
            )
            message_lines.append(line)
            if not test_mode:
                add_posted_event(identifier)

    if message_lines:
        full_message = header + "\n\n" + "\n\n".join(message_lines)
        await channel.send(full_message)

async def check_for_actual_updates(bot, channel_id):
    events = get_investing_calendar()
    channel = bot.get_channel(channel_id)

    for event in events:
        identifier = (event['title'], event['date'], event['country'])

        # Wenn aktuelle Zahlen da sind UND noch nicht gepostet wurden
        if event['actual'] and identifier not in posted_events:
            flag_map = {
                'germany': '🇩🇪',
                'united states': '🇺🇸'
            }
            emoji = flag_map.get(event['country'].lower(), '🌍')
            msg = (
                f"✅ Zahlen veröffentlicht: {event['title']} ({emoji})\n"
                f"Ergebnis: {event['actual']} | Prognose: {event['forecast']} | Vorher: {event['previous']}"
            )
            await channel.send(msg)
            add_posted_event(identifier)

