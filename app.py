
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy database
db = SQLAlchemy(app)




# User model representing users in the database
class User(db.Model, SerializerMixin):
    __tablename__ = "users"

    # User ID (primary key)
    id = db.Column(db.Integer, primary_key=True)
    
    # User name (required field)
    name = db.Column(db.String, nullable=False)

    # One-to-many relationship with posts
    posts = db.relationship(
        "Post",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Include posts in serialization, but prevent circular reference
    serialize_rules = ("-posts.user",)



# Post model representing posts in the database
class Post(db.Model, SerializerMixin):
    __tablename__ = "posts"

    # Post ID (primary key)
    id = db.Column(db.Integer, primary_key=True)
    
    # Post title (required field)
    title = db.Column(db.String, nullable=False)
    
    # Post content (required field)
    content = db.Column(db.String, nullable=False)

    # Foreign key to link to user
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    # Many-to-one relationship with user
    user = db.relationship("User", back_populates="posts")

    # Include user in serialization, but prevent circular reference
    serialize_rules = ("-user.posts",)




# API Routes


# GET /users - Retrieve all users
@app.route("/users", methods=["GET"])
def get_users():
    # Query all users from database
    users = User.query.all()
    
    # Convert users to JSON and return
    return jsonify([user.to_dict() for user in users]), 200


# POST /users - Create a new user
@app.route("/users", methods=["POST"])
def create_user():
    # Get JSON data from request
    data = request.get_json()

    # Create new user with provided name
    new_user = User(name=data["name"])
    
    # Add user to database session
    db.session.add(new_user)
    
    # Save changes to database
    db.session.commit()

    # Return created user data
    return jsonify(new_user.to_dict()), 201




# Application Entry Point

if __name__ == "__main__":
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Start Flask development server
    app.run(debug=True)