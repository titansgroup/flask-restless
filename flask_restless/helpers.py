"""
    flask.ext.restless.helpers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Helper functions for Flask-Restless.

    :copyright: 2012 Jeffrey Finkelstein <jeffrey.finkelstein@gmail.com>
    :license: GNU AGPLv3+ or BSD

"""


def unicode_keys_to_strings(dictionary):
    """Returns a new dictionary with the same mappings as `dictionary`, but
    with each of the keys coerced to a string (by calling :func:`str(key)`).

    This function is intended to be used for Python 2.5 compatibility when
    unpacking a dictionary to provide keyword arguments to a function or
    method. For example::

        >>> def func(a=1, b=2):
        ...     return a + b
        ...
        >>> d = {u'a': 10, u'b': 20}
        >>> func(**d)
        Traceback (most recent call last):
          File "<stdin>", line 1, in <module>
        TypeError: func() keywords must be strings
        >>> func(**unicode_keys_to_strings(d))
        30

    """
    return dict((str(k), v) for k, v in dictionary.iteritems())


def infer_backend(model):
    """Returns a string identifying the backend (a database abstraction layer
    like SQLAlchemy, Flask-SQLAlchemy, or Elixir) for which `model` has been
    defined.

    This function returns one of ``'sqlalchemy'``, ``'flask-sqlalchemy'``, and
    ``'elixir'``, or ``None`` if the backend could not be inferred. Note that
    this function is relatively dumb, and simply checks for the presence of
    attributes on the model which signify that it was defined using one of the
    above backends.

    This function should correctly infer the backend regardless of whether the
    concrete tables have been created (or destroyed); that is, this works
    before your tables are created, after they are created, and after they have
    been destroyed.

    .. versionadded:: 0.6

    """
    if hasattr(model, 'table'):
        return 'elixir'
    if hasattr(model, 'query') and hasattr(model, 'query_class'):
        return 'flask-sqlalchemy'
    if hasattr(model, '__tablename__'):
        return 'sqlalchemy'
    return None
