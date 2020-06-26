#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import sys
from conans import ConanFile

class TestPackageConan(ConanFile):

    def test(self):
        if sys.platform == 'win32':
            self.run("pvengine64 /QINSTALL .. . /exit")
        else:
            self.run("povray --version")
