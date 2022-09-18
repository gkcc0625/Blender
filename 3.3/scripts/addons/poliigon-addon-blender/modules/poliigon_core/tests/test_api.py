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

from dataclasses import dataclass
from unittest import mock
import json
import os
import requests
import sys
import tempfile
import unittest

try:
    # Testing within Poliigon core venv.
    from poliigon_core import api
    from poliigon_core import env
except ModuleNotFoundError:
    # Testing within addon environment.
    SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.dirname(SCRIPT_DIR))

    from poliigon_core import api
    from poliigon_core import env


@dataclass
class MockResponse:
    """Mock object for a requests.post response."""
    text: str  # Main body of repsonse
    ok: bool = True
    status_code: int = 200
    reason: str = "OK"  # Populated if status code is not 200.


class ApiTest(unittest.TestCase):
    """Create api service related tests."""

    @classmethod
    def setUpClass(cls):
        cls._env = env.PoliigonEnvironment(
            addon_name="poliigon-addon-core",
            base=os.path.dirname(__file__),
            env_filename="test_env.ini"
        )

        if cls._env.env_name == "prod":
            env_file = os.path.join(cls._env.base, cls._env.env_filename)
            raise RuntimeError("Test environment file is missing: " + env_file)

    def setUp(self):
        """Run setup before each test, reusable mocks."""
        self.ok = api.ApiResponse({}, True, None)

        # Set mock return for requests.
        resp = mock.MagicMock()
        resp.ok = False
        resp.text = "{}"

        patch_post = mock.patch("requests.post",
                                return_value=resp)
        patch_get = mock.patch("requests.get",
                               return_value=resp)

        self.patch_post = patch_post.start()
        self.addCleanup(patch_post.stop)
        self.patch_get = patch_get.start()
        self.addCleanup(patch_get.stop)

        self._api = api.PoliigonConnector(
            env=self._env,
            software="poliigon-addon-core"
        )
        self._api.register_update("vtest", "vtest")
        self._api.token = "123"

        self.mock_dl_expired = {
            "message": "The download request link has been expired",
            "errors": {"link": ["The download request link has been expired"]}
        }

    def test_construct(self):
        """Test that the API class can be constructed."""
        api.PoliigonConnector(env=self._env, software="poliigon-addon-core")

    def test_add_utm_suffix(self):
        """Test that the utm suffix is added correctly."""
        software = "poliigon-addon-core"
        param_list = [
            [
                "no_suffix", "www.site.com",
                f"www.site.com?utm_campaign=addon-{software}-v1.0&utm_source={software}&utm_medium=addon"
            ],
            [
                "slash_suffix", "www.site.com/",
                f"www.site.com/?utm_campaign=addon-{software}-v1.0&utm_source={software}&utm_medium=addon"
            ],
            [
                "q_suffix", "www.site.com?",
                f"www.site.com?utm_campaign=addon-{software}-v1.0&utm_source={software}&utm_medium=addon"
            ],
            [
                "one_exisitng_param", "www.site.com?tg",
                f"www.site.com?tg&utm_campaign=addon-{software}-v1.0&utm_source={software}&utm_medium=addon"
            ],
            [
                "one_exisitng_param_and", "www.site.com?tg&",
                f"www.site.com?tg&utm_campaign=addon-{software}-v1.0&utm_source={software}&utm_medium=addon"
            ]
        ]

        connector = api.PoliigonConnector(
            env=self._env,
            software=software
        )
        connector.version_str = "v1.0"
        for params in param_list:
            name = params[0]
            url = params[1]
            expected = params[2]
            # Subtest available in python 3.4+
            with self.subTest(msg=name, url=url, expected=expected):
                self.assertEqual(connector.add_utm_suffix(url), expected)

    def test_add_utm_with_content(self):
        """Test adding utm tags to urls with a content flag."""

    def test_meta_populated_optin(self):
        """Ensures that the meta field is populated if user opted in."""

        def get_optin():
            return True

        self._api.get_optin = get_optin

        resp = mock.MagicMock()
        resp.ok = True
        resp.text = "{}"

        # Test the optin status.
        with mock.patch("requests.post", return_value=resp) as resp_mock:
            self._api.log_out()
            resp_mock.assert_called_once()

            args, kwargs = resp_mock.call_args
            payload = kwargs["data"]  # Payload is input as a dumped json str.
            self.assertIn("addon_software_version", payload)
            self.assertIn('"optin": true', payload)

    def test_meta_populated_optout(self):
        """Ensures that the meta field is populated if user opted in."""

        def get_optin():
            return False

        self._api.get_optin = get_optin

        resp = mock.MagicMock()
        resp.ok = True
        resp.text = "{}"

        # Test the optin status.
        with mock.patch("requests.post", return_value=resp) as resp_mock:
            self._api.log_out()
            resp_mock.assert_called_once()

            args, kwargs = resp_mock.call_args
            payload = kwargs["data"]

            self.assertNotIn("addon_software_version", payload)
            self.assertIn('"optin": false', payload)

    def test_signal_event_optin(self):

        def get_optin():
            return True

        self._api.get_optin = get_optin

        # Set mock return
        resp = mock.MagicMock()
        resp.ok = True
        resp.text = "{}"

        # Test the optin status.
        with mock.patch("requests.post", return_value=resp) as resp_mock:
            res = self._api.signal_import_asset(123)
            resp_mock.assert_called_once()
            self.assertTrue(res.ok)

    def test_signal_event_optout(self):

        def get_optin():
            return False

        self._api.get_optin = get_optin

        # Set mock return
        resp = mock.MagicMock()
        resp.ok = True
        resp.text = "{}"

        # Test the optin status.
        with mock.patch("requests.post", return_value=resp) as resp_mock:
            res = self._api.signal_import_asset(123)

            # If opted out, should exit before getting to request function.
            resp_mock.assert_not_called()
            self.assertFalse(res.ok)

    @mock.patch("requests.post",
                side_effect=requests.exceptions.ConnectionError)
    def test_status_change(self, resp_mock):
        """Validates status change behaves without and with internet."""
        listen_mock = mock.MagicMock()
        self._api._status_listener = listen_mock

        resp = self._api.log_in("fake@email.com", "fake_password_1234")
        self.assertEqual(resp.error, api.ERR_CONNECTION)
        # Now check the listener itself.
        listen_mock.assert_called_once()
        # Finally, check the end status has persisted.
        self.assertEqual(self._api.status, api.ApiStatus.NO_INTERNET)

        # Now test back online.

        # First, setup the mocked valid response
        resp = mock.MagicMock()
        resp.ok = True
        resp.text = "{}"

        # Then set mock in place
        resp_mock.side_effect = None
        resp_mock.return_value = resp

        # Now test the new request, showing connection valid.
        listen_mock = mock.MagicMock()
        self._api._status_listener = listen_mock
        resp = self._api.log_in("fake@email.com", "fake_password_1234")
        self.assertNotEqual(resp.error, api.ERR_CONNECTION)
        # Now check the listener itself.
        listen_mock.assert_called_once()
        # Finally, check the end status has persisted.
        self.assertEqual(self._api.status, api.ApiStatus.CONNECTION_OK)

    def test_login_mocked(self):
        """Ensures the expected response return for certain requests."""

        # Test the server error `message` field is used when erro occurs.
        with mock.patch("requests.post") as resp_mock:
            jbody = {
                "message": "The password must be at least 6 characters. (and 1 more error)",
                "errors": {
                    "password": [
                        "The password must be at least 6 characters."
                    ],
                    "source": [
                        "The source field is required."
                    ]
                }
            }
            resp_mock.return_value = MockResponse(
                text=json.dumps(jbody),
                ok=False,
                status_code=422,
                reason="Unprocessable Entity")
            resp = self._api.log_in("fake@email.com", "fake_password_1234")

            resp_mock.assert_called_once()
            self.assertFalse(resp.ok)
            self.assertEqual(resp.error, jbody["message"])

        # Test when no message given on failure, should be the status code.
        with mock.patch("requests.post") as resp_mock:
            jbody = {}
            resp_mock.return_value = MockResponse(
                text=json.dumps(jbody),
                ok=False,
                status_code=422,
                reason="Unprocessable Entity")
            resp = self._api.log_in("fake@email.com", "fake_password_1234")

            resp_mock.assert_called_once()
            self.assertFalse(resp.ok)
            self.assertEqual(resp.error, "(422) Unprocessable Entity")

        # Ensure no error responses as expected, error value should be None.
        with mock.patch("requests.post") as resp_mock:
            jbody = {"access_token": "123"}
            resp_mock.return_value = MockResponse(text=json.dumps(jbody))
            resp = self._api.log_in("fake@email.com", "fake_password_1234")

            resp_mock.assert_called_once()
            self.assertTrue(resp.ok)
            self.assertIsNone(resp.error)

    def test_purchase_asset_mocked(self):
        """Ensure attempts to purchase asset are handled as expected."""

        # Validate success.
        with mock.patch("requests.post") as resp_mock:
            jbody = {
                "status": 200,
                "payload": {
                    "message": "Asset purchased successfully"
                }
            }
            resp_mock.return_value = MockResponse(text=json.dumps(jbody))
            resp = self._api.purchase_asset(123, "search", "/Textures")
            resp_mock.assert_called_once()
            self.assertTrue(resp.ok)
            self.assertIsNone(resp.error)

        # Issue like enough credits, pick up the right message - instead of
        # passing forward unprocessable entity.
        with mock.patch("requests.post") as resp_mock:
            jbody = {
                "message": "User doesn't have enough credits",
                "errors": {
                    "message": [
                        "User doesn't have enough credits"
                    ]
                }
            }
            resp_mock.return_value = MockResponse(
                text=json.dumps(jbody),
                ok=False,
                status_code=422,
                reason="Unprocessable Entity")
            resp = self._api.purchase_asset(123, "search", "/Textures")
            resp_mock.assert_called_once()
            self.assertFalse(resp.ok)
            self.assertEqual(resp.error, api.ERR_NOT_ENOUGH_CREDITS)

    def test_download_asset_mocked(self):
        download_data = {
            "assets": [
                {
                    "id": 3284,
                    "name": "BottleSodaEmpty001",
                    "lods": 0,
                    "softwares": [
                        "ALL_OTHERS"
                    ],
                    "sizes": [
                        "1K"
                    ]
                }
            ]
        }
        asset_id = download_data["assets"][0]["id"]
        dst_file = os.path.join(tempfile.gettempdir(), "test_downlaod_asset.zip")
        if os.path.isfile(dst_file):
            try:
                os.remove(dst_file)
            except Exception as e:
                print("Non-blocking exception during file remove in test")
                print(e)

        # Mock callback
        mock_fn = mock.MagicMock()

        # Mock data bytes iterator
        def mock_iter_content(chunk_size):
            return iter([b"somedata"])

        # The primary function to validate.
        post_mock = mock.MagicMock()
        post_mock.text = json.dumps({"url": "https://fakeurl.com/download_id"})
        post_mock.ok = True
        post_mock.status_code = 200

        get_mock = mock.MagicMock()
        get_mock.body = {"url": "https://fakeurl.com/download_id"}
        get_mock.ok = True
        get_mock.status_code = 200
        get_mock.reason = "OK"
        get_mock.headers["Content-Length"] = len("somedata")
        get_mock.iter_content = mock_iter_content

        # Have to wrap two mocks: one for the post requesting data, the other
        # for the streamed get request.
        with mock.patch("requests.post",
                        # autospec=True,
                        return_value=post_mock) as post_patch:
            with mock.patch("requests.get",
                            # autospec=True,
                            return_value=get_mock
                            ) as get_patch:
                res = self._api.download_asset(
                    asset_id, download_data, dst_file, mock_fn)
                post_patch.assert_called_once()
                get_patch.assert_called_once()

        # The above mocking will fail at the point of trying to unip our 'data'
        # which is a good enough sign that it is working up to that point.
        self.assertTrue(api.ERR_OS_WRITE in res.error)
        mock_fn.assert_called()  # Should be called many times during download.

        if os.path.isfile(dst_file):
            try:
                os.remove(dst_file)
            except Exception as e:
                print("Non-blocking exception during file remove in test")
                print(e)

    def test_subscription_status_active(self):
        active_sub = {
            "id": 123,
            "user_id": 12345,
            "team_id": None,
            "subscription_id": "ABCDEF",
            "status": "active",
            "plan_price_id": "plan_name",
            "plan_name": "PlanName",
            "period_unit": "month",
            "plan_price": "10",
            "currency_code": "USD",
            "plan_credit": 1000,
            "schedule_plan_changed_info": None,
            "paused_info": None,
            "next_subscription_renewal_date": "2022-08-19 23:58:37",
            "next_credit_renewal_date": "2022-08-19 23:58:37",
            "current_term_end": "2022-08-19 23:58:37",
            "created_at": "2022-05-19 23:58:48",
            "updated_at": "2022-07-20 00:01:25",
            "currency_symbol": "&#36;",
            "base_price": 0,
            "res_code_status": 200
        }

        post_mock = MockResponse(text=json.dumps(active_sub))
        with mock.patch("requests.post",
                        # autospec=True,
                        return_value=post_mock) as post_patch:
            res = self._api.get_subscription_details()
            post_patch.assert_called_once()
            self.assertTrue(res.ok)
            self.assertEqual(res.body["plan_name"], "PlanName")

    def test_subscription_status_not_active(self):
        no_sub_resp = {
            "res_code_status": 404,
            "error": "Subscription not found."
        }
        post_mock = MockResponse(
            text=json.dumps(no_sub_resp),
            ok=False,
            status_code=404,
            reason="Not found")
        with mock.patch("requests.post",
                        # autospec=True,
                        return_value=post_mock) as post_patch:
            res = self._api.get_subscription_details()
            post_patch.assert_called_once()
            self.assertTrue(res.ok)
            self.assertEqual(res.body.get("plan_name"), api.STR_NO_PLAN)


