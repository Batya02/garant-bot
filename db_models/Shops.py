from orm import Model, Integer, Boolean, Float, DateTime
from objects.globals import db, metadata

class Shops(Model):
    __tablename__ = "shops"
    __database__ = db
    __metadata__ = metadata

    id = Integer(primary_key=True)

    user_id = Integer()
    created = DateTime()
    price = Float()
    other_chat_id = Integer()
    ended = Boolean()