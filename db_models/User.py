from orm import Model, String, Integer, DateTime, Float
from objects.globals import db, metadata

class User(Model):

    __tablename__ = "users"
    __database__ = db
    __metadata__ = metadata

    id = Integer(primary_key=True)

    user_id = Integer()
    username = String(max_length=100)
    created = DateTime()
    balance = Float()