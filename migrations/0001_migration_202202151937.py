# auto-generated snapshot
from peewee import *
import datetime
import peewee
import playhouse.postgres_ext


snapshot = Snapshot()


@snapshot.append
class User(peewee.Model):
    email = TextField()
    password = TextField()
    active = BooleanField(default=True)
    fs_uniquifier = TextField()
    confirmed_at = DateTimeField(null=True)
    token = playhouse.postgres_ext.BinaryJSONField(default={}, index=True)
    class Meta:
        table_name = "user"


@snapshot.append
class Day(peewee.Model):
    user = snapshot.ForeignKeyField(backref='days', index=True, model='user')
    date = DateField(unique=True)
    notes = CharField(max_length=255, null=True)
    alcohol_doses = IntegerField(null=True)
    mood = IntegerField(null=True)
    tiredness_morning = IntegerField(null=True)
    tiredness_evening = IntegerField(null=True)
    nap_minutes = IntegerField(null=True)
    office = BooleanField(null=True)
    vacation = BooleanField(null=True)
    class Meta:
        table_name = "day"


@snapshot.append
class Role(peewee.Model):
    name = CharField(max_length=255, unique=True)
    description = TextField(null=True)
    permissions = TextField(null=True)
    class Meta:
        table_name = "role"


@snapshot.append
class Sleep(peewee.Model):
    day = snapshot.ForeignKeyField(backref='sleeps', index=True, model='day')
    provider = CharField(max_length=255)
    duration_total = IntegerField()
    duration_rem = IntegerField()
    duration_deep = IntegerField()
    duration_awake = IntegerField()
    phases = playhouse.postgres_ext.BinaryJSONField(default={}, index=True)
    score = IntegerField(null=True)
    start = DateTimeField()
    end = DateTimeField()
    offset = IntegerField()
    class Meta:
        table_name = "sleep"


@snapshot.append
class Stress(peewee.Model):
    day = snapshot.ForeignKeyField(backref='stresses', index=True, model='day')
    provider = CharField(max_length=255)
    duration_total = IntegerField()
    stress_values = playhouse.postgres_ext.BinaryJSONField(default={}, index=True)
    battery_values = playhouse.postgres_ext.BinaryJSONField(default={}, index=True)
    start = DateTimeField()
    end = DateTimeField()
    offset = IntegerField()
    class Meta:
        table_name = "stress"


@snapshot.append
class UserRoles(peewee.Model):
    user = snapshot.ForeignKeyField(backref='roles', index=True, model='user')
    role = snapshot.ForeignKeyField(backref='users', index=True, model='role')
    class Meta:
        table_name = "userroles"


