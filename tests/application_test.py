import mock
import sys
from tornado import web
try:
    import unittest2 as unittest
except ImportError:
    import unittest
sys.path.insert(0, '..')

from tinman import application


class ApplicationTests(unittest.TestCase):

    def setUp(self):

        self._mock_obj = mock.Mock(spec=application.TinmanApplication)


    def test_load_translations(self):

        with mock.patch('tornado.locale.load_translations') as mock_load:


            path = '/foo'
            print application.TinmanApplication._load_translations(self._mock_obj, path)
            mock_load.assert_called_once_with(path)






class AttributeTests(unittest.TestCase):

    def test_add_attribute_exists(self):
        obj = application.TinmanAttributes()
        obj.add('test_attr', 'test')
        self.assertTrue('test_attr' in obj)

    def test_add_attribute_matches(self):
        obj = application.TinmanAttributes()
        value = 'Test Value'
        obj.add('test_attr', value)
        self.assertEqual(obj.test_attr, value)

    def test_add_attribute_raises(self):
        obj = application.TinmanAttributes()
        value = 'Test Value'
        obj.add('test_attr', value)
        self.assertRaises(AttributeError, obj.add, 'test_attr', value)

    def test_set_attribute_matches(self):
        obj = application.TinmanAttributes()
        value = 'Test Value'
        obj.test_attr = value
        self.assertEqual(obj.test_attr, value)

    def test_set_overwrite_attribute(self):
        obj = application.TinmanAttributes()
        obj.test_attr = 'First Value'
        value = 'Test Value'
        obj.test_attr = value
        self.assertEqual(obj.test_attr, value)

    def test_attribute_in_obj(self):
        obj = application.TinmanAttributes()
        obj.test_attr = 'First Value'
        self.assertTrue('test_attr' in obj)

    def test_attribute_not_in_obj(self):
        obj = application.TinmanAttributes()
        self.assertFalse('test_attr' in obj)

    def test_attribute_delete(self):
        obj = application.TinmanAttributes()
        obj.test_attr = 'Foo'
        del obj.test_attr
        self.assertFalse('test_attr' in obj)

    def test_attribute_remove(self):
        obj = application.TinmanAttributes()
        obj.test_attr = 'Foo'
        obj.remove('test_attr')
        self.assertFalse('test_attr' in obj)

    def test_attribute_remove_raises(self):
        obj = application.TinmanAttributes()
        self.assertRaises(AttributeError, obj.remove, 'test_attr')
