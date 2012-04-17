"""
    tests.test_manager
    ~~~~~~~~~~~~~~~~~~

    Provides unit tests for the :mod:`flask_restless.manager` module.

    :copyright: 2012 Jeffrey Finkelstein <jeffrey.finkelstein@gmail.com>
    :license: GNU AGPLv3+ or BSD

"""
import datetime
from unittest2 import skipUnless
from unittest2 import TestCase
from unittest2 import TestSuite

from flask import Flask
from flask import json
try:
    from flask.ext.sqlalchemy import SQLAlchemy
except:
    has_flask_sqlalchemy = False
else:
    has_flask_sqlalchemy = True
try:
    from elixir import create_all
    from elixir import Date
    from elixir import DateTime
    from elixir import drop_all
    from elixir import Entity
    from elixir import Field
    from elixir import Float
    from elixir import ManyToOne
    from elixir import metadata
    from elixir import OneToMany
    from elixir import session
    from elixir import setup_all
    from elixir import Unicode
except:
    has_elixir = False
else:
    has_elixir = True

from flask.ext.restless import APIManager
from flask.ext.restless.views import _get_columns

from .helpers import FlaskTestBase
from .helpers import setUpModule
from .helpers import tearDownModule
from .helpers import TestSupport


__all__ = ['APIManagerTest', 'FSATest', 'ElixirTest']


dumps = json.dumps
loads = json.loads


