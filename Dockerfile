# Utiliser une image de base Python
FROM python:3.10-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /FOODAPP

# Copier les fichiers de votre projet dans le conteneur
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .

# Exposer le port de l'application
EXPOSE 5000


# Commande pour exécuter l'application
CMD ["flask", "run", "--host=0.0.0.0"]

