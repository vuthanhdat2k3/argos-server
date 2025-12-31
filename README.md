# Argos Translate Local Server

A simple REST API server for Argos Translate.

## Setup

1. **Create a Python virtual environment (recommended)**:
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server**:
   ```bash
   python server.py
   ```

The server will start on `http://127.0.0.1:5100`.

## API Endpoints

### Health Check
```
GET /health
```
Response: `{"status": "ok", "engine": "argos-translate"}`

### Get Available Languages
```
GET /languages
```
Response: `{"languages": [{"from": "en", "to": "vi", "name": "English -> Vietnamese"}, ...]}`

### Translate Text
```
POST /translate
Content-Type: application/json

{
  "q": "Hello world",
  "source": "en",
  "target": "vi"
}
```
Response: `{"translatedText": "Xin chào thế giới"}`

## Notes

- Language packages are downloaded automatically on first use
- First translation for a new language pair may take a few seconds to download the model
- All translations run locally - no internet required after downloading models
