"""
    tests.test_helpers
    ~~~~~~~~~~~~~~~~~~

    Provides unit tests for the :mod:`flask_restless.helpers` module.

    :copyright: 2012 Jeffrey Finkelstein <jeffrey.finkelstein@gmail.com>
    :license: GNU AGPLv3+ or BSD

"""
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
    import elixir as elx
except:
    has_elixir = False
else:
    has_elixir = True
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from flask.ext.restless.helpers import infer_backend


__all__ = ['BackendInferenceTest']


dumps = json.dumps
loads = json.loads


class BackendInferenceTest(TestCase):
    """Tests for inferring the type of database abstraction layer based on a
    given model class.

    """

    def test_sqlalchemy(self):
        """Tests that SQLAlchemy is correctly inferred from a SQLAlchemy model.

        """
        engine = sa.create_engine('sqlite://', convert_unicode=True)
        Base = declarative_base()
        Base.metadata.bind = engine

        class Test(Base):
            __tablename__ = 'person'
            id = sa.Column(sa.Integer, primary_key=True)
            name = sa.Column(sa.Unicode, unique=True)
        self.assertEqual(infer_backend(Test), 'sqlalchemy')
        Base.metadata.create_all()
        self.assertEqual(infer_backend(Test), 'sqlalchemy')
        # TODO put this in tearDown
        Base.metadata.drop_all()
        self.assertEqual(infer_backend(Test), 'sqlalchemy')

    def test_flask_sqlalchemy(self):
        """Tests that Flask-SQLAlchemy is correctly inferred from a
        Flask-SQLAlchemy model.

        """
        app = Flask(__name__)
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db = SQLAlchemy(app)

        class Test(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.Unicode, unique=True)
        self.assertEqual(infer_backend(Test), 'flask-sqlalchemy')
        db.create_all()
        self.assertEqual(infer_backend(Test), 'flask-sqlalchemy')
        # TODO put this in tearDown
        db.drop_all()
        self.assertEqual(infer_backend(Test), 'flask-sqlalchemy')

    def test_elixir(self):
        """Tests that Elixir is correctly inferred from an Elixir model."""
        app = Flask(__name__)
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        elx.metadata.bind = 'sqlite://'

        class Test(elx.Entity):
            name = elx.Field(elx.Unicode, unique=True)
        self.assertEqual(infer_backend(Test), 'elixir')
        elx.setup_all()
        self.assertEqual(infer_backend(Test), 'elixir')
        elx.create_all()
        self.assertEqual(infer_backend(Test), 'elixir')
        # TODO put this in tearDown
        elx.drop_all()
        self.assertEqual(infer_backend(Test), 'elixir')

    test_flask_sqlalchemy = \
        skipUnless(has_flask_sqlalchemy,
                   'Flask-SQLAlchemy not found.')(test_flask_sqlalchemy)

    test_elixir = skipUnless(has_elixir, 'Elixir not found.')(test_elixir)


def load_tests(loader, standard_tests, pattern):
    """Returns the test suite for this module."""
    suite = TestSuite()
    suite.addTest(loader.loadTestsFromTestCase(BackendInferenceTest))
    return suite
