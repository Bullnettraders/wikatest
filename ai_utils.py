import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_macro_event_time(text, country="Germany"):
    prompt = f"""
Du bist ein KI-Assistent für Finanzdaten. Bestimme die typische Veröffentlichungszeit (MEZ, 24h) für folgendes Wirtschaftsevent in {country}, wenn möglich.

TEXT:
{text}

Antworte nur mit einer Uhrzeit im Format „HH:MM Uhr“. Wenn unklar, antworte mit „unbekannt“.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("GPT-Fehler:", e)
        return "unbekannt"

def extract_earnings_time(text):
    prompt = f"""
Du bist ein Finanzassistent. Erkenne aus diesem Text die typische Veröffentlichungszeit in MEZ (24h-Format).

Beispiele:
- "before market open" → 13:00 Uhr
- "after market close" → 22:05 Uhr
- "at 8:30 a.m. ET" → 14:30 Uhr

TEXT:
{text}
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print("GPT-Fehler:", e)
        return "unbekannt"
