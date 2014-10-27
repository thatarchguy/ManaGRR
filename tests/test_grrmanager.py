#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_grrmanager
----------------------------------

Tests for `grrmanager` module.
"""

import urllib2
from flask import Flask
from flask.ext.testing import LiveServerTestCase
from app import app, db

class Testgrrmanager(LiveServerTestCase):

    def create_app(self):
        app.config.from_object('config.TestConfiguration')
        return app
    
    def test_server_is_up_and_running(self):
        response = urllib2.urlopen(self.get_server_url())
        self.assertEqual(response.code, 200)
