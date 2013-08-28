"""
Tinman data serializers for use with sessions and other data objects.

"""
import datetime
import json
try:
    import msgpack
except ImportError:
    msgpack = None
import pickle


class Serializer(object):
    """Base data serialization object used by session adapters and other
    classes. To use different data serialization formats, extend this class and
    implement the serialize and deserialize methods.

    """
    def deserialize(self, data):
        """Return the deserialized data.

        :param str data: The data to deserialize
        :rtype: dict
        :raises: NotImplementedError

        """
        raise NotImplementedError

    def serialize(self, data):
        """Return self._data as a serialized string.

        :param str data: The data to serialize
        :rtype: str

        """
        raise NotImplementedError

    def _deserialize_datetime(self, data):
        """Take any values coming in as a datetime and deserialize them

        """
        for key in data:
            if isinstance(data[key], dict):
                if data[key].get('type') == 'datetime':
                    data[key] = \
                        datetime.datetime.fromtimestamp(data[key]['value'])
        return data

    def _serialize_datetime(self, data):
        for key in data.keys():
            if isinstance(data[key], datetime.datetime):
                data[key] = {'type': 'datetime',
                             'value': data[key].strftime('%s')}
        return data


class Pickle(Serializer):
    """Serializes the data in Pickle format"""
    def deserialize(self, data):
        """Return the deserialized data.

        :param str data: The data to deserialize
        :rtype: dict

        """
        if not data:
            return dict()
        return self._deserialize_datetime(pickle.loads(data))

    def serialize(self, data):
        """Return self._data as a serialized string.

        :param str data: The data to serialize
        :rtype: str

        """
        return pickle.dumps(self._serialize_datetime(data))


class JSON(Serializer):
    """Serializes the data in JSON format"""
    def deserialize(self, data):
        """Return the deserialized data.

        :param str data: The data to deserialize
        :rtype: dict

        """
        return self._deserialize_datetime(json.loads(data, encoding='utf-8'))

    def serialize(self, data):
        """Return the data as serialized string.

        :param dict data: The data to serialize
        :rtype: str

        """
        return json.dumps(self._serialize_datetime(data), ensure_ascii=False)


class MsgPack(Serializer):
    """Serializes the data in msgpack format"""

    def deserialize(self, data):
        """Return the deserialized data.

        :param str data: The data to deserialize
        :rtype: dict

        """
        return self._deserialize_datetime(msgpack.loads(data))

    def serialize(self, data):
        """Return the data as serialized string.

        :param dict data: The data to serialize
        :rtype: str

        """
        return msgpack.dumps(self._serialize_datetime(data))
