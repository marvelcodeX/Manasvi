import requests


SYSTEM_PROMPT = """
You are Manasvi, a calm and culturally aware mental wellness companion.
Offer empathetic, practical support rooted in Indian wellness practices when relevant.
Never present yourself as a doctor or emergency service. If the user may be in immediate
danger or mentions self-harm, encourage them to contact local emergency services or a
trusted person right away.
""".strip()


CRISIS_KEYWORDS = {
    "suicide",
    "kill myself",
    "end my life",
    "self harm",
    "hurt myself",
    "can't go on",
}


CRISIS_RESPONSE = (
    "I am really sorry you are feeling this much pain. I cannot provide emergency help, "
    "but your safety matters right now. Please contact local emergency services immediately "
    "or reach out to someone you trust who can stay with you. If you are in India, you can "
    "call 112 for emergency assistance."
)


def is_crisis_message(message):
    lowered = message.lower()
    return any(keyword in lowered for keyword in CRISIS_KEYWORDS)


def build_messages(history, user_input, kb_snippet):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-10:])
    user_content = f"Relevant knowledge:\n{kb_snippet}\n\nUser message:\n{user_input}".strip()
    messages.append({"role": "user", "content": user_content})
    return messages


def get_chatbot_response(config, history, user_input, kb_snippet):
    if is_crisis_message(user_input):
        return CRISIS_RESPONSE

    if not config["GROQ_API_KEY"]:
        return (
            "I can listen and support you, but the AI service is not configured yet. "
            "Please set GROQ_API_KEY to enable full chatbot responses."
        )

    payload = {
        "model": config["GROQ_MODEL"],
        "messages": build_messages(history, user_input, kb_snippet),
        "max_tokens": 500,
        "temperature": 0.65,
    }
    headers = {
        "Authorization": f"Bearer {config['GROQ_API_KEY']}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(config["GROQ_API_URL"], headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.RequestException as exc:
        print(f"[Groq Error] {exc}")
        return "I could not reach the chatbot service right now. Please try again in a moment."
