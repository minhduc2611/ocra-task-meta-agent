# Buddha-Py - AI Agent Platform

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Weaviate instance (cloud or local)

### Setup

1. **Create a virtual environment**:
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** in your `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key
WEAVIATE_URL=your_weaviate_url
WEAVIATE_API_KEY=your_weaviate_api_key
EMBEDDING_MODEL=text-embedding-3-small

```
Notes:
- `OPENAI_API_KEY` is the API key for the OpenAI API.
- `WEAVIATE_URL` is the URL for the Weaviate instance.
- `WEAVIATE_API_KEY` is the API key for the Weaviate instance.
- `GOOGLE_PROJECT_ID` is the ID of the Google Cloud project. just create a new project in Google Cloud and get the project ID, and you good to go. Also, you need to enable the following APIs:
    - Vertex AI API
    - Speech-to-Text API


4. **Run the project**
- use `launch.json` to run the project
- or run `python main.py` to run the project
