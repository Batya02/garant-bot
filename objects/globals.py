from aiogram import Bot, Dispatcher
from databases import Database
from sqlalchemy import MetaData
from typing import List, Optional

bot:Bot  = None
config:dict = None
dp:Dispatcher = None

db:Database = None
metadata:MetaData = None
db_engine = None

state_type:Optional[str] = ""
payment_services:List[str] = ["Qiwi", "Yoomoney"]