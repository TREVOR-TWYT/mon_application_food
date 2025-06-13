from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import base64
import os
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = 'b\xae\x1b\x02A\x83\x00\xd7X\xe4u\x83e\xb1\x1a\x84\x7f\xa8w\xcb\xc7O\xff\xfd\x01'  # Nécessaire pour les messages flash
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://trevor:TREFRIED1707@localhost/fooddb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèles (Personne, Food, Image, Ingredient, Allergie) 

# Modèle pour la table Personne
class Personne(db.Model):
    __tablename__ = 'personne'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    sexe = db.Column(db.String, nullable=False)

# Modèle pour la table Foods
class Food(db.Model):
    __tablename__ = 'foods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    image = db.Column(db.String, nullable=True)
    ingredients = db.relationship('Ingredient', backref='food', lazy=True)

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
        client = genai.Client(
            api_key=os.environ.get("AIzaSyD3ioFlYYUPA4gTqHmn2acvzuSpg-f21Qs"),
            endpoint="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyD3ioFlYYUPA4gTqHmn2acvzuSpg-f21Qs"
        )

        model = "gemini-2.5-pro-preview-06-05"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=question),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
        )

        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            response_text += chunk.text

        return response_text
        
    except Exception as e:
        print(f"Erreur lors de l'obtention de la réponse : {e}")
        return "Erreur lors de la génération de la réponse"

@app.route('/')
def Acceuil():
    return render_template('Acceuil.html')

@app.route('/poser-question', methods=['GET', 'POST'])
def poser_question():
    response = None
    if request.method == 'POST':
        question = request.form['question']
        response = obtenir_reponse_gemini(question)

    return render_template('poser_question.html', response=response)

@app.route('/personnes', methods=['POST'])
def add_personne():
    data = request.json
    new_personne = Personne(nom=data['name'], age=data['age'], sexe=data['sexe'])
    db.session.add(new_personne)
    db.session.commit()
    return jsonify({'message': 'Personne ajoutée!'}), 201

@app.route('/foods', methods=['POST'])
def add_food():
    data = request.json
    new_food = Food(name=data['name'], description=data.get('description'))
    db.session.add(new_food)
    db.session.commit()
    return jsonify({'message': 'Food ajouté!'}), 201

@app.route('/images', methods=['POST'])
def add_image():
    data = request.json
    new_image = Image(name=data['name'], food_id=data['food_id'], image=data['image'])
    db.session.add(new_image)
    db.session.commit()
    return jsonify({'message': 'Image ajoutée!'}), 201

@app.route('/ingredients', methods=['POST'])
def add_ingredient():
    data = request.json
    new_ingredient = Ingredient(name=data['name'], food_id=data['food_id'])
    db.session.add(new_ingredient)
    db.session.commit()
    return jsonify({'message': 'Ingrédient ajouté!'}), 201

@app.route('/allergies', methods=['POST'])
def add_allergie():
    data = request.json
    new_allergie = Allergie(personne_id=data['personne_id'], food_id=data['food_id'])
    db.session.add(new_allergie)
    db.session.commit()
    return jsonify({'message': 'Allergie ajoutée!'}), 201



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

@app.route('/ajouter', methods=['GET', 'POST'])
def ajouter():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        name_personne = request.form['name_personne']
        age_personne = request.form['age_personne']
        name_food = request.form['name_food']
        description_food = request.form['description_food']
        ingredient_names = request.form.getlist('ingredients')  # Liste d'ingrédients

        # Ajouter une nouvelle personne
        nouvelle_personne = Personne(name=name_personne, age=age_personne)
        db.session.add(nouvelle_personne)
        db.session.commit()  # Commiter pour obtenir l'ID

        # Ajouter une nouvelle nourriture
        nouvelle_nourriture = Food(name=name_food, description=description_food)
        db.session.add(nouvelle_nourriture)
        db.session.commit()  # Commiter pour obtenir l'ID

        # Ajouter les ingrédients
        for ingredient_name in ingredient_names:
            nouvel_ingredient = Ingredient(name=ingredient_name, food_id=nouvelle_nourriture.id)
            db.session.add(nouvel_ingredient)

        # Relier la personne à la nourriture
        manger_entry = Manger(personne_id=nouvelle_personne.id, food_id=nouvelle_nourriture.id)
        db.session.add(manger_entry)

        db.session.commit()  # Commiter toutes les modifications
        return "Données ajoutées avec succès!"

    return render_template('ajouter.html')  # Afficher le formulaire

    
if __name__ == '__main__':
    with app.app_context():  # Créer un contexte d'application
        db.create_all()  # Crée les tables si elles n'existent pas
    app.run(debug=True)