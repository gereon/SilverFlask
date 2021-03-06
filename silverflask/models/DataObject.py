from sqlalchemy.ext.declarative import declared_attr
from wtforms import fields
from flask_wtf import Form
from wtforms.ext.sqlalchemy.orm import model_fields
from sqlalchemy import event
from silverflask import db
from silverflask.models.OrderedForm import OrderedFormFactory
from silverflask.helper import uncamel

from flask import request
from flask_user import current_user


class CannotCreateError(PermissionError):
    pass
Form
class CannotUpdateError(PermissionError):
    pass

class CannotDeleteError(PermissionError):
    pass

# class DataObjectMetaQuery(cls):
#     """
#     This should return a query that conforms to
#     the class based parameters like:
#     default_sort
#     etc.
#     """
#     pass

class DataObject(object):
    """
    The DataObject class is the basic building block of any CMS
    Element. It is a mixin that provides three basic database columns:

    Attributes:

    :ivar id: Primary key, integer id (use for joins and relationships)
    :ivar created_on: the datetime when the DataObject was created
    :ivar last_modified: the datetime when the DataObject was last modified
    """
    @declared_attr
    def __tablename__(cls):
        """tablename, defaults to the classname in lowercase"""
        return cls.__name__.lower()

    id = db.Column(db.Integer(), primary_key=True)
    created_on = db.Column(db.DateTime, default=db.func.now())
    last_modified = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    singular_name = None
    plural_name = None

    # has_one = {}
    # has_many = {}
    # many_many = {}
    # belongs_many_many = {}

    default_order = None

    auto_form_exclude = ['id', 'created_on', 'last_modified']

    # summary_fields = []
    # searchable_fields = []
    # allowed_actions = []

    # class CMSForm(Form):
    # name = fields.StringField("asdsadsa")
    #     submit = fields.SubmitField("Submit")

    def __new__(cls, *args, **kwargs):
        def before_insert_listener(mapper, connection, target):
            for c in target.__class__.mro():
                if hasattr(c, "before_insert"):
                    c.before_insert(mapper, connection, target)

        def before_update_listener(mapper, connection, target):
            for c in target.__class__.mro():
                if hasattr(c, "before_update"):
                    c.before_update(mapper, connection, target)

        event.listen(cls, 'before_insert', before_insert_listener)
        event.listen(cls, 'before_update', before_update_listener)

        event.listen(cls, 'before_insert', lambda m, c, t: t.can_create(m, c))
        event.listen(cls, 'before_update', lambda m, c, t: t.can_edit(m, c))
        event.listen(cls, 'before_delete', lambda m, c, t: t.can_delete(m, c))

        if not cls.singular_name:
            cls.singular_name = uncamel(cls.__name__)
            cls.plural_name = uncamel(cls.__name__ + "s")

        return super().__new__(cls)


    @classmethod
    def query_factory(cls):
        return db.session.query(cls).order_by(cls.last_modified.desc())

    @classmethod
    def get_cms_form(cls):
        """
        Build and return Form class.

        If you want to define your custom CMS Object, you likely want to override the default CMS Form. E.g.::

            from wtforms import fields
            def get_cms_form(cls):
                form = super().get_cms_form()
                form.textfield = fields.StringField("Textfield")
                return form

        :returns:  Form Class (has to be instantiated!).
        """
        if hasattr(cls, "CMSForm"):
            return cls.CMSForm
        form_factory = OrderedFormFactory()

        form_fields = model_fields(cls, db_session=db.session, exclude=cls.auto_form_exclude)

        for key in sorted(form_fields.keys()):
            form_fields[key].kwargs['name'] = key
            form_factory.add_to_tab("Root.Main", form_fields[key])
        form_factory.add_to_tab("Root.Buttons", fields.SubmitField("Save", name="Save"))
        return form_factory

    def as_dict(self):
        """
        Get object as dict. Very useful for json responses.
        :return: dict with all database columns
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def can_create(self, mapper, connection):
        if request and not current_user:
            raise CannotCreateError
        return True

    def can_edit(self, mapper, connection):
        if request and not current_user:
            raise CannotUpdateError
        return True

    def can_delete(self, mapper, connection):
        if request and not current_user:
            raise CannotDeleteError
        return True

