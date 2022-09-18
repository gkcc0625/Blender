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
    from poliigon_core import updater
except ModuleNotFoundError:
    # Testing within addon environment.
    import sys
    SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.dirname(SCRIPT_DIR))

    from poliigon_core import updater


class MockResponse:
    def __init__(self, ok: bool, jstring: str):
        self.text = jstring
        self.ok = ok
        self.status_code = 200 if ok else 500


class UpdaterUnitTest(unittest.TestCase):
    """Create updater tests."""

    def setUp(self):
        # Patch out to force blender to think its running with an interface.
        patcher = mock.patch("requests.get", autospec=True)
        self.mock_foreground = patcher.start()
        self.addCleanup(patcher.stop)

        self.updater = updater.SoftwareUpdater(
            addon_name="poliigon-addon-blender",
            addon_version=(0, 9, 0),
            software_version=(2, 90)
        )

        base = os.path.dirname(__file__)
        test_data = os.path.join(base, "test_updater_version.json")
        with open(test_data, 'r') as f:
            self.mock_resp = f.read()

        # Mock versions to use in testing.
        self.mock_version_newest = updater.VersionData(
            version=(1, 1, 0),
            min_software_version=(2, 93),  # Ineligible with above.
            max_software_version=None)
        self.mock_version_newer = updater.VersionData(
            version=(1, 0, 0),
            min_software_version=(2, 80),
            max_software_version=None)
        self.mock_version_same = updater.VersionData(
            version=(0, 9, 0),
            min_software_version=(2, 80),
            max_software_version=None)
        self.mock_version_old = updater.VersionData(
            version=(0, 8, 0),
            min_software_version=None,
            max_software_version=(2, 90))  # Ineligible with above.

    def test_update_versions(self):
        resp = MockResponse(True, self.mock_resp)
        with mock.patch("requests.get", return_value=resp):
            self.updater.update_versions()
            self.assertTrue(self.updater.stable is not None)

    def test_check_for_update_stable(self):
        """Check that we successfully get the a latest version."""

        mock_fn = mock.MagicMock()

        # Mock the updates applied
        self.updater.stable = self.mock_version_newer

        with mock.patch("poliigon_core.updater.SoftwareUpdater.update_versions"
                        ) as mock_update:
            # Perform check (mocking above should leave assignments above)
            self.updater.check_for_update(callback=mock_fn)
            mock_update.assert_called_once()
            mock_fn.assert_called_once()
            self.assertTrue(self.updater.update_ready)
            self.assertEqual(self.updater.update_data, self.mock_version_newer)

    def test_check_for_update_max_stable(self):
        """Check that we successfully get stable version."""

        mock_fn = mock.MagicMock()

        # Mock the updates applied, such that stable is ineligible,
        # but another max works.
        self.updater.stable = self.mock_version_newest
        self.updater.all_versions = [
            self.mock_version_newest,  # Should be ineligible due to min ver.
            self.mock_version_newer,  # Should be the one it picks.
            self.mock_version_same,
            self.mock_version_old
        ]

        with mock.patch("poliigon_core.updater.SoftwareUpdater.update_versions"
                        ) as mock_update:

            # Perform check (mocking above should leave assignments above)
            self.updater.check_for_update(callback=mock_fn)
            mock_update.assert_called_once()
            mock_fn.assert_called_once()
            self.assertTrue(self.updater.update_ready)
            self.assertEqual(self.updater.update_data, self.mock_version_newer)

    def test_check_for_update_max_no_update(self):
        """Check that we successfully get the a latest eligible version."""

        mock_fn = mock.MagicMock()

        # Mock the updates applied, such that stable is ineligible,
        # but another max works.
        self.updater.stable = self.mock_version_newest
        self.updater.all_versions = [
            self.mock_version_newest,  # Should be ineligible due to min ver.
            self.mock_version_same,  # Should be the one it picks, but is same.
            self.mock_version_old
        ]

        with mock.patch("poliigon_core.updater.SoftwareUpdater.update_versions"
                        ) as mock_update:

            # Perform check (mocking above should leave assignments above)
            self.updater.check_for_update(callback=mock_fn)
            mock_update.assert_called_once()
            mock_fn.assert_called_once()
            self.assertFalse(self.updater.update_ready)  # Same ver != update.
            self.assertIsNone(self.updater.update_data)

    def test_max_eligible(self):
        """Verify the check_eligible and max_eligible methods work."""
        res = self.updater._check_eligible(self.mock_version_newest)
        self.assertFalse(res)

        res = self.updater._check_eligible(self.mock_version_newer)
        self.assertTrue(res)

        res = self.updater._check_eligible(self.mock_version_old)
        self.assertFalse(res)

        self.updater.all_versions = [
            self.mock_version_newest,  # Should be ineligible due to min ver.
            self.mock_version_newer,  # Should be the one it picks.
            self.mock_version_same,
            self.mock_version_old
        ]
        res = self.updater.get_max_eligible()
        self.assertEqual(res, self.mock_version_newer)


class UpdaterIntegrationTest(unittest.TestCase):
    """Create updater tests."""

    def setUp(self):
        self.updater = updater.SoftwareUpdater(
            addon_name="poliigon-addon-blender",
            addon_version=(0, 9, 0),
            software_version=(2, 80)
        )

    def test_live_versions(self):
        self.updater.update_versions()
        self.assertTrue(self.updater.stable is not None)


if __name__ == '__main__':
    unittest.main()
