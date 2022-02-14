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

    def sleep_score(self):
        return round(
            sum([s.computed_score() for s in self.sleeps]) / len(self.sleeps) / 100
        )


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

    def computed_score(self):
        """https://github.com/abulte/sleep.france.sh/issues/1"""
        # TODO: maybe use min base values for ideal instead of mean
        ideal_duration = 8 * 3600
        sleep_gain = self.duration_total - ideal_duration
        ideal_deep = self.duration_total * 10 / 100
        deep_gain = self.duration_deep - ideal_deep
        ideal_rem = self.duration_total * 22.5 / 100
        rem_gain = self.duration_rem - ideal_rem
        return sleep_gain + deep_gain + rem_gain


class Stress(BaseModel):
    day = pw.ForeignKeyField(Day, backref="stresses")
    provider = pw.CharField()
    duration_total = pw.IntegerField()
    stress_values = BinaryJSONField(default={})
    battery_values = BinaryJSONField(default={})
    # UTC
    start = pw.DateTimeField()
    end = pw.DateTimeField()
    offset = pw.IntegerField()

    @classmethod
    def create_or_update(cls, day, data: dict, provider="garmin"):
        try:
            stress = cls.get(day=day, provider=provider)
            cls.update(**data).where(cls.id == stress.id).execute()
        except cls.DoesNotExist:
            stress = cls(day=day, provider=provider, **data)
            stress.save()
        return stress


def init_app(app):
    db_wrapper.init_app(app)
    app.user_datastore = PeeweeUserDatastore(db_wrapper, User, Role, UserRoles)
    return app


def init_db():
    db_wrapper.database.connect()
    db_wrapper.database.create_tables([Day, User, Sleep, Role, UserRoles, Stress])
    print("DB inited.")
