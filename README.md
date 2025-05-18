# 🧘‍♀️ Manasvi – Your Indian Mental Wellness Companion 🇮🇳💬🌿

**Manasvi** (मनस्वी) is an AI-powered mental wellness chatbot built especially for Indian users. Whether you're feeling stressed, anxious, or just need a break — Manasvi is here to chat, guide you through **Pranayama breathing techniques**, suggest **yoga asanas**, track your mood, and help you meditate with soothing Indian melodies.

---

## 🇮🇳 India-Focused Wellness Features

- 🙏 **Yoga & Pranayama Guidance**: Get personalized suggestions for breathing techniques like *Anulom Vilom* and *Bhramari*, or asanas like *Balasana* and *Shavasana*.
- 🎶 **Indian Calming Music**: Meditate with gentle sitar, flute, or rain ragas.

---

## 🌼 Why Manasvi?

- Named after the Sanskrit word *Manasvi*, meaning “of pure mind” 🕊️
- Brings ancient Indian wellness practices to modern tech interfaces
- Empowers mental health with AI, not stigma

---

## 🚀 Features

- 💬 **AI Chatbot**: Chat via text or voice using an Azure GPT-4-powered assistant.
- 🎤 **Voice to Text**: Speak your thoughts — OpenAI Whisper will convert them to text.
- 📈 **Mood Tracker**: Record how you're feeling and view progress over time with interactive Plotly graphs.
- 🧘 **Meditation Corner**: Play calming music and set a timer to relax your mind.
- 🔐 **User Login System**: Secure signup/login so your data stays yours.
- 🔒 **Data Isolation**: Each user’s data is stored separately and securely.

---

## 🛠️ Tech Stack

| Layer           | Technology Used                                       |
|----------------|--------------------------------------------------------|
| 💻 Frontend     | HTML and CSS                                           |
| 🧠 Chatbot      | GROQ API                                               |
| 🎙️ Voice Input  | [OpenAI Whisper](https://openai.com/research/whisper)  |
| 📊 Graphs       | Chart.js                                              |
| 🗄️ Database     | SQLite (with user data isolation)                     |
| 🔐 Auth         | Python + `bcrypt` for password hashing                |

---

## 🚀 How to Run the Project

Follow these steps to set up and run the project locally:

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/yourproject.git
cd yourproject
```

### 2. Create and Activate a Virtual Environment

**On macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Set Up Environment Variables

Create a `.env` file in the root directory and add your API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
WHISPER_API_KEY=your_openai_whisper_api_key_here
```

> ⚠️ **Note:** Never commit your `.env` file to version control.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
python app.py
```

The application should now be running. Follow the console instructions or visit the localhost URL if using a web framework.

---


## Snapshots
![Demo Image](static/img2.png)

