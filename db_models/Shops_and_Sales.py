from orm import Model, Integer, String, Boolean, Float, DateTime
from objects.globals import db, metadata
from datetime import datetime as dt

class SAS(Model):
    __tablename__ = "shops_and_sales"
    __database__ = db
    __metadata__ = metadata

    id = Integer(primary_key=True)

    main_user = Integer()
    created = DateTime(default=dt.now())
    uncreated = DateTime(default=dt.now())
    price = Float()
    not_main_user = Integer()
    type = String(max_length=4)
    ended = Boolean()