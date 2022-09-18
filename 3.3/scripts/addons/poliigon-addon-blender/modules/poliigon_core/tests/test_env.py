# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from unittest import mock
import os
import unittest

try:
    # Testing within Poliigon core venv.
    from poliigon_core import env
except ModuleNotFoundError:
    # Testing within addon environment.
    import sys
    SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.dirname(SCRIPT_DIR))

    from poliigon_core import env


class EnvironmentUnitTest(unittest.TestCase):
    """Create env tests."""

    def setUp(self):
        self._env = env.PoliigonEnvironment(
            addon_name="poliigon-addon-core",
            base=os.path.dirname(__file__),
            env_filename="test_env.ini"
        )

    def test_env_loaded(self):
        self.assertTrue(self._env.env_name == "test")


if __name__ == '__main__':
    unittest.main()