FROM python:3.12-slim

# Instala dependências do Chrome e do Selenium
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Instala Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Define diretório da aplicação
WORKDIR /app
COPY . /app

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Executa o script
CMD ["python", "main.py"]
