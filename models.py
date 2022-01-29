import peewee as pw
from playhouse.flask_utils import FlaskDB

db_wrapper = FlaskDB()


class BaseModel(db_wrapper.Model):
    pass


class Day(BaseModel):
    date = pw.DateField(unique=True)
    notes = pw.CharField(null=True)
    alcohol_doses = pw.IntegerField(null=True)
    mood = pw.IntegerField(null=True)
    tiredness_morning = pw.IntegerField(null=True)
    tiredness_evening = pw.IntegerField(null=True)
    nap_minutes = pw.IntegerField(null=True)
    office = pw.BooleanField(null=True)
    vacation = pw.BooleanField(null=True)
    # last night
    sleep_score = pw.IntegerField(null=True)
    sleep_feeling = pw.IntegerField(null=True)
    # end last night

    @classmethod
    def get_or_create(cls, day):
        try:
            return cls.get(date=day)
        except cls.DoesNotExist:
            return cls(date=day)


def init_app(app):
    db_wrapper.init_app(app)
    return app


def init_db():
    db_wrapper.database.connect()
    db_wrapper.database.create_tables([Day, ])
    print("DB inited.")
