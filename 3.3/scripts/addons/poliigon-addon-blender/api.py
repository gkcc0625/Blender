# #### BEGIN GPL LICENSE BLOCK #####
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

"""General purpose, pure python interface to Poliigon web APIs and services."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Sequence
from urllib.request import getproxies
import concurrent.futures
import json
import os
import requests
import time
import zipfile

from . import config


TIMEOUT = 10  # Request timeout in seconds.
MAX_DL_THREADS = 6
MIN_VIEW_SCREEN_INTERVAL = 2.0  # seconds min between screen report calls.

# Enum values to reference
ERR_NOT_AUTHORIZED = "Not authorized"
ERR_CONNECTION = "Connection error"
ERR_OS_WRITE = "Failed to write file"
ERR_NO_POPULATED = "Data not populated in response"
ERR_OTHER = "Unknown error occurred"
ERR_INTERNAL = "Internal Server Error"
ERR_NOT_ENOUGH_CREDITS = "User doesn't have enough credits"
ERR_USER_CANCEL_MSG = "User cancelled download"
ERR_OPTED_OUT = "Did not send event, user is opted out"
ERR_INVALID_SCREEN_NAME = "Invalid screen name"
ERR_INTERVAL_VIEW = "Last view was too recent per min interval"
ERR_TIMEOUT = f"Connection timed out after {TIMEOUT} seconds"
ERR_NO_TOKEN = "Failed to get token from login"
ERR_WRONG_CREDS = ("The email/password provided doesn't match our records, "
                   "please try again.")
ERR_PROXY = "Cannot connect due to proxy error"
ERR_MISSING_STREAM = "Reqeusts response object missing from stream"

STR_NO_PLAN = "No plan active"

# Values exactly matching API responses.
API_ALREADY_OWNED = "User already owns the asset"
API_NO_SUBSCRIPTION = "Subscription not found."

# Reusable lists of err constants for which don't warrant reporting.
SKIP_REPORT_ERRS = [
    ERR_NOT_AUTHORIZED, ERR_CONNECTION, ERR_TIMEOUT, ERR_PROXY]


@dataclass
class ApiResponse:
    """Container object for a response from the Poliigon API."""
    body: Dict  # Contents of the reply in all cases.
    ok: bool  # Did the request complete with a successful result.
    error: str  # Meant to be a short, user-friendly message.


class ApiStatus(Enum):
    """Event indicator which parent modules can subscribe to listen for."""
    CONNECTION_OK = 1  # Could connect to API, even if transaction failed.
    NO_INTERNET = 2  # Appears to be no internet.
    PROXY_ERROR = 3  # Appears to be a proxy error.


class PoliigonConnector():
    """Poliigon connector used for integrating with the web API."""

    software_source: str = ""  # e.g. blender
    software_version: str = ""  # e.g. 3.2
    version_str: str = ""  # e.g. 1.2.3, populated after calling init.
    api_url: str
    token: str = None  # Populated on login/settings read, cleared sans auth.
    invalidated: bool = False  # Set true if outdated token detected.
    common_meta: Dict  # Fields to add to all POST requests.
    status: ApiStatus = ApiStatus.CONNECTION_OK

    _last_screen_view: int = None  # State to avoid excessive reporting.

    # Injected function to check if opted into tracking.
    # args: This function should take in no arguments
    get_optin: callable

    # Injected function for remote reporting.
    # args (message, code_msg, level)
    _report_message: callable

    # Injected, called when the overall API status is changed.
    # args (ApiEvent)
    _status_listener: callable

    def __init__(self,
                 software: str,
                 api_url: str = "",
                 get_optin: Optional[callable] = None,
                 report_message: Optional[callable] = None,
                 status_listener: Optional[callable] = None):
        self.software_source = software
        self.api_url = api_url if api_url else config.environ.api_url
        self.get_optin = get_optin
        self._report_message = report_message
        self._status_listener = status_listener

    def register_update(self, addon_v: str, software_v: str) -> None:
        """Run soon after __init__ after app has readied itself.

        Args:
            addon_v: In form "1.2.3"
            software_v: In form "3.2"
        """
        self.version_str = addon_v
        self.software_version = software_v
        self.common_meta = {
            "addon_version": self.version_str,
            "software_name": self.software_source
        }

    def report_message(self, message, code_msg, level):
        if self._report_message is not None:
            self._report_message(message, code_msg, level)

    def _request(self,
                 path: str,
                 method: str,
                 payload: Optional[Dict] = None,
                 headers: Optional[Dict] = None
                 ) -> ApiResponse:
        """Request a repsonse from an api.

        Args:
            path: The api endpoint path without the url domain.
            method: Type of http request, e.g. POST or GET.
            payload: The body of the request.
            headers: Prepopulated headers for the request including auth.
        """
        url = self.api_url + path

        try:
            proxies = getproxies()
            if method == "POST":
                payload = self._update_meta_payload(payload)
                # TODO: Use injected logger when available through core.
                # print(f"Request payload to {url}: {payload}")
                res = requests.post(url,
                                    data=json.dumps(payload),
                                    headers=headers,
                                    proxies=proxies,
                                    timeout=TIMEOUT)
            elif method == "GET":
                res = requests.get(url,
                                   headers=headers,
                                   proxies=proxies,
                                   timeout=TIMEOUT)
            else:
                raise ValueError("raw_request input must be GET, POST, or PUT")
        except requests.exceptions.ConnectionError as e:
            resp = {"error": str(e), "request_url": url}
            self._trigger_status_change(ApiStatus.NO_INTERNET)
            return ApiResponse(resp, False, ERR_CONNECTION)
        except requests.exceptions.Timeout as e:
            resp = {"error": str(e), "request_url": url}
            self._trigger_status_change(ApiStatus.NO_INTERNET)
            return ApiResponse(resp, False, ERR_TIMEOUT)
        except requests.exceptions.ProxyError as e:
            resp = {"error": str(e), "request_url": url, "message": ERR_PROXY}
            self.report_message("failed_proxy_error", url, level="error")
            self._trigger_status_change(ApiStatus.PROXY_ERROR)
            return ApiResponse(resp, False, ERR_PROXY)

        # Connection to site was a success, signal online.
        self._trigger_status_change(ApiStatus.CONNECTION_OK)

        http_err = f"({res.status_code}) {res.reason}" if not res.ok else None
        error = None

        invalid_auth = "unauthorized" in res.text.lower()
        invalid_auth = invalid_auth or "unauthenticated" in res.text.lower()

        if invalid_auth:
            resp = {}
            ok = False
            error = ERR_NOT_AUTHORIZED
            self.token = None
            self.invalidated = True
        elif res.text:
            try:
                resp = json.loads(res.text)
                ok = res.ok

                # If server error, pass forward any message from api, but
                # fallback to generic http status number/name.
                # Requests that fail will not return 200 status, and should
                # include a specific message on what was wrong.
                # There is also typically an "errors" field in the body,
                # but that is a more complex structure (not just a string).
                if not ok:
                    error = resp.get("message", http_err)
                    if error == "":
                        error = f"{http_err} - message present but empty"

            except json.decoder.JSONDecodeError:
                resp = {}
                ok = False
                error = f"Failed to parse response as json - {http_err}"
        else:
            resp = {}
            ok = False
            error = f"No contents in response - {http_err}"

        resp["request_url"] = url

        return ApiResponse(resp, ok, error)

    def _request_stream(self,
                        url: str,
                        headers: Optional[Dict] = None
                        ) -> ApiResponse:
        """Stream a request from an explicit fully defined url.

        Args:
            path: The api endpoint path without the url domain.
            headers: Prepopulated headers for the request including auth.

        Response: ApiResponse where the body is a dict including the key:
            "stream": requests get response object (the streamed connection).
        """
        try:
            proxies = getproxies()
            res = requests.get(url,
                               headers=headers,
                               proxies=proxies,
                               timeout=TIMEOUT,
                               stream=True)
        except requests.exceptions.ConnectionError as e:
            resp = {"error": str(e), "request_url": url}
            self._trigger_status_change(ApiStatus.NO_INTERNET)
            return ApiResponse(resp, False, ERR_CONNECTION)
        except requests.exceptions.Timeout as e:
            resp = {"error": str(e), "request_url": url}
            self._trigger_status_change(ApiStatus.NO_INTERNET)
            return ApiResponse(resp, False, ERR_TIMEOUT)
        except requests.exceptions.ProxyError as e:
            resp = {"error": str(e), "request_url": url, "message": ERR_PROXY}
            self.report_message("failed_proxy_error", url, level="error")
            self._trigger_status_change(ApiStatus.PROXY_ERROR)
            return ApiResponse(resp, False, ERR_PROXY)

        # Connection to site was a success, signal online.
        self._trigger_status_change(ApiStatus.CONNECTION_OK)

        error = f"({res.status_code}) {res.reason}" if not res.ok else None

        invalid_auth = res.status_code == 401

        if invalid_auth:
            resp = {"response": None}
            ok = False
            error = ERR_NOT_AUTHORIZED
            self.token = None
            self.invalidated = True
        else:
            resp = {"stream": res}
            ok = res.ok

        return ApiResponse(resp, ok, error)

    def _request_authenticated(self,
                               path: str,
                               payload: Optional[Dict] = None
                               ) -> ApiResponse:
        """Make an authenticated request to the API using the user token."""

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        else:
            return ApiResponse({}, False, ERR_NOT_AUTHORIZED)
        method = "POST" if payload is not None else "GET"
        res = self._request(path, method, payload, headers)
        if res.error and "server error" in res.error.lower():
            res.ok = False
            res.error = ERR_INTERNAL

        return res

    def add_utm_suffix(self, url: str, content: Optional[str] = None) -> str:
        """Return the UTM tag to append to any url requests for tracking."""

        # Detect if the url already has a param.
        initial_char = ""
        if url[-1] == "/":
            initial_char = "?"
        elif url[-1] == "?":
            initial_char = ""
        elif url[-1] == "&":
            initial_char = ""
        elif "?" in url:
            initial_char = "&"
        else:
            initial_char = "?"

        # Ensure the version str starts with a leading v.
        if not self.version_str or self.version_str[0] != "v":
            addon_v = "v" + self.version_str
        else:
            addon_v = self.version_str
        campaign = f"addon-{self.software_source}-{addon_v}"

        outstr = "{url}{init}utm_campaign={cmpg}&utm_source={src}&utm_medium={med}{cnt}".format(
            url=url,
            init=initial_char,
            cmpg=campaign,  # Granular addon+software+version
            src=self.software_source,  # such as "blender"
            med="addon",
            cnt="" if not content else "&{content}"
        )
        return outstr

    def log_in(self, email: str, password: str,
               time_since_enable: Optional[int] = None) -> ApiResponse:
        """Log the user in with a password/email combo.

        time_since_enable is the number of seconds since the addon was first
        enabled, only populated if this was the first login event for this
        install, used to identify an install event.
        """
        data = {
            "email": email,
            "password": password,
        }
        if time_since_enable is not None:
            data["time_since_enable"] = time_since_enable

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        res = self._request("/login", "POST", data, headers)

        if not res.ok:
            msg = res.body.get("message", "")
            err = res.body.get("errors", "")
            if "do not match" in msg:
                self.report_message("login_error_matching_creds", msg, "info")
                res.error = ERR_WRONG_CREDS
            elif msg:
                self.report_message(
                    "login_error_other", f"{res.error}: {msg}", "error")
                res.error = msg
            elif err:
                self.report_message(
                    "login_error_err_no_msg", f"{res.error} - {err}", "error")
                # err can be a struc, not great for ui, prefer res.error
                res.error = res.error or ERR_OTHER
            else:
                self.report_message(
                    "login_error_no_message", str(res.error), "error")
                # Don't override res.error, which can include status code.
                # Pass forward to front end, likely connection or proxy.

        elif not res.body.get("access_token"):
            self.report_message("login_error_no_token", str(res.body), "error")
            res.ok = False
            res.error = ERR_NO_TOKEN
        else:
            # Request was success.
            self.token = res.body.get("access_token")
            self.invalidated = False
        return res

    def log_out(self) -> ApiResponse:
        """Logs the user out."""
        path = "/logout"
        payload = {}
        res = self._request_authenticated(path, payload)
        return res

    def categories(self) -> ApiResponse:
        """Get the list of website requests."""
        # TODO: Wrap using cachetools to avoid repeat calls.
        res = self._request_authenticated("/categories")
        if res.ok:
            if "payload" in res.body:
                res.body = res.body.get("payload")
            else:
                res.ok = False
                res.error = "Categoreis not populated"
        return res

    def get_user_balance(self) -> ApiResponse:
        """Get the balance for the given user."""
        path = "/available/user/balance"
        res = self._request_authenticated(path)
        return res

    def get_user_info(self) -> ApiResponse:
        """Get information for the given user."""
        path = "/me"
        res = self._request_authenticated(path)
        return res

    def get_subscription_details(self) -> ApiResponse:
        """Get the subscription details for the given user."""
        path = "/subscription/details"
        res = self._request_authenticated(path, {})
        if "plan_name" in res.body:
            return res
        elif not res.ok and res.body.get("error") == API_NO_SUBSCRIPTION:
            # Api returns error if no plan is active, but we want to draw the
            # plan as just inactive in the UI and not treat as an error.
            return ApiResponse(
                {"plan_name": STR_NO_PLAN},
                True,
                None)
        return res

    def download_asset(
        self, asset_id: int, download_data: dict, dst_file: str, callback=None
    ) -> ApiResponse:
        """Stream download a purchased asset to a file.

        Args:
            asset_id: The integer asset id.
            download_data: Structure of data defining the download.
            dst_file: Where to download file to.
            callback: Fn with args (asset_id, file_size) to drive progress bar.
        """

        def construct_error(url: str, response: str, source: dict) -> str:
            """Create a json string with details about an error.

            Args:
                url: The url of the api endpoint called.
                response: Short message describing the error.
                source: Structure of data sent with the the api request.
            """

            error = {
                "request_url": url,
                "server_response": response,
                "source_request": source
            }

            return json.dumps(error, indent=4)

        # Fetch the download URL.
        t0 = time.time()
        res = self._request_authenticated(
            "/assets/download", payload=download_data)
        request_url = res.body.get("request_url", "No request_url in body.")
        if res.ok:
            if res.body.get("url"):
                download_url = res.body.get("url")
            elif res.body.get("message") and "expired" in res.body["message"]:
                return ApiResponse(
                    {"message": res.body["message"]},
                    False,
                    construct_error(
                        request_url,
                        "Download link expired",
                        download_data
                    )
                )
            else:
                return ApiResponse(
                    {"message": "Failed to fetch download url"},
                    False,
                    construct_error(
                        request_url,
                        "Download failed",
                        download_data
                    )
                )
        else:
            res.error = construct_error(request_url, res.error, download_data)
            return res

        res = self._request_stream(download_url)

        if not res.ok:
            err = construct_error(
                download_url,
                f"Received {res.error} error during download",
                download_data)
            res.error = err
            return res
        elif "stream" not in res.body:
            err = construct_error(
                download_url,
                ERR_MISSING_STREAM,
                download_data)
            msg = {"message": "Reqeusts response missing from stream"}
            return ApiResponse(msg, False, err)

        stream = res.body["stream"]

        dst_file = dst_file + "dl"  # Update name for intermediate drawing.
        file_size = int(stream.headers["Content-Length"])

        cancelled = False
        continue_download = callback(asset_id, file_size)

        try:
            with open(dst_file, "wb") as write_file:
                last_callback = time.time()
                for chunk in stream.iter_content(chunk_size=512):
                    if chunk:
                        write_file.write(chunk)
                        if time.time() > last_callback + 0.05:
                            continue_download = callback(asset_id, file_size)
                            if not continue_download:
                                cancelled = True
                                break
                            last_callback = time.time()
        except OSError as e:
            return ApiResponse(
                {"error": e},
                False,
                f"Download error for {asset_id} - {ERR_OS_WRITE}\n{e}")

        # Always do a final callback,
        final_call = callback(asset_id, file_size)
        cancelled = cancelled or not final_call

        if cancelled:
            os.remove(dst_file)
            msg = ERR_USER_CANCEL_MSG
            return ApiResponse({"error": msg}, False, msg)

        # This extracts the zip.
        asset_dir = os.path.splitext(dst_file)[0]

        if not os.path.exists(asset_dir):
            os.makedirs(asset_dir)

        try:
            with zipfile.ZipFile(dst_file, "r") as read_file:
                zip_files = read_file.namelist()

                extract_files = [
                    file for file in zip_files
                    if not os.path.exists(os.path.join(asset_dir, file))]

                read_file.extractall(path=asset_dir, members=extract_files)

            os.remove(dst_file)
        except Exception as e:
            return ApiResponse(
                {"error": e},
                False,
                construct_error(download_url, ERR_OS_WRITE, download_data))

        # print(
        #     "download time :",
        #     time.strftime('%H:%M:%S', time.gmtime(time.time() - t0)))

        return ApiResponse({"file": dst_file}, True, None)

    def download_preview(self, url: str, dst_file: str) -> ApiResponse:
        """Stream download a preview to a file from a custom domain url."""

        # TODO: Add an optional chunk size callback for UI updates mid stream.
        # print(f"download_asset: Downloading {url} to {dst_file}")
        try:
            resp = self._request_stream(url)
            if not resp.ok and resp.error in SKIP_REPORT_ERRS:
                return resp

            stream = resp.body.get("stream")
            if not stream:
                self.report_message(
                    "download_preview_resp_missing",
                    f"{ERR_MISSING_STREAM} - {resp.error}",
                    'error')
                return ApiResponse(
                    {"error": ERR_MISSING_STREAM},
                    False,
                    ERR_MISSING_STREAM)
            elif resp.ok:
                with open(dst_file, "wb") as fwriter:
                    fwriter.write(stream.content)
            else:
                self.report_message(
                    "download_preview_error", resp.error, 'error')
                return resp
        except requests.exceptions.ConnectionError as e:
            self.report_message(
                "download_preview_error_connect", str(e), 'error')
            return ApiResponse({"error": e}, False, ERR_CONNECTION)
        except OSError as e:
            self.report_message(
                "download_preview_error_write", str(e), 'error')
            return ApiResponse({"error": e}, False, ERR_OS_WRITE)
        except Exception as e:
            self.report_message(
                "download_preview_error_other", str(e), 'error')
            return ApiResponse({"error": e}, False, ERR_OTHER)
        return ApiResponse({"file": dst_file}, True, None)

    def purchase_asset(
            self, asset_id: int, search: str, category: str) -> ApiResponse:
        """Purchase a given asset for the logged in user.

        Args:
            asset_id: The unique poliigon asset id.
            search: Current active search query.
            category: Current category in slug form: "/brushes/free.
        """
        path = f"/assets/{asset_id}/purchase"
        payload = {}  # Force to be POST request.

        if self._is_opted_in():
            # Only send if user is opted in.
            payload["last_search_term"] = search
            payload["last_category"] = category

        res = self._request_authenticated(path, payload)
        if not res.ok:
            if "message" in res.body:
                msg = res.body["message"]
                err = str(res.body.get("errors", ""))  # Detailed server error.
                if API_ALREADY_OWNED.lower() in msg.lower():
                    self.report_message("purchased_existing", msg, "info")
                    res.ok = True  # Override so that download initiates.
                    res.error = None
                elif "enough credits" in msg:
                    self.report_message("not_enough_credits", asset_id, "info")
                    res.error = ERR_NOT_ENOUGH_CREDITS
                else:
                    res.error = f"{msg} - asset_id: {asset_id}"
                    self.report_message(
                        "purchase_failed", f"{res.error} {err}", "error")
            else:
                # To API, pass original message before updating to generic one.
                self.report_message("purchase_failed",
                                    f"{res.error}  - asset_id: {asset_id}",
                                    "error")
                res.error = f"{ERR_OTHER} - asset_id: {asset_id}"
        return res

    def get_assets(self, query_data: Dict) -> ApiResponse:
        """Get the assets with an optional query parameter."""
        res = self._request_authenticated("/assets", payload=query_data)
        if not res.ok:
            if res.error not in SKIP_REPORT_ERRS:
                self.report_message("online_assets_error",
                                    f"{query_data} - {res.error}", "error")
            return res
        elif "payload" in res.body:
            res.body = res.body.get("payload")
        else:
            self.report_message(
                "online_assets_no_payload", str(res.body), "error")
            res.ok = False
            res.error = ERR_NO_POPULATED
        return res

    def get_user_assets(self, query_data: Dict) -> ApiResponse:
        """Get assets the user has already purchased."""
        res = self._request_authenticated("/my-assets", payload=query_data)
        if not res.ok:
            if res.error not in SKIP_REPORT_ERRS:
                self.report_message("get_user_assets_error",
                                    f"{query_data} - {res.error}", "error")
            return res
        elif "payload" in res.body:
            res.body = res.body.get("payload")
        else:
            self.report_message(
                "get_user_assets_no_payload", str(res.body), "error")
            res.ok = False
            res.error = ERR_NO_POPULATED
        return res

    def pooled_preview_download(
            self, urls: Sequence, files: str) -> ApiResponse:
        """Threadpool executor for downloading assets or previews.

        Arguments:
            urls: A list of full urls to each download file, not just api stub.
            files: The parallel output list of files to create.
        """
        if len(urls) != len(files):
            raise RuntimeError("List of urls and files are not equal")
        futures = []
        with concurrent.futures.ThreadPoolExecutor(
                max_workers=MAX_DL_THREADS) as executor:
            for i in range(len(urls)):
                future = executor.submit(
                    self.download_preview,
                    urls[i],
                    files[i]
                )
                futures.append(future)

        any_failures = []
        for ftr in futures:
            res = ftr.result()
            if not res or not res.ok:
                any_failures.append(res)

        if any_failures:
            return ApiResponse(
                any_failures, False, "Error during pooled preview download")
        else:
            return ApiResponse("", True, None)

    def _signal_event(self, event_name: str, payload: Dict) -> ApiResponse:
        """Reusable entry to send an event, only if opted in."""
        if not self._is_opted_in():
            return ApiResponse(None, False, ERR_OPTED_OUT)
        return self._request_authenticated(f"/t/{event_name}",
                                           payload=payload)

    def signal_preview_asset(self, asset_id: int) -> ApiResponse:
        """Sends quick asset preview event if opted in."""
        payload = {"asset_id": asset_id}
        return self._signal_event("preview_asset", payload=payload)

    def signal_import_asset(
            self, asset_id: Optional[int] = 0):
        """Sends import asset event if opted in."""
        payload = {"asset_id": asset_id}
        return self._signal_event("import_asset", payload=payload)

    def signal_view_screen(self, screen_name: str) -> ApiResponse:
        """Sends view screen event if opted in.

        Limits one signal even per session per notification type.

        Args:
            screen_name: Explicit agreed upon view names within addon.
        """
        now = time.time()
        if self._last_screen_view:
            if now - self._last_screen_view < MIN_VIEW_SCREEN_INTERVAL:
                return ApiResponse({}, False, ERR_INTERVAL_VIEW)
            else:
                self._last_screen_view = now
        else:
            self._last_screen_view = now

        # Any name changes here require server-side coordination.
        valid_screens = [
            "home",
            "my_assets",
            "imported",
            "my_account",
            "settings",
        ]

        if screen_name not in valid_screens:
            print("Screen name is not valid:", screen_name)
            return ApiResponse(
                {"invalid_screen": screen_name},
                False,
                ERR_INVALID_SCREEN_NAME)
        payload = {"screen_name": screen_name}
        return self._signal_event("view_screen", payload=payload)

    def signal_view_notification(self, notification_id: str) -> ApiResponse:
        """Sends view notification event if opted in."""
        payload = {"notification_id": notification_id}
        return self._signal_event("view_notification", payload=payload)

    def signal_click_notification(
            self, notification_id: str, action: str) -> ApiResponse:
        """Sends click notification event if opted in."""
        payload = {"notification_id": notification_id, "action": action}
        return self._signal_event("click_notification", payload=payload)

    def signal_dismiss_notification(self, notification_id: str) -> ApiResponse:
        """Sends dismissed notification event if opted in."""
        payload = {"notification_id": notification_id}
        return self._signal_event("dismiss_notification", payload=payload)

    def _is_opted_in(self) -> bool:
        return self.get_optin and self.get_optin()

    def _update_meta_payload(self, payload: Dict) -> Dict:
        """Take the given payload and add or update its meta fields."""
        if "meta" not in payload:
            payload["meta"] = {}

        if self._is_opted_in():
            payload["meta"]["optin"] = True
            payload["meta"]["software_version"] = self.software_version
        else:
            payload["meta"] = {}  # Clear out any existing tracking.
            payload["meta"]["optin"] = False

        # Always populate addon version and platform.
        payload["meta"].update(self.common_meta)
        payload["source"] = "toolbox"  # TODO: Remove once no longer required.
        payload["platform"] = "addon"

        return payload

    def _trigger_status_change(self, status_name: ApiStatus) -> None:
        """Trigger callbacks to other modules on API status change.

        Typically used to update the UI in a central location, instaed of
        needing to wrap each and every call with the same handler.
        """
        self.status = status_name
        if self._status_listener is None:
            return
        self._status_listener(status_name)
