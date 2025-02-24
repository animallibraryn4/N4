FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Run both the bot and a simple HTTP server
CMD python bot.py & python -m http.server 8000
