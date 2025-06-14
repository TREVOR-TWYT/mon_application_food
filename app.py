from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import base64
import os
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = 'b\xae\x1b\x02A\x83\x00\xd7X\xe4u\x83e\xb1\x1a\x84\x7f\xa8w\xcb\xc7O\xff\xfd\x01'  # Nécessaire pour les messages flash
app.config['SQLALCHEMY_DATABASE_URI'] ="postgresql+psycopg2://postgres:postgres@my_postgres:5432/foodapp"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

first_request_done = False

"""@app.before_request
def initialize_tables():
    global first_request_done
    if not first_request_done:
        db.create_all()  # Ou toute autre initialisation
        first_request_done = True  # Marquez comme fait"""

client = genai.Client(api_key='AIzaSyD3ioFlYYUPA4gTqHmn2acvzuSpg-f21Qs')

# Modèles (Personne, Food, Image, Ingredient, Allergie) 

# Modèle pour la table Personne
class Personne(db.Model):
    __tablename__ = 'personne'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sexe = db.Column(db.String, nullable=False)

# Modèle pour la table Foods
class Food(db.Model):
    __tablename__ = 'foods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    image = db.Column(db.String, nullable=True)
    ingredients = db.relationship('Ingredient', backref='foods', lazy=True)

class Manger(db.Model):
    __tablename__ = 'manger'
    id = db.Column(db.Integer, primary_key=True)
    personne_id = db.Column(db.Integer, db.ForeignKey('personne.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)

    # Relations avec Personne et Food
    personne = db.relationship('Personne', backref='manger', lazy=True)
    food = db.relationship('Food', backref='manger', lazy=True)

# Modèle pour la table Image
class Image(db.Model):
    __tablename__ = 'image'
    name = db.Column(db.String, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

# Modèle pour la table Ingrédient
class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    name = db.Column(db.String, primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), nullable=False)

# Modèle pour la table Allergies
class Allergie(db.Model):
    __tablename__ = 'allergies'
    personne_id = db.Column(db.Integer, db.ForeignKey('personne.id'), primary_key=True)
    food_id = db.Column(db.Integer, db.ForeignKey('foods.id'), primary_key=True)


def obtenir_reponse_gemini(question):
    try:
        chat = client.chats.create(model='gemini-2.0-flash')
        response = chat.send_message(question)

        # Extraction de la réponse
        if response.candidates and len(response.candidates) > 0:
            # Accéder au premier candidat
            first_candidate = response.candidates[0]
            # Accéder au contenu
            content = first_candidate.content
            # Extraire le texte
            text_response = content.parts[0].text
            
            return text_response
        else:
            return "Aucune réponse trouvée."

    except Exception as e:
        print(f"Erreur lors de l'obtention de la réponse : {e}")
        return "Erreur lors de la génération de la réponse"

@app.route("/", methods=["GET"])
def acceuil():
    return render_template('Acceuil.html')

@app.route('/poser-question', methods=['GET', 'POST'])
def poser_question():
    response = None
    if request.method == 'POST':
        question = request.form['question']
        response = obtenir_reponse_gemini(question)

    return render_template('poser_question.html', response=response)



@app.route('/images', methods=['POST'])
def add_image():
    data = request.json
    new_image = Image(name=data['name'], food_id=data['food_id'], image=data['image'])
    db.session.add(new_image)
    db.session.commit()
    return jsonify({'message': 'Image ajoutée!'}), 201


@app.route('/ajouter/allergie', methods=['GET', 'POST'])
def ajouter_allergie():
    if request.method == 'POST':
        food_id = request.form['food_id']
        personne_id = request.form['personne_id']  # Récupérer l'ID de la personne

        # Ajouter la nouvelle allergie
        nouvelle_allergie = Allergie(food_id=food_id, personne_id=personne_id)
        db.session.add(nouvelle_allergie)
        db.session.commit()

        return "Allergie ajoutée avec succès!"
    
    personnes = Personne.query.all()  # Récupérer toutes les personnes pour le formulaire
    nourritures = Food.query.all()
    return render_template('ajouter_allergie.html', personnes=personnes, nourritures=nourritures)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        personne = Personne.query.filter_by(nom=name).first()
        if personne:
            # Récupérer les nourritures mangées par la personne
            nourritures = db.session.query(Food).join(Allergie).filter(Allergie.personne_id == personne.id).all()
            return render_template('nourritures.html', nourritures=[food.name for food in nourritures])
        flash('Nom d\'utilisateur non trouvé.')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/nourritures', methods=['GET'])
def get_nourritures():
    foods = Food.query.all()
    nouritures_data = []
    for food in foods:
        ingredients = Ingredient.query.filter_by(food_id=food.id).all()
        ingr_list = [ingredient.name for ingredient in ingredients]
        nouritures_data.append({
            'name': food.name,
            'description': food.description,
            'ingredients': ingr_list
        })
    return jsonify(nouritures_data), 200

@app.route('/selectionner', methods=['GET'])
def selectionner():
    return render_template('selectionner.html')

@app.route('/ajouter/personne', methods=['GET', 'POST'])
def ajouter_personne():
    if request.method == 'POST':
        name_personne = request.form['name_personne']
        age_personne = request.form['age_personne']
        sexe_personne = request.form['sexe_personne']  # Récupération du sexe

        nouvelle_personne = Personne(name=name_personne, age=age_personne, sexe=sexe_personne)
        db.session.add(nouvelle_personne)
        db.session.commit()

        return "Personne ajoutée avec succès!"
    
    return render_template('ajouter_personne.html')


@app.route('/ajouter/nourriture', methods=['GET', 'POST'])
def ajouter_nourriture():
    if request.method == 'POST':
        name_food = request.form['name_food']
        description_food = request.form['description_food']
        image_url = request.form.get('image_url')
        ingredient_names = request.form.getlist('ingredients')  # Récupérer la liste d'ingrédients

        # Ajouter la nouvelle nourriture
        nouvelle_nourriture = Food(name=name_food, description=description_food, image=image_url)
        db.session.add(nouvelle_nourriture)
        db.session.commit()  # Commiter pour obtenir l'ID

        # Ajouter les ingrédients
        for ingredient_name in ingredient_names:
            if ingredient_name:  # Vérifier que le nom de l'ingrédient n'est pas vide
                nouvel_ingredient = Ingredient(name=ingredient_name.strip(), food_id=nouvelle_nourriture.id)
                db.session.add(nouvel_ingredient)

        db.session.commit()  # Commiter toutes les modifications
        return "Nourriture ajoutée avec succès!"
    
    return render_template('ajouter_nourriture.html')

@app.route('/manger', methods=['GET', 'POST'])
def manger():
    if request.method == 'POST':
        personne_id = request.form['personne_id']
        food_id = request.form['food_id']
        manger_entry = Manger(personne_id=personne_id, food_id=food_id)
        db.session.add(manger_entry)
        db.session.commit()
        return "Relation ajoutée avec succès!"
    
    personnes = Personne.query.all()  # Récupérer toutes les personnes
    foods = Food.query.all()  # Récupérer toutes les nourritures
    return render_template('manger.html', personnes=personnes, foods=foods)

    
if __name__ == '__main__':
    with app.app_context():  # Créer un contexte d'application
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=True, host='0.0.0.0')