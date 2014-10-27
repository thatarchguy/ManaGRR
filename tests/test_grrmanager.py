#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_grrmanager
----------------------------------

Tests for `grrmanager` module.
"""

from flask import Flask
from flask.ext.testing import TestCase


class Testgrrmanager(TestCase):

    def create_app(self):
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    def test_something(self):
        pass

    def tearDown(self):
        pass


