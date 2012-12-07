"""
    tests.helpers
    ~~~~~~~~~~~~~

    Provides helper functions for unit tests in this package.

    :copyright: 2012 Jeffrey Finkelstein <jeffrey.finkelstein@gmail.com>
    :license: GNU AGPLv3+ or BSD

"""
import datetime
from unittest2 import TestCase

from flask import Flask
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from flask.ext.restless import APIManager


class FlaskTestBase(TestCase):
    """Base class for tests which use a Flask application."""

    def setUp(self):
        """Creates the Flask application and the APIManager."""
        super(FlaskTestBase, self).setUp()

        # create the Flask application
        app = Flask(__name__)
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        self.flaskapp = app

        # create the test client
        self.app = app.test_client()


class TestSupport(FlaskTestBase):
    """Base class for tests which use a database and have an
    :class:`flask_restless.APIManager` with a :class:`flask.Flask` app object.

    The test client for the :class:`flask.Flask` application is accessible to
    test functions at ``self.app`` and the :class:`flask_restless.APIManager`
    is accessible at ``self.manager``.

    """

    def setUp(self):
        """Creates the Flask application and the APIManager."""
        super(TestSupport, self).setUp()

        # initialize SQLAlchemy and Flask-Restless
        app = self.flaskapp
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'],
                               convert_unicode=True)
        self.Session = sessionmaker(autocommit=False, autoflush=False,
                                    bind=engine)
        self.session = scoped_session(self.Session)
        self.Base = declarative_base()
        self.Base.metadata.bind = engine
        #Base.query = self.session.query_property()
        self.manager = APIManager(app, self.session)

        # declare the models
        class Computer(self.Base):
            __tablename__ = 'computer'
            id = Column(Integer, primary_key=True)
            name = Column(Unicode, unique=True)
            vendor = Column(Unicode)
            buy_date = Column(DateTime)
            owner_id = Column(Integer, ForeignKey('person.id'))
            owner = relationship('Person')



        class Person(self.Base):
            __tablename__ = 'person'
            id = Column(Integer, primary_key=True)
            name = Column(Unicode, unique=True)
            age = Column(Float)
            other = Column(Float)
            birth_date = Column(Date)
            computers = relationship('Computer')

            def save(self):
                self.session.add(instance)
                self.session.commit()


        class LazyComputer(self.Base):
            __tablename__ = 'lazycomputer'
            id = Column(Integer, primary_key=True)
            name = Column(Unicode)
            ownerid = Column(Integer, ForeignKey('lazyperson.id'))

        class LazyPerson(self.Base):
            __tablename__ = 'lazyperson'
            id = Column(Integer, primary_key=True)
            name = Column(Unicode)
            computers = relationship('LazyComputer',
                                     backref=backref('owner', lazy='dynamic'))

        class Planet(self.Base):
            __tablename__ = 'planet'
            name = Column(Unicode, primary_key=True)

        class Star(self.Base):
            __tablename__ = 'star'
            id = Column(Integer, primary_key=True)
            inception_time = Column(DateTime, nullable=True)

        self.Person = Person
        self.LazyComputer = LazyComputer
        self.LazyPerson = LazyPerson
        self.Computer = Computer
        self.Planet = Planet
        self.Star = Star

        # create all the tables required for the models
        self.Base.metadata.create_all()

    def tearDown(self):
        """Drops all tables from the temporary database."""
        #self.session.remove()
        self.Base.metadata.drop_all()


class TestSupportPrefilled(TestSupport):
    """Base class for tests which use a database and have an
    :class:`flask_restless.APIManager` with a :class:`flask.Flask` app object.

    The test client for the :class:`flask.Flask` application is accessible to
    test functions at ``self.app`` and the :class:`flask_restless.APIManager`
    is accessible at ``self.manager``.

    The database will be prepopulated with five ``Person`` objects. The list of
    these objects can be accessed at ``self.people``.

    """

    def setUp(self):
        """Creates the database, the Flask application, and the APIManager."""
        # create the database
        super(TestSupportPrefilled, self).setUp()
        # create some people in the database for testing
        lincoln = self.Person(name=u'Lincoln', age=23, other=22,
                              birth_date=datetime.date(1900, 1, 2))
        mary = self.Person(name=u'Mary', age=19, other=19)
        lucy = self.Person(name=u'Lucy', age=25, other=20)
        katy = self.Person(name=u'Katy', age=7, other=10)
        john = self.Person(name=u'John', age=28, other=10)
        self.people = [lincoln, mary, lucy, katy, john]
        self.session.add_all(self.people)
        self.session.commit()
