from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Category(id={self.id}, name={self.name})"

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    supplier = db.Column(db.String(100))
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())

    category = db.relationship('Category', backref=db.backref('inventory_items', lazy=True))

    def __repr__(self):
        return f"Inventory(id={self.id}, name={self.name}, quantity={self.quantity}, price={self.price}, description={self.description}, image_url={self.image_url}, category={self.category}, supplier={self.supplier}, date_added={self.date_added})"

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'price': self.price,
            'description': self.description,
            'image_url': self.image_url,
            'category': self.category.serialize(),
            'supplier': self.supplier,
            'date_added': self.date_added.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        
