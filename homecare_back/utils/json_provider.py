from datetime import date, time, datetime
from flask.json.provider import DefaultJSONProvider

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (date, time, datetime)):
            return obj.isoformat()

        return super().default(obj)