class APIManagerTest(TestSupport):
    """Unit tests for the :class:`flask_restless.manager.APIManager` class.

    """

    def test_init_app(self):
        """Tests for initializing the Flask application after instantiating the
        :class:`flask.ext.restless.APIManager` object.

        """
        # initialize the Flask application
        self.manager.init_app(self.flaskapp, self.session)

        # create an API
        self.manager.create_api(self.Person)

        # make a request on the API
        #client = app.test_client()
        response = self.app.get('/api/person')
        self.assertEqual(response.status_code, 200)

    def test_create_api(self):
        """Tests that the :meth:`flask_restless.manager.APIManager.create_api`
        method creates endpoints which are accessible by the client, only allow
        specified HTTP methods, and which provide a correct API to a database.

        """
        # create three different APIs for the same model
        self.manager.create_api(self.Person, methods=['GET', 'POST'])
        self.manager.create_api(self.Person, methods=['PATCH'],
                                url_prefix='/api2')
        self.manager.create_api(self.Person, methods=['GET'],
                                url_prefix='/readonly')

        # test that specified endpoints exist
        response = self.app.post('/api/person', data=dumps(dict(name='foo')))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(loads(response.data)['id'], 1)
        response = self.app.get('/api/person')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)

        # test that non-specified methods are not allowed
        response = self.app.delete('/api/person/1')
        self.assertEqual(response.status_code, 405)
        response = self.app.patch('/api/person/1',
                                  data=dumps(dict(name='bar')))
        self.assertEqual(response.status_code, 405)

        # test that specified endpoints exist
        response = self.app.patch('/api2/person/1',
                                  data=dumps(dict(name='bar')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)['id'], 1)
        self.assertEqual(loads(response.data)['name'], 'bar')

        # test that non-specified methods are not allowed
        response = self.app.get('/api2/person/1')
        self.assertEqual(response.status_code, 405)
        response = self.app.delete('/api2/person/1')
        self.assertEqual(response.status_code, 405)
        response = self.app.post('/api2/person',
                                 data=dumps(dict(name='baz')))
        self.assertEqual(response.status_code, 405)

        # test that the model is the same as before
        response = self.app.get('/readonly/person')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)
        self.assertEqual(loads(response.data)['objects'][0]['name'], 'bar')

    def test_different_collection_name(self):
        """Tests that providing a different collection name exposes the API at
        the corresponding URL.

        """
        self.manager.create_api(self.Person, methods=['POST', 'GET'],
                                collection_name='people')

        response = self.app.post('/api/people', data=dumps(dict(name='foo')))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(loads(response.data)['id'], 1)

        response = self.app.get('/api/people')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)

        response = self.app.get('/api/people/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)['id'], 1)

    def test_allow_functions(self):
        """Tests that the ``allow_functions`` keyword argument makes a
        :http:get:`/api/eval/...` endpoint available.

        """
        self.manager.create_api(self.Person, allow_functions=True)
        response = self.app.get('/api/eval/person', data=dumps(dict()))
        self.assertNotEqual(response.status_code, 400)
        self.assertEqual(response.status_code, 204)

    def test_disallow_functions(self):
        """Tests that if the ``allow_functions`` keyword argument if ``False``,
        no endpoint will be made available at :http:get:`/api/eval/...`.

        """
        self.manager.create_api(self.Person, allow_functions=False)
        response = self.app.get('/api/eval/person')
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 404)

    def test_include_columns(self):
        """Tests that the `include_columns` argument specifies which columns to
        return in the JSON representation of instances of the model.

        """
        all_columns = _get_columns(self.Person)
        # allow all
        self.manager.create_api(self.Person, include_columns=None,
                                url_prefix='/all')
        self.manager.create_api(self.Person, include_columns=all_columns,
                                url_prefix='/all2')
        # allow some
        self.manager.create_api(self.Person, include_columns=('name', 'age'),
                                url_prefix='/some')
        # allow none
        self.manager.create_api(self.Person, include_columns=(),
                                url_prefix='/none')

        # create a test person
        self.manager.create_api(self.Person, methods=['POST'],
                                url_prefix='/add')
        d = dict(name=u'Test', age=10, other=20,
                 birth_date=datetime.date(1999, 12, 31).isoformat())
        response = self.app.post('/add/person', data=dumps(d))
        self.assertEqual(response.status_code, 201)
        personid = loads(response.data)['id']

        # get all
        response = self.app.get('/all/person/%s' % personid)
        for column in 'name', 'age', 'other', 'birth_date', 'computers':
            self.assertIn(column, loads(response.data))
        response = self.app.get('/all2/person/%s' % personid)
        for column in 'name', 'age', 'other', 'birth_date', 'computers':
            self.assertIn(column, loads(response.data))

        # get some
        response = self.app.get('/some/person/%s' % personid)
        for column in 'name', 'age':
            self.assertIn(column, loads(response.data))
        for column in 'other', 'birth_date', 'computers':
            self.assertNotIn(column, loads(response.data))

        # get none
        response = self.app.get('/none/person/%s' % personid)
        for column in 'name', 'age', 'other', 'birth_date', 'computers':
            self.assertNotIn(column, loads(response.data))

    def test_different_urls(self):
        """Tests that establishing different URL endpoints for the same model
        affect the same database table.

        """
        methods = frozenset(('get', 'patch', 'post', 'delete'))
        # create a separate endpoint for each HTTP method
        for method in methods:
            url = '/%s' % method
            self.manager.create_api(self.Person, methods=[method.upper()],
                                    url_prefix=url)

        # test for correct requests
        response = self.app.get('/get/person')
        self.assertEqual(response.status_code, 200)
        response = self.app.post('/post/person', data=dumps(dict(name='Test')))
        self.assertEqual(response.status_code, 201)
        response = self.app.patch('/patch/person/1',
                                  data=dumps(dict(name='foo')))
        self.assertEqual(response.status_code, 200)
        response = self.app.delete('/delete/person/1')
        self.assertEqual(response.status_code, 204)

        # test for incorrect requests
        response = self.app.get('/post/person')
        self.assertEqual(response.status_code, 405)
        response = self.app.get('/patch/person/1')
        self.assertEqual(response.status_code, 405)
        response = self.app.get('/delete/person/1')
        self.assertEqual(response.status_code, 405)

        response = self.app.post('/get/person')
        self.assertEqual(response.status_code, 405)
        response = self.app.post('/patch/person/1')
        self.assertEqual(response.status_code, 405)
        response = self.app.post('/delete/person/1')
        self.assertEqual(response.status_code, 405)

        response = self.app.patch('/get/person')
        self.assertEqual(response.status_code, 405)
        response = self.app.patch('/post/person')
        self.assertEqual(response.status_code, 405)
        response = self.app.patch('/delete/person/1')
        self.assertEqual(response.status_code, 405)

        response = self.app.delete('/get/person')
        self.assertEqual(response.status_code, 405)
        response = self.app.delete('/post/person')
        self.assertEqual(response.status_code, 405)
        response = self.app.delete('/patch/person/1')
        self.assertEqual(response.status_code, 405)

        # test that the same model is updated on all URLs
        response = self.app.post('/post/person', data=dumps(dict(name='Test')))
        self.assertEqual(response.status_code, 201)
        response = self.app.get('/get/person/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)['name'], 'Test')
        response = self.app.patch('/patch/person/1',
                                  data=dumps(dict(name='Foo')))
        self.assertEqual(response.status_code, 200)
        response = self.app.get('/get/person/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)['name'], 'Foo')
        response = self.app.delete('/delete/person/1')
        self.assertEqual(response.status_code, 204)
        response = self.app.get('/get/person/1')
        self.assertEqual(response.status_code, 404)

    def test_session_class(self):
        """Test for providing a session class instead of a sesssion instance.

        """
        manager = APIManager(self.flaskapp, session=self.Session)
        manager.create_api(self.Person, methods=['GET', 'POST'])
        response = self.app.get('/api/person')
        self.assertEqual(response.status_code, 200)
        response = self.app.post('/api/person', data=dumps(dict(name='foo')))
        self.assertEqual(response.status_code, 201)
        response = self.app.get('/api/person/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)['id'], 1)


class FSATest(FlaskTestBase):
    """Tests which use models defined using Flask-SQLAlchemy instead of pure
    SQLAlchemy.

    """

    def setUp(self):
        """Creates the Flask application, the APIManager, the database, and the
        Flask-SQLAlchemy models.

        """
        super(FSATest, self).setUp()

        # initialize SQLAlchemy and Flask-Restless
        self.db = SQLAlchemy(self.flaskapp)
        self.manager = APIManager(self.flaskapp, flask_sqlalchemy_db=self.db)

        # for the sake of brevity...
        db = self.db

        # declare the models
        class Computer(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.Unicode, unique=True)
            vendor = db.Column(db.Unicode)
            buy_date = db.Column(db.DateTime)
            owner_id = db.Column(db.Integer, db.ForeignKey('person.id'))

        class Person(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.Unicode, unique=True)
            age = db.Column(db.Float)
            other = db.Column(db.Float)
            birth_date = db.Column(db.Date)
            computers = db.relationship('Computer',
                                        backref=db.backref('owner',
                                                           lazy='dynamic'))
        self.Person = Person
        self.Computer = Computer

        # create all the tables required for the models
        self.db.create_all()

    def tearDown(self):
        """Drops all tables from the temporary database."""
        self.db.drop_all()

    def test_flask_sqlalchemy(self):
        """Tests that :class:`flask.ext.restless.APIManager` correctly exposes
        models defined using Flask-SQLAlchemy.

        """
        # create three different APIs for the same model
        self.manager.create_api(self.Person, methods=['GET', 'POST'])
        self.manager.create_api(self.Person, methods=['PATCH'],
                                url_prefix='/api2')
        self.manager.create_api(self.Person, methods=['GET'],
                                url_prefix='/readonly')

        # test that specified endpoints exist
        response = self.app.post('/api/person', data=dumps(dict(name='foo')))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(loads(response.data)['id'], 1)
        response = self.app.get('/api/person')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)
        response = self.app.patch('/api2/person/1',
                                  data=dumps(dict(name='bar')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)['id'], 1)
        self.assertEqual(loads(response.data)['name'], 'bar')

        # test that the model is the same as before
        response = self.app.get('/readonly/person')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)
        self.assertEqual(loads(response.data)['objects'][0]['name'], 'bar')


class ElixirTest(FlaskTestBase):
    """Tests which use models defined using Elixir instead of pure SQLAlchemy.

    """

    def setUp(self):
        """Creates the Flask application, the APIManager, the database, and the
        Elixir models.

        """
        super(ElixirTest, self).setUp()

        # initialize Elixir and Flask-Restless
        metadata.bind = self.flaskapp.config['SQLALCHEMY_DATABASE_URI']
        self.manager = APIManager(self.flaskapp, session=session)

        # declare the models
        class Computer(Entity):
            name = Field(Unicode, unique=True)
            vendor = Field(Unicode)
            buy_date = Field(DateTime)
            owner = ManyToOne('Person')

        class Person(Entity):
            name = Field(Unicode, unique=True)
            age = Field(Float)
            other = Field(Float)
            birth_date = Field(Date)
            computers = OneToMany('Computer')

        self.Person = Person
        self.Computer = Computer

        # create all the tables required for the models
        setup_all()
        create_all()

    def tearDown(self):
        """Drops all tables from the temporary database."""
        drop_all()

    def test_elixir(self):
        """Tests that :class:`flask.ext.restless.APIManager` correctly exposes
        models defined using Elixir.

        """
        # create three different APIs for the same model
        self.manager.create_api(self.Person, methods=['GET', 'POST'],
                                collection_name='person')
        self.manager.create_api(self.Person, methods=['PATCH'],
                                url_prefix='/api2', collection_name='person')
        self.manager.create_api(self.Person, methods=['GET'],
                                url_prefix='/readonly',
                                collection_name='person')

        # test that specified endpoints exist
        response = self.app.post('/api/person', data=dumps(dict(name='foo')))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(loads(response.data)['id'], 1)
        response = self.app.get('/api/person')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)
        response = self.app.patch('/api2/person/1',
                                  data=dumps(dict(name='bar')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(loads(response.data)['id'], 1)
        self.assertEqual(loads(response.data)['name'], 'bar')

        # test that the model is the same as before
        response = self.app.get('/readonly/person')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(loads(response.data)['objects']), 1)
        self.assertEqual(loads(response.data)['objects'][0]['id'], 1)
        self.assertEqual(loads(response.data)['objects'][0]['name'], 'bar')

# skipUnless should be used as a decorator, but Python 2.5 doesn't have
# decorators.
FSATest = skipUnless(has_flask_sqlalchemy,
                     'Flask-SQLAlchemy not found.')(FSATest)
ElixirTest = skipUnless(has_elixir, 'Elixir not found.')(ElixirTest)


def load_tests(loader, standard_tests, pattern):
    """Returns the test suite for this module."""
    suite = TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(APIManagerTest))
    suite.addTest(loader.loadTestsFromTestCase(ElixirTest))
    suite.addTest(loader.loadTestsFromTestCase(FSATest))
    return suite
