from orm import Model, Integer, Boolean, DateTime, Float
from objects.globals import db, metadata
from datetime import datetime as dt

class OutputApplication(Model):
    __tablename__ = "output_applications" 
    __database__  = db
    __metadata__  = metadata

    id      = Integer(primary_key=True)
    user_id = Integer()
    amount  = Float()
    created = DateTime(default=dt.now())
    status  = Boolean(default=True)