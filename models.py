import peewee as pw

from flask_security import UserMixin, RoleMixin, PeeweeUserDatastore, current_user
from playhouse.flask_utils import FlaskDB
from playhouse.postgres_ext import BinaryJSONField

db_wrapper = FlaskDB()


class BaseModel(db_wrapper.Model):
    pass


class Role(RoleMixin, BaseModel):
    name = pw.CharField(unique=True)
    description = pw.TextField(null=True)
    permissions = pw.TextField(null=True)


class User(UserMixin, BaseModel):
    email = pw.TextField()
    password = pw.TextField()
    active = pw.BooleanField(default=True)
    fs_uniquifier = pw.TextField(null=False)
    confirmed_at = pw.DateTimeField(null=True)
    token = BinaryJSONField(default={})

    @classmethod
    def fetch_token(cls, name):
        return current_user.token.get(name)


class UserRoles(BaseModel):
    user = pw.ForeignKeyField(User, related_name='roles')
    role = pw.ForeignKeyField(Role, related_name='users')
    name = property(lambda self: self.role.name)
    description = property(lambda self: self.role.description)

    def get_permissions(self):
        return self.role.get_permissions()


class Day(BaseModel):
    user = pw.ForeignKeyField(User, backref="days")
    date = pw.DateField(unique=True)
    notes = pw.CharField(null=True)
    alcohol_doses = pw.IntegerField(null=True)
    mood = pw.IntegerField(null=True)
    tiredness_morning = pw.IntegerField(null=True)
    tiredness_evening = pw.IntegerField(null=True)
    nap_minutes = pw.IntegerField(null=True)
    office = pw.BooleanField(null=True)
    vacation = pw.BooleanField(null=True)

    @classmethod
    def get_or_create(cls, day, user, autosave=False):
        kwargs = {
            "user": user,
            "date": day,
        }
        try:
            return cls.get(**kwargs)
        except cls.DoesNotExist:
            day = cls(**kwargs)
            if autosave:
                day.save()
            return day


class Sleep(BaseModel):
    day = pw.ForeignKeyField(Day, backref="sleeps")
    provider = pw.CharField()
    duration_total = pw.IntegerField()
    duration_rem = pw.IntegerField()
    duration_deep = pw.IntegerField()
    duration_awake = pw.IntegerField()
    phases = BinaryJSONField(default={})
    score = pw.IntegerField(null=True)
    # UTC
    start = pw.DateTimeField()
    end = pw.DateTimeField()
    offset = pw.IntegerField()

    @classmethod
    def create_or_update(cls, day, provider, data: dict):
        try:
            sleep = cls.get(day=day, provider=provider)
            cls.update(**data).where(cls.id == sleep.id).execute()
        except cls.DoesNotExist:
            sleep = cls(day=day, provider=provider, **data)
            sleep.save()
        return sleep


def init_app(app):
    db_wrapper.init_app(app)
    app.user_datastore = PeeweeUserDatastore(db_wrapper, User, Role, UserRoles)
    return app


def init_db():
    db_wrapper.database.connect()
    db_wrapper.database.create_tables([Day, User, Sleep, Role, UserRoles])
    print("DB inited.")
