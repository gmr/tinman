"""
A generic mapping object that allows access to attributes and via getters and
setters.

"""
import collections
import inspect
import json


class Mapping(collections.Mapping):
    """A generic data object that provides access to attributes via getters
    and setters, built in serialization via JSON, iterator methods
    and other Mapping methods.

    """
    def __init__(self, **kwargs):
        """Assign all kwargs passed in as attributes of the object."""
        self.from_dict(kwargs)

    def as_dict(self):
        """Return this object as a dict value.

        :rtype: dict

        """
        return dict(self.items())

    def from_dict(self, values):
        """Assign the values from the dict passed in. All items in the dict
        are assigned as attributes of the object.

        :param dict values: The dictionary of values to assign to this mapping

        """
        for k in values.keys():
            setattr(self, k, values[k])

    def clear(self):
        """Clear all set attributes in the mapping.

        """
        for key in self.keys():
            delattr(self, key)

    def dumps(self):
        """Return a JSON serialized version of the mapping.

        :rtype: str|unicode

        """
        return json.dumps(self.as_dict(), encoding='utf-8', ensure_ascii=False)

    def loads(self, value):
        """Load in a serialized value, overwriting any previous values.

        :param str|unicode value: The serialized value

        """
        self.from_dict(json.loads(value, encoding='utf-8'))

    def __contains__(self, item):
        """Check to see if the attribute name passed in exists.

        :param str item: The attribute name

        """
        return item in self.keys()

    def __eq__(self, other):
        """Test another mapping for equality against this one

        :param mapping other: The mapping to test against this one
        :rtype: bool

        """
        if not isinstance(other, self.__class__):
            return False
        return all([getattr(self, k) == getattr(other, k)
                    for k in self.keys()])

    def __delitem__(self, key):
        """Delete the attribute from the mapping.

        :param str key: The attribute name
        :raises: KeyError

        """
        if key not in self.keys():
            raise KeyError(key)
        delattr(self, key)

    def __getitem__(self, item):
        """Get an item from the mapping.

        :param str item: The attribute name
        :rtype: mixed
        :raises: KeyError

        """
        if item not in self.keys():
            raise KeyError(item)
        return getattr(self, item)

    def __hash__(self):
        """Return the hash value of the items

        :rtype: int

        """
        return hash(self.items())

    def __iter__(self):
        """Iterate through the keys in the mapping object.

        :rtype: listiterator

        """
        return self.iterkeys()

    def __len__(self):
        """Return the number of attributes in this mapping object.

        :rtype: int

        """
        return len(self.keys())

    def __ne__(self, other):
        """Test two mappings for inequality.

        :param mapping other: The mapping to test against this one
        :rtype: bool

        """
        return not self.__eq__(other)


    def __setitem__(self, key, value):
        """Set an item in the mapping

        :param str key: The attribute name
        :param mixed value: The value to set

        """
        setattr(self, key, value)

    def keys(self):
        """Return a list of attribute names for the mapping.

        :rtype: list

        """
        return sorted([k for k in dir(self) if
                       k[0:1] != '_' and k != 'keys' and not k.isupper() and
                       not inspect.ismethod(getattr(self, k)) and
                       not (hasattr(self.__class__, k) and
                            isinstance(getattr(self.__class__, k),
                                       property)) and
                       not isinstance(getattr(self, k), property)])

    def get(self, key, default=None):
        """Get the value of key, passing in a default value if it is not set.

        :param str key: The attribute to get
        :param mixed default: The default value
        :rtype: mixed

        """
        return getattr(self, key, default)

    def iterkeys(self):
        """Iterate through the attribute names for this mapping.

        :rtype: listiterator

        """
        return iter(self.keys())

    def iteritems(self):
        """Iterate through a list of the attribute names and their values.

        :rtype: listiterator

        """
        return iter(self.items())

    def itervalues(self):
        """Iterate through a list of the attribute values for this mapping.

        :rtype: listiterator

        """
        return iter(self.values())

    def items(self):
        """Return a list of attribute name and value tuples for this mapping.

        :rtype: list

        """
        return [(k, getattr(self, k)) for k in self.keys()]

    def set(self, key, value):
        """Set the value of key.

        :param str key: The attribute to set
        :param mixed value: The value to set
        :raises: KeyError

        """
        return setattr(self, key, value)

    def values(self):
        """Return a list of values for this mapping in attribute name order.

        :rtype list

        """
        return [getattr(self, k) for k in self.keys()]
