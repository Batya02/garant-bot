from orm import Model, Integer, String, Boolean, Float, DateTime
from objects.globals import db, metadata

class Sales(Model):
    __tablename__ = "sales"
    __database__ = db
    __metadata__ = metadata

    id = Integer(primary_key=True)

    user_id = Integer()
    created = DateTime()
    price = Float()
    other_chat_id = Integer()
    ended = Boolean()
