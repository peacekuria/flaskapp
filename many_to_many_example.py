from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///many_to_many_app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy database
db = SQLAlchemy(app)




# ASSOCIATION TABLE (Bridge Table)
# This is the key to Many-to-Many relationships
# It doesn't have a model, just defines the relationship
post_tags = db.Table(
    'post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)




# Tag model
class Tag(db.Model, SerializerMixin):
    __tablename__ = "tags"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    
    # Many-to-Many relationship with Posts
    # Uses the association table 'post_tags'
    posts = db.relationship(
        'Post',
        secondary=post_tags,
        back_populates='tags'
    )
    
    # SERIALIZE_RULES EXAMPLES for Tag:
    
    # Option 1: Include posts but exclude circular reference to avoid infinite loops
    # serialize_rules = ("-posts.tags",)
    
    # Option 2: Don't include posts at all (simpler, no relationships)
    # serialize_rules = ()
    
    # Option 3: Include everything (might cause circular reference)
    # serialize_rules = ()




# Post model with Many-to-Many relationship
class Post(db.Model, SerializerMixin):
    __tablename__ = "posts"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    
    # Foreign key to link to user (from your original code)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="posts")
    
    # Many-to-Many relationship with Tags
    # Uses the association table 'post_tags'
    tags = db.relationship(
        'Tag',
        secondary=post_tags,
        back_populates='posts'
    )
    
    # SERIALIZE_RULES EXAMPLES for Post:
    
    # Option 1: Include tags, user, but prevent circular references
    # This is usually the best choice for Many-to-Many
    serialize_rules = ("-user.posts", "-tags.posts")
    
    # Option 2: Include everything (might cause circular reference)
    # serialize_rules = ()
    
    # Option 3: Exclude relationships entirely (simplest)
    # serialize_rules = ()




# User model (extended from your original code)
class User(db.Model, SerializerMixin):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    
    posts = db.relationship(
        "Post",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Include posts but prevent circular reference
    serialize_rules = ("-posts.user",)




# API ROUTES FOR MANY-TO-MANY OPERATIONS

@app.route("/posts/<int:post_id>/tags", methods=["POST"])
def add_tag_to_post(post_id):
    """Add a tag to a specific post"""
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    # Find or create tag
    tag = Tag.query.filter_by(name=data["tag_name"]).first()
    if not tag:
        tag = Tag(name=data["tag_name"])
        db.session.add(tag)
    
    # Add tag to post (association table handles the Many-to-Many)
    if tag not in post.tags:
        post.tags.append(tag)
    
    db.session.commit()
    
    return jsonify(post.to_dict()), 200


@app.route("/posts/<int:post_id>/tags/<int:tag_id>", methods=["DELETE"])
def remove_tag_from_post(post_id, tag_id):
    """Remove a tag from a specific post"""
    post = Post.query.get_or_404(post_id)
    tag = Tag.query.get_or_404(tag_id)
    
    # Remove tag from post (association table handles the Many-to-Many)
    if tag in post.tags:
        post.tags.remove(tag)
    
    db.session.commit()
    
    return jsonify(post.to_dict()), 200


@app.route("/tags", methods=["GET"])
def get_tags():
    """Get all tags with their posts"""
    tags = Tag.query.all()
    return jsonify([tag.to_dict() for tag in tags]), 200


@app.route("/posts", methods=["GET"])
def get_posts():
    """Get all posts with their tags"""
    posts = Post.query.all()
    return jsonify([post.to_dict() for post in posts]), 200


# Example of how different serialize_rules affect the output:

def demonstrate_serialize_rules():
    """
    This function shows how different serialize_rules configurations
    affect the JSON output
    """
    
    # Example data setup
    tag1 = Tag(name="Python")
    tag2 = Tag(name="Flask")
    tag3 = Tag(name="SQLAlchemy")
    
    post1 = Post(title="Flask Tutorial", content="Learn Flask...")
    post1.tags = [tag1, tag2]  # Many-to-Many assignment
    
    post2 = Post(title="SQLAlchemy Guide", content="Learn SQLAlchemy...")
    post2.tags = [tag1, tag3]  # Many-to-Many assignment
    
    tag1.posts = [post1, post2]  # Reverse relationship
    tag2.posts = [post1]
    tag3.posts = [post2]
    
    # With serialize_rules = ("-user.posts", "-tags.posts"):
    # Post output: {"id": 1, "title": "...", "content": "...", "tags": [{"id": 1, "name": "Python"}, ...]}
    # Tag output: {"id": 1, "name": "Python", "posts": [{"id": 1, "title": "...", "content": "..."}, ...]}
    
    # Without serialize_rules, you might get circular references:
    # Post -> tags -> posts -> tags -> posts -> ... (infinite loop!)
    
    pass




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        
        # Demo data
        user = User(name="John Doe")
        post = Post(title="My First Post", content="Hello World!", user=user)
        tag1 = Tag(name="beginner")
        tag2 = Tag(name="tutorial")
        
        post.tags = [tag1, tag2]
        
        db.session.add_all([user, post, tag1, tag2])
        db.session.commit()
        
        print("=== SERIALIZE_RULES DEMONSTRATION ===")
        print("\n1. Post with serialize_rules = ('-user.posts', '-tags.posts'):")
        print(post.to_dict())
        
        print("\n2. Tag with serialize_rules = ('-posts.tags',):")
        print(tag1.to_dict())
        
        print("\n3. What happens if you don't prevent circular references:")
        print("(This would cause infinite recursion in real JSON serialization)")
        
    app.run(debug=True)
