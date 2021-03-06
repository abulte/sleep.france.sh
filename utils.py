import typing as t
from datetime import date

from flask.json import JSONEncoder
from werkzeug.routing import BaseConverter, ValidationError


class ISODateConverter(BaseConverter):

    def to_python(self, value: str) -> t.Any:
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValidationError()

    def to_url(self, value: t.Any) -> str:
        return value.isoformat()


class ISODateJSONEncoder(JSONEncoder):
    """Custom JSON encoder for dates"""
    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()
        return super().default(o)
