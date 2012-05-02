"""
    flask.ext.restless.backends
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Backend-specific helper functions.

    :copyright: 2012 Jeffrey Finkelstein <jeffrey.finkelstein@gmail.com>
    :license: GNU AGPLv3+ or BSD

"""
import heapq


class Backend(object):
    """Base class for backend-specific functionality.

    In order for Flask-Restless to provide support for specific database
    abstraction layers, it must know some backend-specific functionality. In
    order to make Flask-Restless aware, define a subclass of this class and
    implement the methods described below. In addition, each subclass must set
    the :attr:`name` attribute to be an identifying string for the backend.

    For example, a subclass which provides functionality for pure SQLAlchemy
    might look like this::

        # Step 1 - subclass Backend or SQLALchemyBackendBase (if your backend
        # is a layer on top of SQLAlchemy).
        class SQLAlchemyBackend(SQLAlchemyBackendBase):

            # Step 2 - provide an identifying string for your backend.
            name = 'sqlalchemy'

            # Step 3 - implement infer(), which is necessary for Flask-Restless
            # to guess whether a given model is defined for this particular
            # backend.
            @staticmethod
            def infer(model, *args, **kw):
                return hasattr(model, '__tablename__')

            # Step 3 - implement query(), which provides a consistent interface
            # for Flask-Restless to query a database.
            @staticmethod
            def query(model, session, *args, **kw):
                return session.query(model)

    Note that the first two parameters of both :meth:`infer` and :meth:`query`
    are ``model`` and ``session``, but you don't have to use them (as seen in
    the definition of ``infer`` in the above example). However, you should
    still provide ``*args`` and ``**kw`` parameters.

    """

    #: An identifying name for this backend.
    name = None

    @staticmethod
    def infer(model, session, *args, **kw):
        """Returns ``True`` if and only if `model` has been defined for use
        with the backend which this class represents.

        Subclasses must implement this static method, and must decorate it with
        the :func:`staticmethod` decorator.

        """
        raise NotImplementedError('Subclasses must override infer().')

    @staticmethod
    def query(model, session, *args, **kw):
        """Returns a query-like object on the specified database model.

        A "query-like object" is something like a SQLAlchemy query object. That
        means it must have at least a ``filter_by`` function.

        Subclasses must implement this static method, and must decorate it with
        the :func:`staticmethod` decorator.

        Pre-condition: `model` is not ``None``.

        """
        raise NotImplementedError('Subclasses must override _query().')


class SQLAlchemyBackendBase(Backend):
    """A base class for backends which are based on SQLAlchemy (including pure
    SQLAlchemy, Flask-SQLAlchemy, and Elixir).

    Use this as the base class for backends which are derived from SQLAlchemy.

    """
    pass


class SQLAlchemyBackend(SQLAlchemyBackendBase):
    """Represents a pure SQLAlchemy backend."""

    name = 'sqlalchemy'

    @staticmethod
    def infer(model, *args, **kw):
        return hasattr(model, '__tablename__')

    @staticmethod
    def query(model, session, *args, **kw):
        return session.query(model)


class FlaskSQLAlchemyBackend(SQLAlchemyBackendBase):
    """Represents a Flask-SQLAlchemy backend."""

    name = 'flask-sqlalchemy'

    @staticmethod
    def infer(model, *args, **kw):
        return hasattr(model, 'query') and hasattr(model, 'query_class')

    @staticmethod
    def query(model, *args, **kw):
        return model.query


class ElixirBackend(SQLAlchemyBackendBase):
    """Represents an Elixir backend."""

    name = 'elixir'

    @staticmethod
    def infer(model, *args, **kw):
        return hasattr(model, 'table')

    @staticmethod
    def query(model, *args, **kw):
        return model.query


def infer_backend(model, session=None):
    """Returns a string identifying the backend (a database abstraction layer
    like SQLAlchemy, Flask-SQLAlchemy, or Elixir) for which `model` has been
    defined.

    `session` may also be provided, though some backend inference tests will
    ignore it. `session` represents the session in which database transactions
    will be made for `model`; this may help some backend inference tests infer
    the type of backend.

    This function returns one of the backends registered in :data:`backends` or
    ``None`` if the backend could not be inferred. Note that the inference
    functions are relatively dumb---most simply check for the presence of
    attributes on the model which signify that it was defined for use with a
    particular backend.

    If this function can correctly infer the backend, it can do so regardless
    of whether the concrete tables have been created (or destroyed); that is,
    this works before your tables are created, after they are created, and
    after they have been destroyed.

    .. versionadded:: 0.6

    """
    for backend in (b for p, b in sorted(backends)):
        if backend.infer(model, session):
            return backend
    return None


def register_backend(backend, priority=None):
    """Registers `backend` with the list of known backends.

    `backend` is a subclass of :class:`Backend`.

    If `priority` is not ``None``, the backend will be added with the specified
    priority, an integer between 0 and 100 which indicates the order in which
    the backend will be tested in the :func:`infer_backend`
    function. Specifying a priority is necessary for situations in which a test
    would return ``True`` for multiple backends, and so more specific backends
    should be tested first (that is, with a higher priority). If `priority` is
    ``None``, `backend` will be added with priority higher than any other
    backend so that it is checked first.

    .. versionadded:: 0.6

    """
    if priority is None:
        # since `backends` is a heap, `backends[0]` is the minimum, i.e. the
        # highest priority
        priority = max(0, backends[0] - 1)
    heapq.heappush(backends, (priority, backend))


def unregister_backend(backend):
    """Removes `backend` from the list of known backends.

    .. versionadded:: 0.6

    """
    try:
        i = [b for p, b in backends].index(backend)
    except ValueError:
        return False
    return backends.pop(i)


#: The list of pairs of known backends with their priority when attempting to
#: infer the backend type of a model.
#:
#: Since this list is actually maintained as a heap, backends should not be
#: added directly to this list; instead, use the :func:`register_backend`
#: function to register a new backend along with its priority.
#:
#: .. versionadded:: 0.6
backends = [
    (25, ElixirBackend),
    (50, FlaskSQLAlchemyBackend),
    (75, SQLAlchemyBackend)
    ]
heapq.heapify(backends)
