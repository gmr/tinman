"""
Custom session serializers

"""
import json
try:
    import msgpack
except ImportError:
    msgpack = None

from tinman import session


class JSONSerializer(session.SessionSerializer):
    """Serializes the session data in JSON format"""
    def _deserialize(self, data):
        """Return the deserialized session data.

        :param str data: The data to deserialize
        :rtype: dict

        """
        return json.loads(data)

    def _serialize(self):
        """Return the session data as serialized string.

        :rtype: str

        """
        return json.dumps(self._data)


class MsgPackSerializer(session.SessionSerializer):
    """Serializes the session data in msgpack format"""
    def _deserialize(self, data):
        """Return the deserialized session data.

        :param str data: The data to deserialize
        :rtype: dict

        """
        return msgpack.loads(data)

    def _serialize(self):
        """Return the session data as serialized string.

        :rtype: str

        """
        return msgpack.dumps(self._data)
