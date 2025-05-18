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
