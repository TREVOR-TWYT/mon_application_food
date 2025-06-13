from app import app, db, Personne, Food, Image, Manger, Ingredient

# Créer un contexte d'application
with app.app_context():
    # Créez quelques personnes
    person1 = Personne(id=1, nom='Alice', age=30, sexe='F')
    person2 = Personne(id=2, nom='Bob', age=25, sexe='M')

    # Exemple d'ajout d'une entrée
    entry = Manger(personne_id=1, food_id=1)  # ID de la personne et ID de la nourriture
    db.session.add(entry)
    ingr1 = Ingredient(name = "tomate,viande", food_id=0)
    ingr2 = Ingredient(name = "arachide,poissons", food_id=0)
    db.session.add(ingr1)
    db.session.add(ingr2)
    Food1 = Food(name="tapioca", description="Le sauveur", )

    # Ajouter les objets à la session
    db.session.add(person1)
    db.session.add(person2)

    # Commit les changements
    db.session.commit()

print("Base de données peuplée avec succès!")
