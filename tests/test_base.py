#! ../env/bin/python
# -*- coding: utf-8 -*-

from silverflask import create_app, db
from silverflask.models import Page, User, SiteTree
import unittest
import tempfile
from flask.ext.testing import TestCase


class BaseTest(TestCase):
    """
    The base test case that is used to bootstrap all tests.
    Sets up a app and a in memory SQLite database that can be accessed
    via self.app and self.db respectively.

    Callin super().setUp() will create several database records, such as
    an User with an Admin role, and a published page.
    """
    def create_app(self):
        self.app = create_app("silverflask.settings.TestConfig", env="dev")
        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()

        return self.app

    def setUp(self):
        """
        Initialize app and setup admin user ('admin', 'admin'), a SiteConfig and
        a Page.
        """
        self.create_app()
        from silverflask.models import User
        from silverflask.models.User import Role
        if not len(Role.query.all()):
            admin_role = Role("admin", "Admin has all privileges")
            db.session.add(admin_role)
            db.session.commit()

        if not len(User.query.all()):
            # create standard user
            u = User("admin", "admin")
            u.email = "admin"
            db.session.add(u)
            admin_role = Role.query.filter(Role.name == "admin").first()
            u.roles.append(admin_role)
            db.session.commit()

        from silverflask.models import SiteConfig
        if not len(SiteConfig.query.all()):
            sc = SiteConfig()
            db.session.add(sc)
            db.session.commit()

        if not len(Page.query.all()):
            page = Page()
            page.content = "<p>Please proceed to the admin interface at <a href='/admin'>admin</a>!</p>"
            page.name = "home"
            page.urlsegment = "home"
            db.session.add(page)
            db.session.commit()
            page.mark_as_published()
            db.session.commit()

    @staticmethod
    def deepequal(l1, l2):
        """
        Compare to lists for equality and order.
        """
        for i in range(0, len(l1)):
            if l1[i] != l2[i]:
                return False
        return True
