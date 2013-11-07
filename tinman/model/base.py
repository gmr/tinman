"""
Base tinman data models. The Model class is the base model that all other base
model classes extend. StorageModel defines the interfaces for models with built
in storage functionality.

Specific model storage base classes exist in the tornado.model package.

Example use::

    from tornado import gen
    from tornado import web
    from tinman.handlers import redis_handlers
    from tinman.model.redis import AsyncRedisModel


    class ExampleModel(AsyncRedisModel):
        name = None
        age = None
        location = None


    class Test(redis_handlers.AsynchronousRedisRequestHandler):

        @web.asynchronous
        @gen.engine
        def get(self, *args, **kwargs):
            model = ExampleModel(self.get_argument('id'),
                                 redis_client=self.redis)
            yield model.fetch()
            self.finish(model.as_dict())

        @web.asynchronous
        @gen.engine
        def post(self, *args, **kwargs):
            model = ExampleModel(self.get_argument('id', None),
                                 redis_client=self.redis)

            # Assign the posted values, requiring at least a name
            model.name = self.get_argument('name')
            model.age = self.get_argument('age', None)
            model.location = self.get_argument('location', None)

            # Save the model
            result = yield model.save()
            if result:
                self.set_status(201)
                self.finish(model.as_dict())
            else:
                raise web.HTTPError(500, 'Could not save model')

"""
import collections
import inspect
import json
import time
import uuid

SERIALIZER = json


class Model(collections.Mapping):
    """A data object that provides attribute level assignment and retrieval of
    values, serialization and deserialization, the ability to load values from
    a dict and dump them to a dict, and Mapping and iterator behaviors.

    Base attributes are provided for keeping track of when the model was created
    and when it was last updated.

    If model attributes are passed into the constructor, they will be assigned
    to the model upon creation.

    :param str item_id: An id for the model, defaulting to a random UUID
    :param dict kwargs: Additional kwargs passed in

    """
    created_at = None
    last_updated_at = None

    def __init__(self, item_id=None, **kwargs):
        """Create a new instance of the model, passing in a id value."""
        self.id = item_id or str(uuid.uuid4())
        self.created_at = int(time.time())
        self.last_updated_at = None

        # If values are in the kwargs that match the model keys, assign them
        for k in [k for k in kwargs.keys() if k in self.keys()]:
            setattr(self, k, kwargs[k])

    def as_dict(self):
        """Return the model as a dict value.

        :rtype: dict

        """
        return dict(self.items())

    def from_dict(self, value):
        """Set the values of the model based upon the content of the passed in
        dictionary.

        :param dict value: The dictionary of values to assign to this model

        """
        for key in self.keys():
            setattr(self, key, value.get(key, None))

    def dumps(self):
        """Return a serialized version of the model using the serializer that
        is assigned to model.serializer (default: json).

        :rtype: str|unicode

        """
        return SERIALIZER.dumps(dict(self.items()), encoding='utf-8')

    def loads(self, value):
        """Load in a serialized value and assign it to the current model

        :param str|unicode value: The serialized value

        """
        self.from_dict(SERIALIZER.loads(value, encoding='utf-8'))

    def __contains__(self, item):
        """Check to see if the attribute name passed in is available in this
        model.

        :param str item: The attribute name

        """
        return item in self.keys()

    def __eq__(self, other):
        """Test another model for equality against this one

        :param Model other: The model to test against this one
        :rtype: bool

        """
        if not isinstance(other, self.__class__):
            return False
        return all([getattr(self, k) == getattr(other, k)
                    for k in self.keys()])

    def __getitem__(self, item):
        if item not in self.keys():
            raise KeyError(item)
        return getattr(self, item)

    def __iter__(self):
        return super(Model, self).__iter__()

    def __len__(self):
        return 1

    def __ne__(self, other):
        """Test two models for inequality.

        :param Model other: The model to test against this one
        :rtype: bool

        """
        return not self.__eq__(other)

    def keys(self):
        """Return a list of attribute names for the model.

        :rtype: list

        """
        return sorted([k for k in dir(self.__class__)
                       if k not in dir(super(self.__class__)) and
                          k[0:1] != '_' and k != 'keys' and not k.isupper() and
                          not inspect.ismethod(getattr(self, k)) and
                          not inspect.ismethoddescriptor(getattr(self.__class__,
                                                                 k)) and
                          not isinstance(getattr(self.__class__, k), property)])

    def get(self, key, default=None):
        """Get the value of key, passing in a default value if it is not set.

        :param str key: The attribute to get
        :param mixed default: The default value
        :rtype: mixed
        :raises: KeyError

        """
        if key not in self.keys():
            return KeyError
        return getattr(self, key, default)

    def iterkeys(self):
        """Iterate through the attribute names for this model.

        :rtype: listiterator

        """
        return iter(self.keys())

    def iteritems(self):
        """Iterate through a list of the attribute names and their values.

        :rtype: listiterator

        """
        return iter(self.items())

    def itervalues(self):
        """Iterate through a list of the attribute values for this model.

        :rtype: listiterator

        """
        return iter(self.values())

    def items(self):
        """Return a list of attribute name and value tuples for this model.

        :rtype: list

        """
        return [(k, getattr(self, k)) for k in self.keys()]

    def values(self):
        """Return a list of values for this model in attribute sort order

        :rtype list

        """
        return [getattr(self, k) for k in self.keys()]


class StorageModel(Model):
    """A base model that defines the behavior for models with storage backends.

    :param str item_id: An id for the model, defaulting to a random UUID
    :param dict kwargs: Additional kwargs passed in

    """
    def __init__(self, item_id=None, **kwargs):
        super(StorageModel, self).__init__(item_id, **kwargs)
        if self.id:
            self.fetch()

    def fetch(self):
        """Fetch the data for the model from storage and assign the values.

        :raises: NotImplementedError

        """
        raise NotImplementedError("Must extend this method")

    def save(self):
        """Store the model. This method is defined by a model storage mixin form
        tinman.model.mixins.

        :raises: NotImplementedError

        """
        raise NotImplementedError("Must extend this method")