class ApiIntegrationTest(unittest.TestCase):
    """Create api integration tests with live requests."""

    @classmethod
    def setUpClass(cls):
        cls._env = env.PoliigonEnvironment(
            addon_name="poliigon-addon-core",
            base=os.path.dirname(__file__),
            env_filename="test_env.ini"
        )

        if cls._env.env_name == "prod":
            env_file = os.path.join(cls._env.base, cls._env.env_filename)
            raise RuntimeError("Test environment file is missing: " + env_file)

    def setUp(self):
        """Run setup before each test, reusable mocks."""
        self._api = api.PoliigonConnector(
            env=self._env,
            software="poliigon-addon-core"
        )
        self._api.register_update("vtest", "vtest")
        self.token = None

        self.query_data = {
            # NOTE: Test account MUST have acquired at least one wood asset.
            "query": "wood",
            "page": 1,
            "perPage": 10,
            "algoliaParams": {
                "facetFilters": [], "numericFilters": ["Credit>=0"]
            },
        }

    def load_login_token(self):
        """Utility to get a login token from server using local credentials.

        Local credentials are picked up from a local .env in ini format with
        fields for email and password. These should be for test accounts only,
        not live accounts.
        """
        if self.token:  # Already loaded within this test execution.
            return

        config = self._env.config

        email = config['DEFAULT']['email']
        pwd = config['DEFAULT']['pwd']
        res = self._api.log_in(email, pwd)
        if not res.ok:
            print("Login token test utility failed:")
            print(res.ok, "Body:", res.body, "Error:", res.error)
            errstr = f"{res.ok}: body {res.body}, err: {res.error}"
            raise Exception("Utility login failed during test: " + errstr)
        self.assertIsNotNone(self._api.token)

    def test_login(self):
        """Test logging in."""
        self.load_login_token()  # Implements its own assert statement.

    def test_login_invalid(self):
        """Test that invalid credentials return accordingly."""
        res = self._api.log_in("fake@email.com", "fake_password_1234")
        self.assertFalse(res.ok)

    def test_logout(self):
        """Test logging out."""
        self.load_login_token()
        res = self._api.log_out()
        self.assertTrue(res.ok)
        self.assertEqual(res.body["message"], "logged out successfully")

    def test_non_auth_call(self):
        """Ensure that non authorized calls return as such."""
        self._api.token = "FakeToken"
        res = self._api.categories()
        self.assertFalse(res.ok)
        self.assertEqual(res.error, api.ERR_NOT_AUTHORIZED)

        self._api.token = None
        res = self._api.categories()
        self.assertFalse(res.ok)
        self.assertEqual(res.error, api.ERR_NOT_AUTHORIZED)

    def test_categories(self):
        """Test that we are able to fetch categories."""
        self.load_login_token()
        res = self._api.categories()
        self.assertTrue(res.ok)
        self.assertGreater(len(res.body), 3)  # Should be list form.

        keys = [entry["name"] for entry in res.body]

        self.assertIn("Textures", keys)
        self.assertIn("Models", keys)
        self.assertIn("HDRIs", keys)
        self.assertIn("Brushes", keys)

    def test_get_balance(self):
        """Test that the balance endpoint signature is consistent."""
        self.load_login_token()
        res = self._api.get_user_balance()
        self.assertTrue(res.ok)

        expected_fields = [
            "subscription_balance",
            "ondemand_balance",
            "available_balance"
        ]
        for field in expected_fields:
            self.assertIn(field, res.body)

    def test_get_subscription_details(self):
        """Ensures subscription details endpoint signature is consistent."""
        self.load_login_token()
        res = self._api.get_subscription_details()
        self.assertTrue(res.ok)

        if res.body["plan_name"] == api.STR_NO_PLAN:
            # No plan active for logged in test account.
            pass
        else:
            # Plan is active for logged in test account.
            self.assertIn("id", res.body)
            self.assertIn("status", res.body)
            self.assertIn("plan_name", res.body)
            self.assertIn("paused_info", res.body)
            self.assertIn("plan_credit", res.body)
            self.assertIn("next_credit_renewal_date", res.body)
            self.assertIn("next_subscription_renewal_date", res.body)

    def test_get_assets(self):
        """Test that getting assets functions as expected."""
        self.load_login_token()
        res = self._api.get_assets(query_data=self.query_data)
        self.assertGreater(res.body.get("total", -1), 0)

    def test_get_my_assets(self):
        """Test that getting user assets functions as expected."""
        self.load_login_token()
        res = self._api.get_user_assets(query_data=self.query_data)
        self.assertGreater(res.body.get("total", -1), 0)

    def test_purchase_asset_again(self):
        """Test that pruchasing an exisitng asset returns as expected."""
        self.load_login_token()
        res = self._api.purchase_asset(asset_id=5330, search="", category="/")

        # While the purchase of an already owned asset from the API itself
        # is treated as an error, from addon code we want to see this as a
        # success as it means we can continue with further operations.
        self.assertTrue(res.ok)
        self.assertEqual(res.body.get("message"),
                         "User already owns the asset")

        # Message if not yet purchased: "Asset purchased successfully".
        # No easy way to create repeated tests for this however.

    def test_download_preview(self):
        self.load_login_token()
        tmp_file = os.path.join(tempfile.gettempdir(), "poliigon_converter_test.jpg")
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)
        self.assertFalse(os.path.isfile(tmp_file))

        # Random url file to test for public download.
        # Note! This is a high resolution file passed into a resizer function.
        url = (
            "https://poliigon.com/cdn-cgi/image/width=300,sharpen=0,f=auto/"
            "https://cdn.poliigon.com/assets/4079/previews/"
            "BricksBlackMulti001_Sphere.png?v=1646644669"
        )

        res = self._api.download_preview(
            url=url, dst_file=tmp_file)
        self.assertTrue(res.ok)
        self.assertTrue(os.path.isfile(tmp_file))

    def test_download_asset(self):
        self.load_login_token()
        download_data = {
            "assets": [
                {
                    "id": 3284,
                    "name": "BottleSodaEmpty001",
                    "lods": 0,
                    "softwares": [
                        "ALL_OTHERS"
                    ],
                    "sizes": [
                        "1K"
                    ]
                }
            ]
        }
        asset_id = download_data["assets"][0]["id"]
        dst_file = os.path.join(tempfile.gettempdir(), "test_downlaod_asset.zip")
        if os.path.isfile(dst_file):
            try:
                os.remove(dst_file)
            except Exception as e:
                print("Non-blocking exception during file remove in test")
                print(e)

        mock_fn = mock.MagicMock()

        # The primary function to validate.
        res = self._api.download_asset(
            asset_id, download_data, dst_file, mock_fn)
        print("What is the res result?", res.ok, res.body, ";er:", res.error)

        self.assertTrue(res.ok)
        mock_fn.assert_called()  # Should be called many times during download.

        if os.path.isfile(dst_file):
            try:
                os.remove(dst_file)
            except Exception as e:
                print("Non-blocking exception during file remove in test")
                print(e)

    def test_signal_event(self):
        # TODO: Enable once server has been updated.
        return
        self.load_login_token()

        def get_optin():
            return True

        self._api.get_optin = get_optin
        res = self._api.signal_import_asset(123)
        self.assertTrue(res.ok)


if __name__ == '__main__':
    unittest.main()
