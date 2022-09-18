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


from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from math import radians
from typing import Optional
import atexit
import datetime
import json
import mathutils
import os
import queue
import re
import threading
import time
import traceback

try:
    import ConfigParser
except:
    import configparser as ConfigParser

from bpy.app.handlers import persistent
import bpy.utils.previews
import bmesh

from . import api
from .utils import *
from . import reporting
from . import updater


MAX_PURCHASE_THREADS = 5
MAX_DOWNLOAD_THREADS = 5


# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


def panel_update(context=None):
    """Force a redraw of the 3D and preferences panel from operator calls."""
    if not context:
        context = bpy.context
    cTB.f_CheckAssets()
    try:
        for wm in bpy.data.window_managers:
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type not in ("VIEW_3D", "PREFERENCES"):
                        continue
                    for region in area.regions:
                        region.tag_redraw()
    except AttributeError:
        pass  # Startup condition, nothing to redraw anyways.


def last_update_callback(value):
    """Called by the updated module to allow saving in local system."""
    if cTB.updater is None:
        return
    cTB.vSettings["last_update"] = cTB.updater.last_check
    cTB.f_SaveSettings()


# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


@dataclass
class Notification:
    """Container object for a user notification."""
    class ActionType(Enum):
        OPEN_URL = 1
        UPDATE_READY = 2
        POPUP_MESSAGE = 3

    notification_id: str  # Unique id for this specific kind of notice.
    title: str  # Main title, should be short
    action: ActionType  # Indicator of how to structure and draw notification.
    allow_dismiss: bool = True  # Allow the user to dismiss the notification.
    tooltip: Optional[str] = None  # Hover-over tooltip, if there is a button
    icon: Optional[str] = None  # Blender icon enum to use.

    # Treat below as a "oneof" where only set if the given action is assigned.
    # OPEN_URL
    ac_open_url_address: Optional[str] = None
    ac_open_url_label: Optional[str] = None
    # UPDATE_READY
    ac_update_ready_download_url: Optional[str] = None
    ac_update_ready_download_label: Optional[str] = None
    ac_update_ready_logs_url: Optional[str] = None
    ac_update_ready_logs_label: Optional[str] = None
    # POPUP_MESSAGE
    # If url is populated, opens the given url in a webbrowser, otherwise
    # this popup can just be dismissed.
    ac_popup_message_body: Optional[str] = None
    ac_popup_message_url: Optional[str] = None


@dataclass
class DisplayError:
    """Container object for errors that the addon encountered."""
    button_label: str  # Short label for button drawing
    description: str  # Longer description of the issue and what to do.
    asset_id: str  # Optional value, if specific to a single asset.
    asset_name: str  # Optional value, if specific to a single asset.


def build_update_notification():
    """Construct the a update notification if available."""
    if not cTB.updater.update_ready:
        return

    this_update = cTB.updater.update_data
    vstring = updater.t2v([str(x) for x in this_update.version])
    logs = "https://docs.google.com/document/d/1VtWk60JgaWZxuVwLGdtYbzRofnMCI7IjRXF6okwpYVI/edit?usp=sharing"

    update_notice = Notification(
        notification_id="UPDATE_READY_MANUAL_INSTALL",
        title="Update ready:",
        action=Notification.ActionType.UPDATE_READY,
        tooltip=f"Download the {vstring} update.",
        allow_dismiss=True,
        ac_update_ready_download_url=this_update.url,
        ac_update_ready_download_label="Install",
        ac_update_ready_logs_url=logs,
        ac_update_ready_logs_label="Logs"
    )
    return update_notice


def build_no_internet_notification():
    msg = (
        "Please connect to the internet to continue using the Poliigon "
        "Addon."
    )
    notice = Notification(
        notification_id="NO_INTERNET_CONNECTION",
        title="No internet access",
        action=Notification.ActionType.POPUP_MESSAGE,
        tooltip=msg,
        allow_dismiss=False,
        ac_popup_message_body=msg
    )
    return notice


def build_proxy_notification():
    msg = ("Error: Blender cannot connect to the internet.\n"
           "Disable network proxy or firewalls.")
    notice = Notification(
        notification_id="PROXY_CONNECTION_ERROR",
        title="Encountered proxy error",
        action=Notification.ActionType.POPUP_MESSAGE,
        tooltip=msg,
        allow_dismiss=False,
        ac_popup_message_body=msg
    )
    return notice


class c_Toolbox:

    # Container for any notifications to show user in the panel UI.
    notifications = []
    # Containers for errors to persist in UI for drawing, e.g. after dload err.
    ui_errors = []

    updater = None  # Callable set up on register.

    # Static strings referenced elsewhere:
    ERR_CREDS_FORMAT = "Invalid email format/password length."

    def __init__(self, api_service=None):
        if api_service is None:
            self._api = api.PoliigonConnector(
                software="blender",
                get_optin=reporting.get_optin,
                report_message=reporting.capture_message,
                status_listener=self.update_api_status_banners)
        else:
            self._api = api_service

    def register(self, version: str):
        """Deferred registration, to ensure properties exist."""
        self.version = version
        software_version = ".".join([str(x) for x in bpy.app.version])
        self._api.register_update(self.version, software_version)

        self.updater = updater.SoftwareUpdater(
            addon_name="poliigon-addon-blender",
            addon_version=updater.v2t(version),
            software_version=bpy.app.version
        )
        self.updater.last_check_callback = last_update_callback

        self.gScriptDir = os.path.join(os.path.dirname(__file__), "files")
        # Output used to recognize a fresh install (or update).
        any_updated = self.update_files(self.gScriptDir)

        # TODO(SOFT-58): Defer folder creation and prompt for user path.
        base_dir = os.path.join(
            os.path.expanduser("~").replace("\\", "/"),
            "Poliigon")

        self.gSettingsDir = os.path.join(base_dir, "Blender")
        f_MDir(self.gSettingsDir)

        self.gOnlinePreviews = os.path.join(base_dir, "OnlinePreviews")
        f_MDir(self.gOnlinePreviews)

        self.gSettingsFile = os.path.join(
            self.gSettingsDir, "Poliigon_Blender_Settings.ini")

        # self.vAsset = None

        print(":" * 100)
        print("\n", "Starting the Poliigon Addon for Blender...", "\n")
        print(self.gSettingsFile)
        print("Toggle verbose logging in addon prefrences")

        self.vRunning = 1
        self.vRedraw = 0
        self.vWidth = 0

        self.vRequests = 0

        self.vCheckScale = 0

        self.vGettingData = 0

        # Flag which triggers getting local assets again when settings change
        self.vRerunGetLocalAssets = False

        self.vTimer = time.time()

        self.vSettings = {}
        self.skip_legacy_settings = ["name", "email"]

        # ......................................................................................

        # Separating UI icons from asset previews.
        self.vIcons = bpy.utils.previews.new()
        self.vIcons.load("ICON_poliigon",
                         os.path.join(self.gScriptDir, "poliigon_logo.png"),
                         "IMAGE")
        self.vIcons.load("ICON_myassets",
                         os.path.join(self.gScriptDir, "my_assets.png"),
                         "IMAGE")
        self.vIcons.load("ICON_new",
                         os.path.join(self.gScriptDir, "poliigon_new.png"),
                         "IMAGE")
        self.vIcons.load("ICON_import",
                         os.path.join(self.gScriptDir, "poliigon_import.png"),
                         "IMAGE")
        self.vIcons.load("ICON_apply",
                         os.path.join(self.gScriptDir, "poliigon_apply.png"),
                         "IMAGE")
        self.vIcons.load("GET_preview",
                         os.path.join(self.gScriptDir, "get_preview.png"),
                         "IMAGE")
        self.vIcons.load("NO_preview",
                         os.path.join(self.gScriptDir, "icon_nopreview.png"),
                         "IMAGE")
        self.vIcons.load("NOTIFY",
                         os.path.join(self.gScriptDir, "poliigon_notify.png"),
                         "IMAGE")
        self.vIcons.load("NEW_RELEASE",
                         os.path.join(self.gScriptDir, "poliigon_new.png"),
                         "IMAGE")
        self.vIcons.load("ICON_cart",
                         os.path.join(self.gScriptDir, "cart_icon.png"),
                         "IMAGE")
        self.vIcons.load("ICON_working",
                         os.path.join(self.gScriptDir, "icon_working.gif"),
                         "MOVIE")
        self.vIcons.load("ICON_dots",
                         os.path.join(self.gScriptDir, "icon_dots.png"),
                         "IMAGE")
        self.vIcons.load("ICON_acquired_check",
                         os.path.join(self.gScriptDir, "acquired_checkmark.png"),
                         "IMAGE")

        self.vPreviews = bpy.utils.previews.new()

        self.vPreviewsLoaded = []

        # ......................................................................................

        self.vUser = {}
        self.vUser["name"] = ""
        self.vUser["id"] = ""
        self.vUser["credits"] = 0
        self.vUser["credits_od"] = 0
        self.vUser["plan_name"] = ""  # UI friendly name
        self.vUser["plan_credit"] = 0
        self.vUser["plan_next_renew"] = ""  # Datetime overall plan renew.
        self.vUser["plan_next_credits"] = ""  # Dateime when +plan_credit added
        self.vUser["is_free_user"] = None  # None until proven one or otherwise
        self.vIsFreeStatusSet = False  # Not saved to ini, flipped once per session.
        self.vLoginError = ""

        self.vSettings = {}
        self.vSettings["res"] = "4K"
        self.vSettings["maps"] = []

        self.vSuggestions = []

        self.vSearch = {}
        self.vSearch["poliigon"] = ""
        self.vSearch["my_assets"] = ""
        self.vSearch["imported"] = ""
        self.vLastSearch = ""

        self.vPage = {}
        self.vPage["poliigon"] = 0
        self.vPage["my_assets"] = 0
        self.vPage["imported"] = 0

        self.vPages = {}
        self.vPages["poliigon"] = 0
        self.vPages["my_assets"] = 0
        self.vPages["imported"] = 0

        self.vGoTop = 0

        self.vEditPreset = None

        self.vSetup = {}
        self.vSetup["size"] = None
        self.vSetup["disp"] = 1

        self.vPrevScale = 1.0
        self.vMatSlot = 0

        self.vTexExts = [".jpg", ".png", ".tif", ".exr"]
        self.vModExts = [".fbx", ".blend"]

        self.vMaps = [
            "ALPHA",
            "ALPHAMASKED",
            "AO",
            "BUMP",
            "BUMP16",
            "COL",
            "DIFF",
            "DISP",
            "DISP16",
            "EMISSIVE",
            "FUZZ",
            "GLOSS",
            "HDR",
            "IDMAP",
            "JPG",
            "MASK",
            "METALNESS",
            "NRM",
            "NRM16",
            "REFL",
            "ROUGHNESS",
            "SSS",
            "TRANSMISSION",
            "OVERLAY",
        ]
        self.vSizes = [f'{i+1}K' for i in range(18)] + ["HIRES"]
        self.vLODs = ['SOURCE'] + [f'LOD{i}' for i in range(5)]
        self.vVars = [f'VAR{i}' for i in range(1, 10)]

        self.vModSecondaries = ["Footrest", "Vase"]

        # .....................................................................

        self.f_GetSettings()
        self.prefs = self.get_prefs()
        self.ui_errors = []

        self.vActiveCat = self.vSettings["category"][self.vSettings["area"]]
        self.vAssetType = self.vActiveCat[0]

        if self.vSettings["last_update"]:
            self.updater.last_check = self.vSettings["last_update"]

        if any_updated and not self._api.token:
            # This means this was a new install without a local login token.
            # This setup won't pick up installs in new blender instances
            # where no login event had to happen, but will pick up the first
            # install on the same machine.
            now = datetime.datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            self.vSettings["first_enabled_time"] = now_str
            self.f_SaveSettings()

        # .....................................................................

        self.vCategories = {}
        self.vCategories["poliigon"] = {}
        self.vCategories["my_assets"] = {}
        self.vCategories["imported"] = {}
        self.vCategories["new"] = {}

        self.vAssetTypes = ["Textures", "Models", "HDRIs", "Brushes"]

        self.vAssets = {}
        self.vAssets["poliigon"] = {}
        self.vAssets["my_assets"] = {}
        self.vAssets["imported"] = {}
        self.vAssets["local"] = {}

        # Ensure the base keys always exist:
        for key in self.vAssetTypes:
            self.vAssets["poliigon"][key] = {}
            self.vAssets["my_assets"][key] = {}
            self.vAssets["imported"][key] = {}
            self.vAssets["local"][key] = {}

        self.vAssetsIndex = {}
        self.vAssetsIndex["poliigon"] = {}
        self.vAssetsIndex["my_assets"] = {}
        self.vAssetsIndex["imported"] = {}

        self.vPurchased = []

        # ..................................................

        self.vInterrupt = time.time()

        self.vInvalid = 0

        self.vWorking = {}
        self.vWorking["login"] = 0
        self.vWorking["startup"] = False

        self.vThreads = []

        self.vDownloadQueue = {}
        self.vPurchaseQueue = {}
        self.vDownloadCancelled = set()
        self.vPreviewsQueue = []
        self.vQuickPreviewQueue = {}

        self.vDownloadFailed = {}

        self.purchase_queue = queue.Queue()
        self.purchase_threads = []

        self.download_queue = queue.Queue()
        self.download_threads = []

        self.vPreviewsDownloading = []

        self.vGettingData = 1
        self.vWasWorking = False  # Identify if at last check, was still running.
        self.vGettingLocalAssets = 0
        self.vGotLocalAssets = 0

        self.vGettingPages = {}
        self.vGettingPages["poliigon"] = []
        self.vGettingPages["my_assets"] = []
        self.vGettingPages["imported"] = []

        self.f_GetCredits()
        self.f_GetUserInfo()
        self.f_GetSubscriptionDetails()

        self.f_GetAssets("my_assets", vMax=5000, vBackground=1)
        self.f_GetAssets()
        self.f_GetCategories()
        self.f_GetLocalAssets()

        self.vSortedAssets = []

        # ..................................................

        self.vActiveObjects = []
        self.vActiveAsset = None
        self.vActiveMat = None
        self.vActiveMatProps = {}
        self.vActiveTextures = {}
        self.vActiveFaces = {}
        self.vActiveMode = None

        self.vActiveMixProps = {}
        self.vActiveMix = None
        self.vActiveMixMat = None
        self.vMixTexture = ""

        self.vPropDefaults = {}
        self.vPropDefaults["Scale"] = 1.0
        self.vPropDefaults["Aspect Ratio"] = 1.0
        self.vPropDefaults["Normal Strength"] = 1.0
        self.vPropDefaults["Mix Texture Value"] = 0.0
        self.vPropDefaults["Mix Noise Value"] = 1.0
        self.vPropDefaults["Noise Scale"] = 5.0
        self.vPropDefaults["Noise Detail"] = 2.0
        self.vPropDefaults["Noise Roughness"] = 5.0
        self.vPropDefaults["Mix Softness"] = 0.5
        self.vPropDefaults["Mix Bias"] = 5.0

        self.vAllMats = None

        self.vInitialScreenViewed = False

        # Cache of time.time() to know if user too-recently tried to change
        # pages, thus causing potential icon loading issues with blender. Used
        # to trigger refresh_data.
        self.vLastPageChange = 0  # Cache of time.time()
        self.vReloadTriggerInterval = 0.5  # Triggered if less than interval.

    # ...............................................................................................

    def f_GetSettings(self):
        dbg = 0
        self.print_separator(dbg, "f_GetSettings")

        self.vSettings = {}
        self.vSettings["add_dirs"] = []
        self.vSettings["area"] = "poliigon"
        self.vSettings["auto_download"] = 1
        self.vSettings["category"] = {}
        self.vSettings["category"]["imported"] = ["All Assets"]
        self.vSettings["category"]["my_assets"] = ["All Assets"]
        self.vSettings["category"]["poliigon"] = ["All Assets"]
        self.vSettings["conform"] = 0
        self.vSettings["default_lod"] = "LOD1"
        self.vSettings["del_zip"] = 1
        self.vSettings["disabled_dirs"] = []
        self.vSettings["download_lods"] = 1
        self.vSettings["hide_labels"] = 1
        self.vSettings["hide_scene"] = 0
        self.vSettings["hide_suggest"] = 0
        self.vSettings["library"] = ""
        self.vSettings["location"] = "Properties"
        self.vSettings["mapping_type"] = "UV + UberMapping"
        self.vSettings["mat_props"] = []
        self.vSettings["mix_props"] = []
        self.vSettings["new_release"] = ""
        self.vSettings["last_update"] = ""
        self.vSettings["new_top"] = 1
        self.vSettings["notify"] = 5
        self.vSettings["open_count"] = 0
        self.vSettings["page"] = 10
        self.vSettings["preview_size"] = 7
        self.vSettings["previews"] = 1
        self.vSettings["set_library"] = ""
        self.vSettings["show_active"] = 1
        self.vSettings["show_add_dir"] = 1
        self.vSettings["show_asset_info"] = 1
        self.vSettings["show_credits"] = 1
        self.vSettings["show_default_prefs"] = 1
        self.vSettings["show_display_prefs"] = 1
        self.vSettings["show_import_prefs"] = 1
        self.vSettings["show_mat_ops"] = 0
        self.vSettings["show_mat_props"] = 0
        self.vSettings["show_mat_texs"] = 0
        self.vSettings["show_mix_props"] = 1
        self.vSettings["show_pass"] = 0
        self.vSettings["show_plan"] = 1
        self.vSettings["show_settings"] = 0
        self.vSettings["show_user"] = 0
        self.vSettings["sorting"] = "Latest"
        self.vSettings["unzip"] = 1
        self.vSettings["update_sel"] = 1
        self.vSettings["use_16"] = 1
        self.vSettings["use_ao"] = 1
        self.vSettings["use_bump"] = 1
        self.vSettings["use_disp"] = 1
        self.vSettings["use_subdiv"] = 1
        self.vSettings["version"] = self.version
        self.vSettings["win_scale"] = 1
        self.vSettings["first_enabled_time"] = ""

        self.vSettings["res"] = "2K"
        self.vSettings["lod"] = "SOURCE"
        self.vSettings["mres"] = "2K"
        self.vSettings["hdri"] = "1K"
        self.vSettings["hdrib"] = "8K"
        self.vSettings["hdrif"] = "EXR"
        self.vSettings["brush"] = "2K"
        self.vSettings["maps"] = self.vMaps

        # ...............................................................................................

        self.check_dpi()

        # ...............................................................................................

        self.vPresets = {}
        self.vMixPresets = {}

        self.vReleases = {}

        # ...............................................................................................

        if f_Ex(self.gSettingsFile):
            vConfig = ConfigParser.ConfigParser()
            vConfig.optionxform = str
            try:
                vConfig.read(self.gSettingsFile)
            except ConfigParser.ParsingError:
                # Corrupted file, just continue as the sections below will not
                # be found, and the addon will proceed with defaults set above.
                pass

            if vConfig.has_section("user"):
                for vK in vConfig.options("user"):
                    if vK in self.skip_legacy_settings:
                        continue
                    if vK in ["credits", "credits_od", "plan_credit"]:
                        try:
                            self.vUser[vK] = int(vConfig.get("user", vK))
                        except ValueError:
                            self.vUser[vK] = 0
                    elif vK == "is_free_user":
                        # Don't default to 0 value, default to not set for
                        # free user, as 0 is treated as an active user and thus
                        # whould not be shown the free query.
                        try:
                            self.vUser[vK] = int(vConfig.get("user", vK))
                        except ValueError:
                            self.vUser[vK] = None
                    elif vK == "token":
                        token = vConfig.get("user", "token")
                        if token and token != "None":
                            self._api.token = vConfig.get("user", "token")
                    else:
                        self.vUser[vK] = vConfig.get("user", vK)

                if self.vUser["id"]:
                    reporting.assign_user(self.vUser["id"])

            else:
                os.remove(self.gSettingsFile)
                vConfig = ConfigParser.ConfigParser()

            if vConfig.has_section("settings"):
                vVer = None
                if vConfig.has_option("settings", "version"):
                    vVer = vConfig.get("settings", "version")

                for vS in vConfig.options("settings"):
                    if vS.startswith("category"):
                        try:
                            vArea = vS.replace("category_", "")
                            self.vSettings["category"][vArea] = vConfig.get(
                                "settings", vS
                            ).split("/")
                            if "" in self.vSettings[vS]:
                                self.vSettings["category"][vArea].remove("")
                        except:
                            pass
                    else:
                        self.vSettings[vS] = vConfig.get("settings", vS)

                        if vS in [
                            "add_dirs",
                            "disabled_dirs",
                            "mat_props",
                            "mix_props",
                        ]:
                            self.vSettings[vS] = self.vSettings[vS].split(";")
                            if "" in self.vSettings[vS]:
                                self.vSettings[vS].remove("")
                        elif self.vSettings[vS] == "True":
                            self.vSettings[vS] = 1
                        elif self.vSettings[vS] == "False":
                            self.vSettings[vS] = 0
                        else:
                            try:
                                self.vSettings[vS] = int(self.vSettings[vS])
                            except:
                                try:
                                    self.vSettings[vS] = float(self.vSettings[vS])
                                except:
                                    pass

            if vConfig.has_section("presets"):
                for vP in vConfig.options("presets"):
                    try:
                        self.vPresets[vP] = [
                            float(vV) for vV in vConfig.get("presets", vP).split(";")
                        ]
                    except:
                        pass

            if vConfig.has_section("mixpresets"):
                for vP in vConfig.options("mixpresets"):
                    try:
                        self.vMixPresets[vP] = [
                            float(vV) for vV in vConfig.get("mixpresets", vP).split(";")
                        ]
                    except:
                        pass

            if vConfig.has_section("download"):
                for vO in vConfig.options("download"):
                    if vO == "res":
                        self.vSettings["res"] = vConfig.get("download", vO)
                    elif vO == "maps":
                        self.vSettings["maps"] = vConfig.get("download", vO).split(";")

        # ...............................................................................................

        self.vSettings["open_count"] += 1

        if self.vSettings["open_count"] > self.vSettings["notify"]:
            if not self.notifications:
                # Only add the feedback message if sufficient open count,
                # and there aren't existing notifications.
                feedback_url = "https://help.poliigon.com/articles/6342599-poliigon-addon-for-blender"
                feedback_url = self._api.add_utm_suffix(feedback_url)
                feedback_notice = Notification(
                    notification_id="ASK_FEEDBACK",
                    title="Do you have any feedback?",
                    action=Notification.ActionType.OPEN_URL,
                    ac_open_url_address=feedback_url,
                    ac_open_url_label="Share here",
                    icon="NOTIFY"
                )
                # Skipping until post launch for general feedback form.
                # self.notifications.append(feedback_notice)

        # ...............................................................................................

        # self.vSettings["library"] = ""
        if self.vSettings["library"] == "":
            self.vSettings["set_library"] = self.gSettingsDir.replace("Blender", "Library")

        self.vSettings["show_user"] = 0
        self.vSettings["mat_props_edit"] = 0

        self.vSettings["area"] = "poliigon"
        self.vSettings["category"]["poliigon"] = ["All Assets"]
        self.vSettings["category"]["imported"] = ["All Assets"]
        self.vSettings["category"]["my_assets"] = ["All Assets"]

        self.set_free_search()

        self.f_SaveSettings()

    def f_SaveSettings(self):
        dbg = 0
        self.print_separator(dbg, "f_SaveSettings")

        vConfig = ConfigParser.ConfigParser()
        vConfig.optionxform = str
        vConfig.read(self.gSettingsFile)

        # ................................................

        if not vConfig.has_section("user"):
            vConfig.add_section("user")

        for vK in self.vUser.keys():
            if vK in self.skip_legacy_settings:
                vConfig.remove_option("user", vK)
                continue
            vConfig.set("user", vK, str(self.vUser[vK]))

        # Save token as if cTB field, on load will be parsed to _api.token
        vConfig.set("user", "token", str(self._api.token))

        # ................................................

        if not vConfig.has_section("settings"):
            vConfig.add_section("settings")

        for vS in self.vSettings.keys():
            if vS == "category":
                for vA in self.vSettings[vS].keys():
                    vConfig.set(
                        "settings", vS + "_" + vA, "/".join(self.vSettings[vS][vA])
                    )

            elif vS in ["add_dirs", "disabled_dirs", "mat_props", "mix_props"]:
                vConfig.set("settings", vS, ";".join(self.vSettings[vS]))

            else:
                vConfig.set("settings", vS, str(self.vSettings[vS]))

        # ................................................

        if not vConfig.has_section("presets"):
            vConfig.add_section("presets")

        for vP in self.vPresets.keys():
            vConfig.set("presets", vP, ";".join([str(vV) for vV in self.vPresets[vP]]))

        # ................................................

        if not vConfig.has_section("mixpresets"):
            vConfig.add_section("mixpresets")

        for vP in self.vMixPresets.keys():
            vConfig.set(
                "mixpresets", vP, ";".join([str(vV) for vV in self.vMixPresets[vP]])
            )

        # ................................................

        if vConfig.has_section("download"):
            vConfig.remove_section("download")
        vConfig.add_section("download")

        for vK in self.vSettings:
            if vK == "res":
                vConfig.set("download", vK, self.vSettings[vK])
            elif vK == "maps":
                vConfig.set("download", vK, ";".join(self.vSettings[vK]))

        # ................................................

        f_MDir(self.gSettingsDir)

        with open(self.gSettingsFile, "w+") as vFile:
            vConfig.write(vFile)

    # .........................................................................

    def set_free_search(self):
        """Assigns or clears the search field on new login or startup.

        If the user is a free user, it should be added to the search text only
        once per logged in session.
        """
        # Return early if the user is not logged in anyways
        if not self.vUser["id"] or self.vUser["id"] == "None":
            return
        # Return early if the search value had already been assigned once for
        # this logged in session.
        if self.vIsFreeStatusSet and self.vUser["is_free_user"] is not None:
            return

        # If the user is a free user, load the free setting.
        if self.vUser["is_free_user"] == 1:
            self.vLastSearch = ""
            self.vSearch["poliigon"] = "free"
        elif self.vSearch["poliigon"] == "free":
            self.vLastSearch = "free"  # Set different to trigger re-query
            self.vSearch["poliigon"] = ""

        vProps = bpy.context.window_manager.poliigon_props
        vProps.search_poliigon = self.vSearch["poliigon"]
        self.vIsFreeStatusSet = True

    def refresh_ui(self):
        """Wrapper to decouple blender UI drawing from callers of self."""
        panel_update(bpy.context)

    def check_dpi(self):
        """Checks the DPI of the screen to adjust the scale accordingly.

        Used to ensure previews remain square and avoid text truncation.
        """
        prefs = bpy.context.preferences
        self.vSettings["win_scale"] = prefs.system.ui_scale

    def get_ui_scale(self):
        """Utility for fetching the ui scale, used in draw code."""
        self.check_dpi()
        return self.vSettings["win_scale"]

    def check_if_working(self):
        """See if the toolbox is currently running an operation."""
        # Not including `self.vGettingData` as that is just a flag for
        # displaying placeholders in the UI.
        res = 1 in list(self.vWorking.values())
        if res:
            self.vWasWorking = res
        return res

    # .........................................................................

    def is_logged_in(self):
        """Returns whether or not the user is currently logged in."""
        return self._api.token is not None and not self._api.invalidated

    def user_invalidated(self):
        """Returns whether or not the user token was invalidated."""
        return self._api.invalidated

    def clear_user_invalidated(self):
        """Clears any invalidation flag for a user."""
        self._api.invalidated = False

    def check_backplate(self, asset_name):
        """Return bool on whether this asset is a backplate."""
        lwr = asset_name.lower()
        return any(
            lwr.startswith(vS) for vS in ["backdrop", "backplate"])

    # .........................................................................

    def initial_view_screen(self):
        """Reports view from a draw panel, to avoid triggering until use."""
        if self.vInitialScreenViewed is True:
            return
        self.vInitialScreenViewed = True
        self.track_screen_from_area()

    def track_screen_from_area(self):
        """Signals the active screen in background if opted in"""
        area = self.vSettings["area"]
        if area == "poliigon":
            self.track_screen("home")
        elif area == "my_assets":
            self.track_screen("my_assets")
        elif area == "imported":
            self.track_screen("imported")
        elif area == "account":
            self.track_screen("my_account")

    def track_screen(self, area):
        """Signals input screen area in a background thread if opted in."""
        if not self._api._is_opted_in():
            return
        vThread = threading.Thread(
            target=self._api.signal_view_screen,
            args=(area,),
        )
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    def register_notification(self, notice):
        """Stores and displays a new notification banner and signals event."""
        self.print_debug(0, "Creating notice: ", notice.notification_id)
        # Clear any notifications with the same id.
        pre_existing = False
        for existing_notice in self.notifications:
            if existing_notice.notification_id == notice.notification_id:
                self.notifications.remove(existing_notice)
                pre_existing = True
        self.notifications.append(notice)

        if not self._api._is_opted_in() or pre_existing:
            return

        vThread = threading.Thread(
            target=self._api.signal_view_notification,
            args=(notice.notification_id,),
        )
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    def click_notification(self, notification_id, action):
        """Signals event for click notification."""
        if not self._api._is_opted_in():
            return
        vThread = threading.Thread(
            target=self._api.signal_click_notification,
            args=(notification_id, action,),
        )
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    def dismiss_notification(self, notification_index):
        """Signals dismissed notification in background if user opted in."""
        ntype = self.notifications[notification_index].notification_id
        del self.notifications[notification_index]

        if not self._api._is_opted_in():
            return
        vThread = threading.Thread(
            target=self._api.signal_dismiss_notification,
            args=(ntype,),
        )
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    def signal_import_asset(self, asset_id):
        """Signals an asset import in the background if user opted in."""
        if not self._api._is_opted_in():
            return
        vThread = threading.Thread(
            target=self._api.signal_import_asset,
            args=(asset_id,),
        )
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    def signal_preview_asset(self, asset_id):
        """Signals an asset preview in the background if user opted in."""
        if not self._api._is_opted_in():
            return
        vThread = threading.Thread(
            target=self._api.signal_preview_asset,
            args=(asset_id,),
        )
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    # .........................................................................

    #@timer
    def f_Login(self, vMode):
        self.clear_user_invalidated()
        dbg = 0
        self.print_separator(dbg, "f_Login")
        if vMode == "login":

            elapsed_s = None
            if self.vSettings["first_enabled_time"]:
                now = datetime.datetime.now()
                install_tstr = self.vSettings["first_enabled_time"]
                install_t = datetime.datetime.strptime(
                    install_tstr, "%Y-%m-%d %H:%M:%S")
                elapsed = now - install_t
                elapsed_s = int(elapsed.total_seconds())
                if elapsed_s <= 0:
                    self.print_debug(0, "Throwing out negative elapsed time")
                    elapsed_s = None

            vReq = self._api.log_in(
                bpy.context.window_manager.poliigon_props.vEmail,
                bpy.context.window_manager.poliigon_props.vPassHide,
                time_since_enable=elapsed_s)

            if vReq.ok:
                vData = vReq.body

                self.vUser["name"] = vData["user"]["name"]
                self.vUser["id"] = vData["user"]["id"]

                # Ensure logging is associated with this user.
                reporting.assign_user(self.vUser["id"])

                self.vUser["credits"] = 0
                self.vUser["credits_od"] = 0
                self.vUser["plan_name"] = None
                self.vUser["plan_credit"] = None
                self.vUser["plan_next_renew"] = None
                self.vUser["plan_next_credits"] = None
                self.vUser["is_free_user"] = None

                self.f_GetCredits()
                self.f_GetCategories()

                # Non threaded to avoid double request with GetAssets,
                # as this may trigger a change in the default search query
                # to be 'free'
                self.f_APIGetSubscriptionDetails()

                # Fetch updated assets automatically.
                self.f_GetAssets("my_assets", vMax=5000, vBackground=1)
                self.f_GetAssets()

                self.vLoginError = ""

                # Clear out password after login attempt
                bpy.context.window_manager.poliigon_props.vPassHide = ""
                bpy.context.window_manager.poliigon_props.vPassShow = ""

                # Reset navigation on login
                self.vSettings["area"] = "poliigon"
                self.track_screen_from_area()

                self.vSettings["category"]["imported"] = ["All Assets"]
                self.vSettings["category"]["my_assets"] = ["All Assets"]
                self.vSettings["category"]["poliigon"] = ["All Assets"]
                self.vSettings["show_settings"] = 0
                self.vSettings["show_user"] = 0

                self.print_debug(dbg, "f_Login", "Login success")

                # Clear time since install since successful.
                if elapsed_s is not None:
                    self.vSettings["first_enabled_time"] = ""
                    self.f_SaveSettings()

            else:
                self.print_debug(dbg, "f_Login", "ERROR", vReq.error)
                self.vLoginError = vReq.error

            self.refresh_ui()

        elif vMode == "logout":
            req = self._api.log_out()
            reporting.assign_user(None)  # Clear user id from reporting.
            if req.ok:
                self.print_debug(dbg, "f_Login", "Logout success")
            else:
                self.print_debug(dbg, "f_Login", "ERROR", req.error)
                reporting.capture_message("logout_error", req.error, 'error')

            self._api.token = None

            # Clear out all user fields on logout.
            self.vUser["credits"] = 0
            self.vUser["credits_od"] = 0
            self.vUser["plan_name"] = None
            self.vUser["plan_next_renew"] = None
            self.vUser["plan_next_credits"] = None
            self.vUser["plan_credit"] = None
            self.vUser["is_free_user"] = None
            self.vUser["token"] = None
            self.vUser["name"] = None
            self.vUser["id"] = None

            self.vIsFreeStatusSet = False  # Reset as linked to user.

            bpy.context.window_manager.poliigon_props.vEmail = ""
            bpy.context.window_manager.poliigon_props.vPassHide = ""
            bpy.context.window_manager.poliigon_props.vPassShow = ""

            self.refresh_ui()

        self.f_SaveSettings()

        self.vWorking["login"] = 0

        self.vRedraw = 1
        self.refresh_ui()

    # .........................................................................

    def f_GetCategories(self):
        dbg = 0
        self.print_separator(dbg, "f_GetCategories")

        vThread = threading.Thread(target=self.f_APIGetCategories)
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    def f_GetCategoryChildren(self, vType, vCat):
        dbg = 0
        # self.print_separator(dbg, "f_GetCategoryChildren")

        vChldrn = vCat["children"]
        for vC in vChldrn:
            vPath = []
            for vS in vC["path"].split("/"):
                vS = " ".join([vS1.capitalize() for vS1 in vS.split("-")])
                vPath.append(vS)

            vPath = ("/".join(vPath)).replace("/" + vType + "/", "/")
            vPath = vPath.replace("/Hdrs/", "/")

            if "Generators" in vPath:
                continue

            # self.print_debug(dbg, "f_GetCategoryChildren", vPath)

            self.vCategories["poliigon"][vType][vPath] = []

            if len(vC["children"]):
                self.f_GetCategoryChildren(vType, vC)

    @reporting.handle_function(silent=True)
    def f_APIGetCategories(self):
        """Fetch and save categories to file."""
        dbg = 0
        self.print_separator(dbg, "f_APIGetCategories")
        vReq = self._api.categories()
        if vReq.ok:
            # self.print_debug(dbg, "f_APIGetCategories", str(vReq.body))
            if not len(vReq.body):
                self.print_debug(
                    dbg, "f_APIGetCategories", "ERROR",
                    vReq.error, ", ", vReq.body)

            for vC in vReq.body:
                vType = vC["name"]
                self.print_debug(dbg, "f_APIGetCategories", vType)
                if vType not in self.vCategories["poliigon"].keys():
                    self.vCategories["poliigon"][vType] = {}
                self.f_GetCategoryChildren(vType, vC)
                self.print_debug(
                    dbg, "f_APIGetCategories",
                    str(self.vCategories["poliigon"][vType]))

            vDataFile = os.path.join(self.gSettingsDir, "TB_Categories.json")
            with open(vDataFile, "w") as vWrite:
                json.dump(self.vCategories, vWrite)
        self.refresh_ui()

    # .........................................................................

    #@timer
    def f_GetAssets(self, vArea=None, vPage=None, vMax=None,
                    vBackground=0, vUseThread=True):
        dbg = 0
        self.print_separator(dbg, "f_GetAssets")
        self.print_debug(dbg, "f_GetAssets", vArea, vPage, vMax, vBackground)

        if vArea is None:
            vArea = self.vSettings["area"]

        if vPage is None:
            vPage = self.vPage[vArea]

        if vMax is None:
            vMax = self.vSettings["page"]

        vPageAssets, vPageCount = self.f_GetPageAssets(vPage)
        if len(vPageAssets):
            return

        # .........................................................................

        if vPage in self.vGettingPages[vArea]:
            return

        self.vGettingPages[vArea].append(vPage)

        vSearch = self.vSearch[vArea]

        vKey = "/".join([vArea] + self.vSettings['category'][vArea])
        if vSearch != "":
            vKey = "@".join(
                [vArea] + self.vSettings['category'][vArea] + [vSearch]
            )
        self.print_debug(dbg, "f_GetAssets", vKey)
        now = time.time()

        if vUseThread:
            args = (vArea, vPage, vMax, vSearch, vKey, vBackground, now)
            vThread = threading.Thread(
                target=self.f_APIGetAssets,
                args=args
            )
            vThread.daemon = 1
            vThread.start()
            self.vThreads.append(vThread)
        else:
            self.f_APIGetAssets(
                vArea, vPage, vMax, vSearch, vKey, vBackground, now)

    @reporting.handle_function(silent=True)
    def f_APIGetAssets(self, vArea, vPage, vMax, vSearch, vKey, vBackground, vTime):
        dbg = 0
        self.print_separator(dbg, "f_APIGetAssets")
        self.print_debug(
            dbg, "f_APIGetAssets", vPage + 1, vMax, vKey, vBackground, vTime)

        # ...............................................................

        if not self.vRunning:
            return

        if not vBackground:
            self.vGettingData = 1

        # ...............................................................

        vGetPage = int((vPage * self.vSettings["page"]) / vMax)

        vData = {
            "query": vSearch,
            "page": vGetPage + 1,
            "perPage": vMax,
            "algoliaParams": {"facetFilters": [], "numericFilters": ["Credit>=0"]},
        }

        vCat = self.vSettings["category"][vArea][0]

        if len(self.vSettings["category"][vArea]) > 1:
            if self.vSettings["category"][vArea][1] == "Free":
                vData["algoliaParams"]["numericFilters"] = ["Credit=0"]

            if vCat == "All Assets":
                vData["algoliaParams"]["facetFilters"] = [[]]
                for vType in self.vAssetTypes:
                    if (
                        "/" + self.vSettings["category"][vArea][1]
                        in self.vCategories[vArea][vType].keys()
                    ):
                        vCat = [vType] + self.vSettings["category"][vArea][1:]
                        vLvl = len(vCat) - 1
                        vCat = " > ".join(vCat).replace("HDRIs", "HDRs")
                        vData["algoliaParams"]["facetFilters"][0].append(
                            "RefineCategories.lvl" + str(vLvl) + ":" + vCat
                        )

            else:
                vLvl = len(self.vSettings["category"][vArea]) - 1
                vCat = " > ".join(self.vSettings["category"][vArea])
                vCat = vCat.replace("HDRIs", "HDRs")
                vData["algoliaParams"]["facetFilters"] = [
                    "RefineCategories.lvl" + str(vLvl) + ":" + vCat
                ]

        elif vCat != "All Assets":
            vCat = vCat.replace("HDRIs", "HDRs")
            vData["algoliaParams"]["facetFilters"] = ["RefineCategories.lvl0:" + vCat]

        self.print_debug(dbg, "f_APIGetAssets", json.dumps(vData))

        # ...............................................................

        if self.vInterrupt > vTime or not self.vRunning:
            return

        check_owned = vArea == "my_assets"
        if check_owned:
            vReq = self._api.get_user_assets(query_data=vData)
        else:
            vReq = self._api.get_assets(query_data=vData)

        if vPage in self.vGettingPages[vArea]:
            self.vGettingPages[vArea].remove(vPage)

        # ...............................................................

        if vReq.ok:
            try:
                vData = vReq.body.get("data")
            except:
                return

            total = vReq.body.get("total")
            self.print_debug(
                dbg,
                "f_APIGetAssets",
                f"{len(vData)} assets ({total} total)"
            )

            vPages = int(
                (vReq.body.get("total") / self.vSettings["page"]) + 0.999)

            if not vBackground and vPage == self.vPage[vArea]:
                self.vPages[vArea] = vPages

            if vKey not in self.vAssetsIndex[vArea].keys():
                self.vAssetsIndex[vArea][vKey] = {}
                self.vAssetsIndex[vArea][vKey]["pages"] = vPages

            self.print_debug(
                dbg, "f_APIGetAssets", len(vData), vPages, "pages")

            vIdx = vGetPage * vMax

            for vA in vData:
                did_load = self.load_asset(vA, vArea, vKey, vIdx)

                if did_load:
                    self.vRedraw = 1
                    self.refresh_ui()

                    vIdx += 1

            if self.vInterrupt > vTime or not self.vRunning:
                return

            if not vBackground and vPage == self.vPage[vArea]:
                self.vGettingData = 0

                self.vRedraw = 1
                self.refresh_ui()

        else:
            self.print_debug(dbg, "f_APIGetAssets", "ERROR", vReq.error)

    def load_asset(self, vA, vArea, vKey, vIdx):
        """Loads a single asset into the structure.

        Args:
            vA: Asset data.
            vArea: Interface load context.
            vKey: Key for this asset.
            vIdx: Index within current struncure loading into.

        Return: bool on whether did load asset, false if skipped.
        """
        vType = vA["type"].replace("HDRS", "HDRIs")

        if vType == "Substances":
            return False

        if vType not in self.vAssets[vArea].keys():
            self.vAssets[vArea][vType] = {}

        vName = vA["asset_name"]

        if vArea == "my_assets" and vName not in self.vPurchased:
            self.vPurchased.append(vName)

        # TODO: Turn this into a dataclass structure to avoid keying.
        self.vAssets[vArea][vType][vName] = {}
        self.vAssets[vArea][vType][vName]["name"] = vName
        self.vAssets[vArea][vType][vName]["id"] = vA["id"]
        self.vAssets[vArea][vType][vName]["slug"] = vA["slug"]
        self.vAssets[vArea][vType][vName]["type"] = vType
        self.vAssets[vArea][vType][vName]["files"] = []
        self.vAssets[vArea][vType][vName]["maps"] = []
        self.vAssets[vArea][vType][vName]["lods"] = []
        self.vAssets[vArea][vType][vName]["sizes"] = []
        self.vAssets[vArea][vType][vName]["workflows"] = []
        self.vAssets[vArea][vType][vName]["vars"] = []
        self.vAssets[vArea][vType][vName]["date"] = vA["published_at"]
        self.vAssets[vArea][vType][vName]["credits"] = vA["credit"]
        self.vAssets[vArea][vType][vName]["categories"] = vA["categories"]
        self.vAssets[vArea][vType][vName]["preview"] = ""
        self.vAssets[vArea][vType][vName]["thumbnails"] = []
        self.vAssets[vArea][vType][vName]["quick_preview"] = vA["toolbox_previews"]

        if "lods" in vA.keys():
            self.vAssets[vArea][vType][vName]["lods"] = vA["lods"]

        if len(vA["previews"]):
            # Primary thumbnail previews
            self.vAssets[vArea][vType][vName]["preview"] = vA["previews"][0]
            # Additional previews, skipping e.g. mview files.
            valid = [x for x in vA["previews"]
                     if ".png" in x or ".jpg" in x]
            self.vAssets[vArea][vType][vName]["thumbnails"] = valid

        # Asset-type based loading.
        if vType in ["Textures", "HDRIs", "Brushes"]:
            # Identify workflow types and sizes available.
            all_sizes = []
            if "render_schema" in vA.keys():
                for schema in vA["render_schema"]:

                    # Set workflow type
                    workflow = schema.get('name', 'REGULAR')
                    if workflow not in self.vAssets[vArea][vType][vName]["workflows"]:
                        self.vAssets[vArea][vType][vName]["workflows"].append(workflow)

                    # A single 'type' is a dict of a single map, such as:
                    # {
                    #    "type_code": "COL",  # COL here even if 'SPECULAR_COL'
                    #    "type_name": "Diffuse",
                    #    "type_preview": "diffuse.jpg",
                    #    "type_options": ["1K", "2K", "3K", "4K"]
                    # }
                    if "types" in schema.keys():
                        for vM in schema["types"]:
                            all_sizes.extend(vM["type_options"])
            all_sizes = list(set(all_sizes))
            self.vAssets[vArea][vType][vName]["sizes"] = all_sizes

            # Workflow partitioned map names, e.g. "SPECULAR_COL"
            self.vAssets[vArea][vType][vName]["maps"] = vA.get("type_options")
        elif vType == "Models":

            self.vAssets[vArea][vType][vName]["workflows"] = ["METALNESS"]

            self.vAssets[vArea][vType][vName]["sizes"] = vA["render_schema"]["options"]

        # Cleanup processing.
        sorted_sizes = [vS for vS in self.vSizes
                        if vS in self.vAssets[vArea][vType][vName]["sizes"]]
        if not sorted_sizes:
            # Keep the same sizes as they will exist online, but un-sorted.
            self.print_debug(0, "Invalid sizes found",
                             self.vAssets[vArea][vType][vName]["sizes"])
            # Disabling this as volume can be large, given number of times
            # already seen during UAT.
            # reporting.capture_message(
            #     "asset_size_empty",
            #     self.vAssets[vArea][vType][vName]["sizes"],
            #     'error')
        else:
            self.vAssets[vArea][vType][vName]["sizes"] = sorted_sizes

        self.vAssetsIndex[vArea][vKey][vIdx] = [vType, vName]

        return True  # Indicates structure was loaded.

    #@timer
    def f_GetPageAssets(self, vPage):
        dbg = 0
        self.print_separator(dbg, "f_GetPageAssets")

        vArea = self.vSettings["area"]

        vSearch = self.vSearch[vArea]

        vMax = self.vSettings["page"]

        vPageAssets = []
        vPageCount = 0
        if vArea in self.vAssetsIndex.keys():
            vKey = "/".join([vArea] + self.vSettings['category'][vArea])
            if vSearch != "":
                vKey = "@".join([vArea] + self.vSettings['category'][vArea] + [vSearch])

            self.print_debug(dbg, "f_GetPageAssets", vKey)

            if vKey in self.vAssetsIndex[vArea].keys():
                for i in range(vPage * vMax, (vPage * vMax) + vMax):
                    if i in self.vAssetsIndex[vArea][vKey].keys():
                        vType, vAsset = self.vAssetsIndex[vArea][vKey][i]

                        try:
                            vPageAssets.append(self.vAssets[vArea][vType][vAsset])
                        except KeyError as err:
                            print("Failed to vPageAssets.append")
                            print(err)

                vPageCount = self.vAssetsIndex[vArea][vKey]['pages']

        return [vPageAssets, vPageCount]

    #@timer
    def f_GetAssetsSorted(self, vPage):
        dbg = 0
        self.print_separator(dbg, "f_GetAssetsSorted")

        vArea = self.vSettings["area"]
        vSearch = self.vSearch[vArea]

        if vArea in ["poliigon", "my_assets"]:
            vPageAssets, vPageCount = self.f_GetPageAssets(vPage)
            if len(vPageAssets):
                self.vPages[vArea] = vPageCount
                return vPageAssets

            if self.vGettingData:
                self.print_debug(dbg, "f_GetAssetsSorted", "f_DummyAssets")
                return self.f_DummyAssets()

            else:
                self.print_debug(dbg, "f_GetAssetsSorted", "[]")
                return []

        else:
            vAssetType = self.vSettings["category"]["imported"][0]

            vSortedAssets = []
            for vType in list(self.vAssets["imported"].keys()):
                if vAssetType in ["All Assets", vType]:
                    for vA in self.vAssets["imported"][vType].keys():
                        if (
                            len(vSearch) >= 3
                            and vSearch.lower() not in vA.lower()
                        ):
                            continue

                        if vType in self.vAssets["local"].keys():
                            if vA in self.vAssets["local"][vType].keys():
                                vSortedAssets.append(self.vAssets["local"][vType][vA])

            self.vPages[vArea] = int(
                (len(vSortedAssets) / self.vSettings["page"]) + 0.99999
            )

            return vSortedAssets

    def get_poliigon_asset(self, vType, vAsset):
        """Get the data for a single explicit asset of a given type."""
        if vType not in self.vAssets["poliigon"]:
            self.print_debug(0, f"Was missing {vType}, populated now")
            self.vAssets["poliigon"][vType] = {}

        if vAsset not in self.vAssets["poliigon"][vType]:
            # Handle a given datapoint being missing at moment of request
            # and fetch it.
            # raise Exception("Asset is not avaialble")

            # This is the exception, not the norm, and should be trated as a
            # warning. This would mostly occur when there is a cache miss if
            # an operator is called for an arbitrary asset from an automated
            # script and not from within the normal use of the plugin.
            self.print_debug(
                0,
                "get_poliigon_asset",
                f"Had to fetch asset info for {vAsset}")
            vArea = "poliigon"
            vSearch = vAsset
            vKey = "@".join([vArea] + self.vSettings['category'][vArea] + [vSearch])

            vPage = 0
            vMax = 100
            self.f_APIGetAssets(
                vArea, vPage, vMax, vSearch, vKey, 0, time.time())

            if not self.vAssets["poliigon"][vType].get(vAsset):
                raise RuntimeError("Failed to fetch asset information")
            else:
                # Report this cache miss, as generally shouln't happen.
                reporting.capture_message("get_asset_miss", vAsset, 'error')

        return self.vAssets["poliigon"][vType].get(vAsset)

    def get_data_for_asset_id(self, asset_id):
        """Get the data structure for an asset by asset_id alone."""
        area_order = ["poliigon", "my_assets", "local"]
        for area in area_order:
            subcats = list(self.vAssets[area])
            for cat in subcats:  # e.g. HDRIs
                for asset in self.vAssets[area][cat]:
                    if self.vAssets[area][cat][asset].get("id") == asset_id:
                        return self.vAssets[area][cat][asset]

        # Failed to fetch asset, return empty structure.
        return {}

    def get_data_for_asset_name(self, asset_name):
        """Get the data structure for an asset by asset_name alone."""
        area_order = ["poliigon", "my_assets", "local"]
        for area in area_order:
            subcats = list(self.vAssets[area])
            for cat in subcats:
                for asset in self.vAssets[area][cat]:
                    if asset == asset_name:
                        return self.vAssets[area][cat][asset]

        # Failed to fetch asset, return empty structure.
        return {}

    def f_DummyAssets(self):
        dbg = 0
        self.print_separator(dbg, "f_DummyAssets")

        vDummyAssets = []

        vDummy = {}
        vDummy["name"] = "dummy"
        vDummy["slug"] = ""
        vDummy["type"] = ""
        vDummy["files"] = []
        vDummy["maps"] = []
        vDummy["lods"] = []
        vDummy["sizes"] = []
        vDummy["vars"] = []
        vDummy["date"] = ""
        vDummy["credits"] = 0
        vDummy["categories"] = []
        vDummy["preview"] = ""
        vDummy["thumbnails"] = []

        for i in range(self.vSettings["page"]):
            vDummyAssets.append(vDummy)

        return vDummyAssets

    def f_UpdateData(self):
        dbg = 0
        self.print_separator(dbg, "f_UpdateData")

        vDFile = self.gSettingsDir + "/Poliigon_Data.ini"

        vConfig = ConfigParser.ConfigParser()
        vConfig.optionxform = str
        if f_Ex(vDFile):
            vConfig.read(vDFile)

        vArea = "my_assets"

        if vArea in self.vAssets.keys():
            for vType in self.vAssets[vArea].keys():
                for vAsset in self.vAssets[vArea][vType].keys():
                    if not vConfig.has_section(vAsset):
                        vConfig.add_section(vAsset)

                    vConfig.set(vAsset, "id", self.vAssets[vArea][vType][vAsset]["id"])
                    vConfig.set(
                        vAsset, "type", self.vAssets[vArea][vType][vAsset]["type"]
                    )
                    vConfig.set(
                        vAsset, "date", self.vAssets[vArea][vType][vAsset]["date"]
                    )
                    vConfig.set(
                        vAsset,
                        "categories",
                        ";".join(self.vAssets[vArea][vType][vAsset]["date"]),
                    )

        with open(vDFile, "w+") as vFile:
            vConfig.write(vFile)

    # .........................................................................

    def f_GetCredits(self):
        dbg = 0
        self.print_separator(dbg, "f_GetCredits")

        vThread = threading.Thread(target=self.f_APIGetCredits)
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    @reporting.handle_function(silent=True)
    def f_APIGetCredits(self):
        dbg = 0
        self.print_separator(dbg, "f_APIGetCredits")

        vReq = self._api.get_user_balance()

        if vReq.ok:
            self.vUser["credits"] = vReq.body.get("subscription_balance")
            self.vUser["credits_od"] = vReq.body.get("ondemand_balance")
        else:
            self.print_debug(dbg, "f_APIGetCredits", "ERROR", vReq.error)

    # .........................................................................

    def f_GetUserInfo(self):
        dbg = 0
        self.print_separator(dbg, "f_GetUserInfo")

        vThread = threading.Thread(target=self.f_APIGetUserInfo)
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    @reporting.handle_function(silent=True)
    def f_APIGetUserInfo(self):
        dbg = 0
        self.print_separator(dbg, "f_APIGetUserInfo")

        vReq = self._api.get_user_info()

        if vReq.ok:
            self.vUser["name"] = vReq.body.get("user")["name"]
            self.vUser["id"] = vReq.body.get("user")["id"]
        else:
            self.print_debug(dbg, "f_APIGetUserInfo", "ERROR", vReq.error)

    # .........................................................................

    def f_GetSubscriptionDetails(self):
        dbg = 0
        self.print_separator(dbg, "f_GetSubscriptionDetails")

        vThread = threading.Thread(target=self.f_APIGetSubscriptionDetails)
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    @reporting.handle_function(silent=True)
    def f_APIGetSubscriptionDetails(self):
        """Fetches the current user's subscription status."""
        dbg = 0
        self.print_separator(dbg, "f_APIGetSubscriptionDetails")

        vReq = self._api.get_subscription_details()

        if vReq.ok:
            plan = vReq.body
            if plan.get("plan_name") and plan["plan_name"] != api.STR_NO_PLAN:
                self.vUser["plan_name"] = plan["plan_name"]
                self.vUser["plan_credit"] = plan.get("plan_credit", None)

                # Extract "2022-08-19" from "2022-08-19 23:58:37"
                renew = plan.get("next_subscription_renewal_date", "")
                renew = renew.split(" ")[0]
                self.vUser["plan_next_renew"] = renew

                next_credits = plan.get("next_credit_renewal_date", "")
                next_credits = next_credits.split(" ")[0]
                self.vUser["plan_next_credits"] = next_credits
                self.vUser["is_free_user"] = 0
            else:
                self.vUser["plan_name"] = None
                self.vUser["plan_credit"] = None
                self.vUser["plan_next_renew"] = None
                self.vUser["plan_next_credits"] = None
                self.vUser["is_free_user"] = 1

            self.set_free_search()
            self.f_SaveSettings()
        else:
            self.vUser["plan_name"] = None
            self.vUser["plan_credit"] = None
            self.vUser["plan_next_renew"] = None
            self.vUser["plan_next_credits"] = None
            self.vUser["is_free_user"] = None
            self.print_debug(
                dbg, "f_APIGetSubscriptionDetails", "ERROR", vReq.error)

    # .........................................................................

    def f_QueuePreview(self, vAsset, thumbnail_index=0):
        dbg = 0
        self.print_separator(dbg, "f_QueuePreview")

        vThread = threading.Thread(target=self.f_DownloadPreview,
                                   args=(vAsset, thumbnail_index))
        vThread.daemon = 1
        vThread.start()
        self.vThreads.append(vThread)

    @reporting.handle_function(silent=True)
    def f_DownloadPreview(self, vAsset, thumbnail_index):
        """Download a single thumbnail preview for a single asset."""
        dbg = 0
        self.print_separator(dbg, "f_DownloadPreview")

        if self.vSettings["area"] not in ["poliigon", "my_assets"]:
            return

        already_local = 0
        target_file = self.f_GetThumbnailPath(vAsset, thumbnail_index)
        target_base, target_ext = os.path.splitext(target_file)

        # Check if a partial or complete download already exists.
        for vExt in [".jpg", ".png", "X.jpg", "X.png"]:
            f_MDir(self.gOnlinePreviews)

            vQPrev = os.path.join(self.gOnlinePreviews, target_base + vExt)
            if f_Ex(vQPrev):
                self.print_debug(dbg, "f_DownloadPreview", vQPrev)
                if "X" in vExt:
                    try:
                        os.rename(vQPrev, vQPrev.replace("X.jpg", ".jpg"))
                    except:
                        os.remove(vQPrev)

                already_local = 1
                break

        if already_local:
            return

        # .....................................................................

        # Download to a temp filename.
        vPrev = os.path.join(self.gOnlinePreviews,
                             target_base + "X" + target_ext)

        vURL = None
        for vType in self.vAssets[self.vSettings["area"]]:
            # One of Models, HDRIs, Textures.
            if vAsset in self.vAssets[self.vSettings["area"]][vType]:
                cdn_url = (
                    "https://poliigon.com/cdn-cgi/image/"
                    "width={size},sharpen=1,q=75,f=auto/{url}")

                # This specific combo, width=300, sharpen=1, and q=75 will
                # ensure we make use of the same caching as the website.
                if thumbnail_index == 0:
                    base_url = self.vAssets[self.vSettings["area"]][vType][vAsset]["preview"]
                    vURL = cdn_url.format(size=300, url=base_url)
                else:
                    base_url = self.vAssets[self.vSettings["area"]][vType][
                        vAsset]["thumbnails"][thumbnail_index - 1]
                    vURL = cdn_url.format(size=1024, url=base_url)
                break

        if vURL:
            self.print_debug(dbg, "f_DownloadPreview", vPrev, vURL)

            resp = self._api.download_preview(vURL, vPrev)
            if resp.ok:
                if f_Ex(vPrev):
                    if vPrev.endswith("X.png"):
                        try:
                            os.rename(vPrev, vPrev.replace("X.png", ".png"))
                        except:
                            pass
                    else:
                        try:
                            os.rename(vPrev, vPrev.replace("X.jpg", ".jpg"))
                        except:
                            pass

                if thumbnail_index > 0:
                    pass  # Don't load large thumbnail into preview grid.
                elif vAsset not in self.vPreviews.keys():
                    if os.access(target_file, os.W_OK):
                        try:
                            self.vPreviews.load(vAsset, target_file, "IMAGE")
                        except KeyError:
                            pass  # Image already loaded into blender.
                        self.vPreviews[vAsset].reload()

                        self.vRedraw = 1
                        self.refresh_ui()
            else:
                print(f"Encountered preview download error: {len(resp.error)}")
        else:
            reporting.capture_message(
                "download_preview_error",
                f"Failed to find preview url for {vAsset}",
                'error')

        # Always remove from download queue (can have thread conflicts, so try)
        try:
            self.vPreviewsDownloading.remove(vAsset)
        except ValueError:  # Already removed.
            pass

    # .........................................................................

    def check_if_purchase_queued(self, asset_id):
        """Checks if an asset is queued for purchase"""
        queued = asset_id in list(self.vPurchaseQueue.keys())
        return queued

    def queue_purchase(self, asset_id, asset_data, start_thread=True):
        """Adds an asset to the purchase_queue and starts threads"""
        self.vPurchaseQueue[asset_id] = asset_data
        self.purchase_queue.put(asset_id)
        self.print_debug(0, f"Queued asset {asset_id}")

        self.purchase_threads = [
            thread for thread in self.purchase_threads if thread.is_alive()]

        if start_thread and len(self.purchase_threads) < MAX_PURCHASE_THREADS:
            thread = threading.Thread(target=self.purchase_assets_thread)
            thread.daemon = 1
            thread.start()
            self.purchase_threads.append(thread)

    @reporting.handle_function(silent=True)
    def purchase_assets_thread(self):
        """Thread to purchase queue of assets"""
        while self.purchase_queue.qsize() > 0:
            try:
                asset_id = int(self.purchase_queue.get_nowait())
            except queue.Empty:
                time.sleep(0.1)
                continue

            if not self.vRunning:
                print("Cancelling in progress purchases")
                return

            asset_data = self.vPurchaseQueue[asset_id]

            asset = asset_data['name']

            # Metadata required to pass forward
            wm_props = bpy.context.window_manager.poliigon_props
            search = wm_props.search_poliigon.lower()

            # Get the slug format of the active category, e.g.
            # from ["All Models"] to "/"
            # from ["Models", "Bathroom"] to "/models/bathroom"
            # and undo transforms of f_GetCategoryChildren.
            # TODO: Refactor f_GetCategoryChildren as part of Core migration.
            category = "/" + "/".join(
                [cat.lower().replace(" ", "-") for cat in self.vActiveCat]
            )
            if category.startswith("/hdris/"):
                category = category.replace("/hdris/", "/hdrs/")
            elif category == "/all-assets":
                category = "/"
            self.print_debug(0, "Active cat: ", self.vActiveCat, category)

            req = self._api.purchase_asset(asset_id, search, category)
            del self.vPurchaseQueue[asset_id]  # Remove regardless, for ui draw

            if req.ok:
                # Append purchased if success, or if the asset is free.
                self.vPurchased.append(asset)
                self.vAssets["my_assets"][asset_data["type"]][asset] = asset_data

                # Process auto download if setting enabled.
                if self.vSettings["auto_download"]:
                    self.vDownloadQueue[asset_id] = {
                        "data": asset_data,
                        "size": None,
                        "download_size": None
                    }
                    self.queue_download(asset_id)

            else:
                self.print_debug(
                    0, f"Failed to purchase asset {asset_id} {asset}",
                    str(req.error), str(req.body))

                # Check the reason for failure.
                if "enough credits" in req.error:
                    ui_err = DisplayError(
                        asset_id=asset_id,
                        asset_name=asset,
                        button_label="Need credits",
                        description=f"{req.error})"
                    )
                else:
                    ui_err = DisplayError(
                        asset_id=asset_id,
                        asset_name=asset,
                        button_label="Failed, retry",
                        description=f"Error during purchase, please try again ({req.error})"
                    )
                self.ui_errors.append(ui_err)

            # Clear cached data in index to prompt refresh after purchase
            self.vAssetsIndex["my_assets"] = {}

            # Runs in this same thread, and if there are many purchase
            # events then there may be multiple executions of this. It is
            # important that the last purchase always does update the
            # credits balance, so this tradeoff is ok to have overlapping
            # requests potentially.
            self.f_APIGetCredits()
            self.vRedraw = 1
            self.refresh_ui()

    # .........................................................................

    def refresh_data(self, icons_only=False):
        """Reload data structures of the addon to update UI and stale data.

        This function could be called in main or background thread.
        """
        self.print_debug(0, "refresh_data")
        thread = threading.Thread(
            target=self._refresh_data_thread,
            args=(icons_only,))
        thread.daemon = 1
        thread.start()
        self.vThreads.append(thread)

    @reporting.handle_function(silent=True)
    def _refresh_data_thread(self, icons_only):
        """Background thread for the data resets."""

        # Clear out state variables.
        self.vPreviews.clear()
        if icons_only is False:
            self.notifications = []
            self.vPurchased = []

            self.vAssetsIndex["poliigon"] = {}
            self.vAssetsIndex["my_assets"] = {}

        # Non-background thread requestes
        self.vGettingData = 1
        self.f_GetAssets(
            "my_assets", vMax=5000, vBackground=1)  # Populates vPurchased.
        self.f_GetAssets(vBackground=1)
        if icons_only is False:
            self.f_APIGetCategories()
            self.f_GetLocalAssetsThread()
        self.vGettingData = 0

        if icons_only is False:
            self.f_APIGetCredits()
            self.f_APIGetUserInfo()
            self.f_GetSubscriptionDetails()

        self.vRedraw = 1
        self.refresh_ui()

    def check_if_download_queued(self, asset_id):
        """Checks if an asset is queued for download"""
        cancelled = asset_id in self.vDownloadCancelled
        queued = asset_id in list(self.vDownloadQueue.keys())
        return queued and not cancelled

    def get_maps_by_workflow(self, maps, workflow):
        """Download only relevant maps.

        Where `workflow` should be one of: REGULAR, SPECULAR, METALNESS.
        """

        # Some maps in API belong only to a single workflow, even though
        # they are the same for both.
        force_dl = ["IDMAP"]

        # Each map should be in the form of "WORKFLOW_MAPNAME".
        target_maps = [
            m.split("_", maxsplit=1)[-1] for m in maps
            if m.startswith(workflow) or m.split("_", 1)[-1] in force_dl]
        return list(set(target_maps))

    def get_download_data(self, asset_data, size=None):
        """Cosntruct the data needed for the download.

        Args:
            asset_data: Original asset data structure.
            size: Intended download size like '4K', fallback to pref default.
        """
        sizes = [size]

        if size in ['', None]:
            if asset_data["type"] == "Textures":
                sizes = [self.vSettings["res"]]
            elif asset_data["type"] == "Models":
                sizes = [self.vSettings["mres"]]
            elif asset_data["type"] == "HDRIs":
                sizes = [self.vSettings["hdri"]]
            elif asset_data["type"] == "Brushes":
                sizes = [self.vSettings["brush"]]

            self.vDownloadQueue[asset_data["id"]]['size'] = sizes[0]

        download_data = {
            'assets': [
                {
                    'id': asset_data['id'],
                    'name': asset_data['name']
                }
            ]
        }

        if asset_data['type'] in ['Textures', 'HDRIs']:
            download_data['assets'][0]['workflows'] = []
            if 'METALNESS' in asset_data['workflows']:
                download_data['assets'][0]['workflows'] = ['METALNESS']
            elif 'REGULAR' in asset_data['workflows']:
                download_data['assets'][0]['workflows'] = ['REGULAR']
            elif 'SPECULAR' in asset_data['workflows']:
                download_data['assets'][0]['workflows'] = ['SPECULAR']

            maps = self.get_maps_by_workflow(
                asset_data['maps'],
                download_data['assets'][0]['workflows'][0])

            download_data['assets'][0]['type_codes'] = maps

        elif asset_data['type'] == 'Models':
            download_data['assets'][0]['lods'] = int(
                self.vSettings["download_lods"])

            download_data['assets'][0]['softwares'] = ['ALL_OTHERS']

        elif asset_data['type'] == 'Brushes':
            # No special data needed for Brushes
            pass

        download_data['assets'][0]['sizes'] = [
            size for size in sizes if size in asset_data['sizes']]
        if not len(download_data['assets'][0]['sizes']):
            for size in reversed(self.vSizes):
                if size in asset_data['sizes']:
                    download_data['assets'][0]['sizes'] = [size]
                    break
        if not download_data['assets'][0]['sizes']:
            self.print_debug(0, "Missing sizes for download", download_data)

        return download_data

    def queue_download(self, asset_id):
        """Adds an asset to the purchase_queue and starts thread if necessary"""
        self.download_queue.put(asset_id)

        self.download_threads = [
            thread for thread in self.download_threads if thread.is_alive()]

        if len(self.download_threads) < MAX_DOWNLOAD_THREADS:
            thread = threading.Thread(target=self.download_assets_thread)
            thread.daemon = 1
            thread.start()
            self.download_threads.append(thread)

    @reporting.handle_function(silent=True)
    def download_assets_thread(self):
        """Thread to download queue of assets"""
        while self.download_queue.qsize() > 0:
            if not self.vRunning:
                print("Cancelling in progress downloads")
                return

            try:
                asset_id = int(self.download_queue.get_nowait())
            except queue.Empty:
                time.sleep(0.1)
                continue

            self.download_asset(asset_id)

    def download_asset(self, asset_id):
        """Gathers download params and calls download function"""
        asset_data = self.vDownloadQueue[asset_id]['data']
        size = self.vDownloadQueue[asset_id]['size']
        asset = asset_data["name"]
        atype = asset_data["type"]

        download_data = self.get_download_data(asset_data, size=size)

        source_dir = self.vSettings["library"]
        primary_files = []
        add_files = []
        if asset in self.vAssets["local"][atype].keys():
            for file in self.vAssets["local"][atype][asset]["files"]:
                if f_Ex(file):
                    if file.split(asset, 1)[0] == source_dir:
                        primary_files.append(file)
                    else:
                        add_files.append(file)

            self.print_debug(0, "download_asset",
                             "Found asset files in primary library:",
                             primary_files)
            if not len(primary_files):
                # Asset must be located in an additional directory
                #
                # Always download new maps to the highest-level directory
                # containing asset name, regardless of any existing (sub)
                # structure within that directory
                if len(add_files):
                    file = add_files[0]
                    if asset in os.path.dirname(file):
                        source_dir = file.split(asset, 1)[0]
                        self.print_debug(1, "download_asset", source_dir)

        dst_file = os.path.join(source_dir, asset + ".zip")
        self.vDownloadQueue[asset_id]['download_file'] = dst_file + "dl"

        res = self._api.download_asset(
            asset_id, download_data, dst_file, callback=self.download_update)
        if res.ok:
            pass
        elif res.error == api.ERR_USER_CANCEL_MSG:
            reporting.capture_message(
                "user_cancelled_download", asset_id, "info")
        elif not res.ok:
            reporting.capture_message(
                "download_asset_failed", res.error, "error")
            ui_err = DisplayError(
                asset_id=asset_id,
                asset_name=asset,
                button_label="Failed, retry",
                description=f"Error during download, please try again ({res.error})"
            )
            del self.vDownloadQueue[asset_id]
            self.ui_errors.append(ui_err)
            self.vRedraw = 1
            return

        asset_dir = os.path.splitext(dst_file)[0]

        if f_Ex(asset_dir):
            asset_files = []
            for path, dirs, files in os.walk(asset_dir):
                asset_files += [os.path.join(path, file) for file in files]

            # Ensure previously found asset files are added back
            asset_files += primary_files + add_files
            asset_files = list(set(asset_files))

            self.vAssets["local"][atype][asset] = self.build_local_asset_data(
                asset, atype, asset_files)

        del self.vDownloadQueue[asset_id]

        # self.refresh_ui() does not work, set the vRedraw so handler picks up.
        self.vRedraw = 1

    def should_continue_asset_download(self, asset_id):
        """Check for any user cancel presses."""
        if asset_id in self.vDownloadCancelled:
            self.vDownloadCancelled.remove(asset_id)
            return False
        return True

    def download_update(self, asset_id, download_size):
        """Updates info for download progress bar, return false to cancel."""
        if asset_id in self.vDownloadQueue.keys():
            self.vDownloadQueue[asset_id]['download_size'] = download_size
            self.refresh_ui()
        return self.should_continue_asset_download(asset_id)

    def reset_asset_error(self, asset_id=None, asset_name=None):
        """Resets any prior errors for this asset, such as download issue."""
        for err in self.ui_errors:
            if asset_id and err.asset_id == asset_id:
                self.ui_errors.remove(err)
                self.print_debug(0, "Reset error from id", err)
            elif asset_name and err.asset_name == asset_name:
                self.ui_errors.remove(err)
                self.print_debug(0, "Reset error from name", err)

    # .........................................................................

    def f_BuildMat(self, vAsset, vSize, vTextures, vType, vOperator,
                   vLOD=None, vReuse=True):
        """Construct the material to be generated.

        Args:
            vAsset: Asset name like Metal001
            vSize: Size like 4K, HIRES, or PREVIEW
            vTextures: List of full filepaths
            vType: Asset type like Textures or Brushes
            vOperator: Passed in `self` from operator execution context.
            vLOD: The LOD textures to apply.
            vReuse: Try to reuse existing materials if found in the file.
        """
        dbg = 0
        self.print_separator(dbg, "f_BuildMat")
        self.print_debug(dbg, "f_BuildMat", vAsset, vSize, str(vTextures), vType)

        vMName = vAsset + "_" + vSize

        # Ensure we are only using textures of the input size
        sized_textures = []
        for tex in vTextures:
            match_object = re.search(r"_(\d+K)[_\.]", os.path.basename(tex))
            if match_object:
                size = match_object.group(1)
                if size == vSize:
                    sized_textures.append(tex)
            elif vSize == "PREVIEW":
                sized_textures.append(tex)

        if not sized_textures:
            msg = f"No textures found with size {vSize} for {vAsset}!"
            if vOperator:
                vOperator.report({"ERROR"}, msg)
            reporting.capture_message("build_mat_error", msg, "error")
            return None
        vTextures = sized_textures

        if vReuse and vMName in bpy.data.materials.keys():
            return bpy.data.materials[vMName]

        vCurMats = [vM for vM in bpy.data.materials]

        vMTexs = [vT for vT in vTextures if f_FName(vT).endswith("METALNESS")]
        vSTexs = [vT for vT in vTextures if f_FName(vT).endswith("SPECULAR")]
        vRTexs = [vT for vT in vTextures if vT not in vMTexs and vT not in vSTexs]
        vOTexs = [vT for vT in vTextures if "OVERLAY" in f_FName(vT)]
        vOnlyOverlay = False

        if len(vOTexs) == len(vTextures):
            # This is an overlay, not a full texture.
            vOnlyOverlay = True
        elif len(vMTexs) >= 4:
            vTextures = vMTexs + vRTexs
        elif len(vSTexs) >= 4:
            vTextures = vSTexs + vRTexs
        elif len(vRTexs) >= 4:
            vTextures = vRTexs
        elif vSize == "PREVIEW":
            pass
        else:
            msg = (
                f"Wrong tex counts for {vMName} to determine workflow - "
                f"metal:{len(vMTexs)}, "
                f"specular:{len(vSTexs)}, "
                f"dielectric:{len(vRTexs)}"
            )
            reporting.capture_message(
                "build_mat_error_workflow", msg, "error")
            return None

        # Pick the first variant
        var_names = {}
        for f in vTextures:
            basename = os.path.basename(f).upper()
            if "_VAR" not in basename:
                continue

            base, post = basename.split("_VAR")
            this_map = base.split("_")[-1]
            if not var_names.get(this_map):
                var_names[this_map] = basename
            elif var_names[this_map] > basename:
                var_names[this_map] = basename

        self.print_debug(dbg, "=" * 100)

        self.print_debug(dbg, "Building Poliigon Material : " + vAsset)
        self.print_debug(dbg, "Size : " + vSize)
        self.print_debug(dbg, "Textures :")

        vTexs = {}
        for vF in vTextures:
            basename = os.path.basename(vF)
            vSplit = f_FName(vF).split("_")
            if vSplit[-1] in ["SPECULAR", "METALNESS"]:
                vSplit[-1] = None

            if "AO" in vSplit and not self.vSettings["use_ao"]:
                continue
            if (
                any(vS for vS in ["BUMP", "BUMP16"] if vS in vSplit)
                and not self.vSettings["use_bump"]
            ):
                continue
            if (
                any(vS for vS in ["DISP", "DISP16"] if vS in vSplit)
                and not self.vSettings["use_disp"]
            ):
                continue
            if (
                any(vS for vS in ["DISP16", "BUMP16", "NRM16"] if vS in vSplit)
                and not self.vSettings["use_16"]
            ):
                continue
            if vLOD != None:
                if "LOD" in basename and vLOD not in basename:
                    continue
                if "NRM" in basename and vLOD not in basename:
                    continue

            # Detect if this is a non-preferred variant and skip if so.
            skip_var = False
            for mtype in var_names.keys():
                if mtype in vSplit:
                    if not var_names.get(mtype):
                        continue
                    elif var_names[mtype] != basename.upper():
                        skip_var = True
                        break
            if skip_var:
                continue

            vMap = [vT for vT in self.vMaps if vT in vSplit]
            if len(vMap) and vSize in vSplit + ["PREVIEW"]:
                vTexs[vMap[0]] = vF

                self.print_debug(dbg, " " + basename)

        # .....................................................................

        # vTemplate = self.gScriptDir + "/poliigon_material_template.blend"
        # if vAsset.startswith("Rock") and any(
        #     vT for vT in ["BUMP", "BUMP16"] if vT in vTexs.keys()
        # ):
        #     vTemplate = self.gScriptDir + "/poliigon_material_template_rock.blend"
        # elif any(vT for vT in ["BUMP", "BUMP16"] if vT in vTexs.keys()) and not any(
        #     vT for vT in ["DISP", "DISP16"] if vT in vTexs.keys()
        # ):
        #     vTemplate = self.gScriptDir + "/poliigon_material_template_rock.blend"
        # elif any(vS for vS in ["Carpet", "Fabric", "Rug"] if vS in vAsset):
        #     vTemplate = self.gScriptDir + "/poliigon_material_template_fabric.blend"
        # elif any(vT for vT in ["ALPHAMASKED", "MASK"] if vT in vTexs.keys()):
        #     vTemplate = self.gScriptDir + "/poliigon_material_template_alpha.blend"
        # elif "METALNESS" in vTexs.keys():
        #     vTemplate = self.gScriptDir + "/poliigon_material_template_metal.blend"

        # TODO(SOFT-369): Align on template usage long term, override for now.
        vTemplate = self.gScriptDir + "/poliigon_material_template.blend"

        vUberGroup = None
        vAdjustGroup = None
        vFabricGroup = None
        vMixerGroup = None
        for vN in list(bpy.data.node_groups):
            if "UberMapping" in vN.name:
                if "Aspect Ratio" in [vI.name for vI in vN.inputs]:
                    vUberGroup = vN
            elif "Adjustments" in vN.name:
                if "Hue Adj." in [vI.name for vI in vN.inputs]:
                    vAdjustGroup = vN
            elif "Fabric" in vN.name:
                if "Falloff" in [vI.name for vI in vN.inputs]:
                    vFabricGroup = vN
            elif "Mixer" in vN.name:
                if "Mix Texture Value" in [vI.name for vI in vN.inputs]:
                    vMixerGroup = vN

        with bpy.data.libraries.load(vTemplate, link=False) as (vFrom, vTo):
            vTo.materials = vFrom.materials

        vMat = [vM for vM in bpy.data.materials if vM not in vCurMats][0]
        vMat.name = vMName

        vMat.poliigon = vType + ";" + vAsset

        vMGroup = None
        for vN in vMat.node_tree.nodes:
            if vN.type == "BSDF_PRINCIPLED":
                if "SSS" in vTexs.keys():
                    vN.inputs["Subsurface"].default_value = 0.02

            elif vN.type == "GROUP":
                if "Color Hue Adj." in [vI.name for vI in vN.inputs]:
                    vMGroup = vN
                elif "Mix Texture Value" in [vI.name for vI in vN.inputs]:
                    if vMixerGroup != None:
                        bpy.data.node_groups.remove(vN.node_tree)
                    vMat.node_tree.nodes.remove(vN)

            elif vN.type == "DISPLACEMENT":
                if "DISP" not in vTexs.keys() and "DISP16" not in vTexs.keys():
                    vMat.node_tree.nodes.remove(vN)

        vMGroup.name = vMGroup.label = vMGroup.node_tree.name = vMName

        vOutput = None
        vMUberGroup = None
        vMAdjustGroup = None
        vMFabricGroup = None

        vMNodes = vMGroup.node_tree.nodes
        vMLinks = vMGroup.node_tree.links

        vNormalMap = None
        vBumpMap = None
        vOverlayMap = None

        vTexNodes = []
        vNTrees = [vMNodes]
        for vN in vMNodes:
            if vN.type == "GROUP_OUTPUT":
                vOutput = vN

            # Remove overlay if there isn't any.
            elif vN.name == "Overlay":
                if not any(vM in vTexs.keys() for vM in ["OVERLAY"]):
                    vMNodes.remove(vN)

            elif vN.type == "TEX_IMAGE":
                vTexNodes.append(vN)

            elif vN.type == "NORMAL_MAP":
                vNormalMap = vN

            elif vN.type == "BUMP":
                vBumpMap = vN

            # Remove Alpha Multiply Node if no Alpha maps found
            elif vN.name == "Alpha Multiply":
                if not any(vM in vTexs.keys() for vM in ["ALPHAMASKED", "MASK"]):
                    vMNodes.remove(vN)

            elif vN.type == "GROUP":
                vName = vN.name
                if "UberMapping" in vName:
                    if "Aspect Ratio" in [vI.name for vI in vN.inputs]:
                        vMUberGroup = vN
                        if vUberGroup != None:
                            vOld = vN.node_tree
                            vN.node_tree = vUberGroup
                            bpy.data.node_groups.remove(vOld)
                elif "Adjustments" in vName:
                    if "Hue Adj." in [vI.name for vI in vN.inputs]:
                        vMAdjustGroup = vN
                        if vAdjustGroup != None:
                            vOld = vN.node_tree
                            vN.node_tree = vAdjustGroup
                            bpy.data.node_groups.remove(vOld)

                    # Remove Alpha Multiply Node if no Alpha maps found
                    if "Alpha" in [vI.name for vI in vN.inputs]:
                        if not any(vM in vTexs.keys() for vM in ["ALPHAMASKED", "MASK"]):
                            vN.inputs["Alpha"].default_value = 1.0

                elif "Fabric" in vName:
                    if "Falloff" in [vI.name for vI in vN.inputs]:
                        if vAsset.startswith("Fabric"):
                            vMFabricGroup = vN
                            if vFabricGroup != None:
                                vOld = vN.node_tree
                                vN.node_tree = vFabricGroup
                                bpy.data.node_groups.remove(vOld)
                        else:
                            vMNodes.remove(vN)
                else:
                    vNNodes = vN.node_tree.nodes
                    vNTrees.append(vNNodes)
                    for vN1 in vNNodes:
                        if vN1.type == "TEX_IMAGE":
                            vTexNodes.append(vN1)

        if vBumpMap != None:
            if "BUMP" not in vTexs.keys() and "BUMP16" not in vTexs.keys():
                vMNodes.remove(vBumpMap)

                if vNormalMap != None:
                    vMLinks.new(
                        vNormalMap.outputs["Normal"], vMAdjustGroup.inputs["Normal"]
                    )

            else:
                vMLinks.new(vBumpMap.outputs["Normal"], vMAdjustGroup.inputs["Normal"])

        for vN in vTexNodes:
            vMap = vN.name
            if vMap == "ALPHA":
                if "MASK" in vTexs.keys():
                    vMap = "MASK"

                    vMat.blend_method = "HASHED"
                    vMat.shadow_method = "CLIP"

            elif vMap == "COLOR":
                if "ALPHAMASKED" in vTexs.keys():
                    vMap = "ALPHAMASKED"

                    vMat.blend_method = "HASHED"
                    vMat.shadow_method = "CLIP"
                else:
                    vMap = "COL"

            elif vMap == "BUMP":
                vMap = "BUMP"
                if "BUMP16" in vTexs.keys():
                    vMap = "BUMP16"

            elif vMap == "DISPLACEMENT":
                vMap = "DISP"
                if "DISP16" in vTexs.keys():
                    vMap = "DISP16"

            elif vMap == "NORMAL":
                vMap = "NRM"
                if "NRM16" in vTexs.keys():
                    vMap = "NRM16"

            elif vMap == "OVERLAY":
                vMap = "OVERLAY"

            if vMap in vTexs.keys():
                if vMap == "ROUGHNESS":
                    vMLinks.new(
                        vN.outputs["Color"], vMAdjustGroup.inputs["ROUGHNESS"])

                if vOnlyOverlay and vMap == "OVERLAY":
                    # If only overlay textures exist, plug the overlay texture
                    # into the output as a sort of preview.
                    vMLinks.new(
                        vN.outputs["Color"], vMAdjustGroup.inputs["COLOR"])

                if vMap in ["DISP", "DISP16"]:
                    if self.prefs.use_micro_displacements:
                        vMGroup.inputs["Displacement Strength"].default_value = 0.05
                        if "NRM" or "NRM16" in vTexs.keys():
                            # Micro displacement does not work with normal and
                            # displacement maps at the same time, so disable
                            # normal (if displacement used).
                            vMGroup.inputs["Normal Strength"].default_value = 0
                            if vOperator is not None:
                                vOperator.report(
                                    {"INFO"},
                                    "Disabling normals due to use of micro displacements."
                                )
                    else:
                        vMGroup.inputs["Displacement Strength"].default_value = 0.0

                engine = bpy.context.scene.render.engine
                if engine == "BLENDER_EEVEE" and vMap == "TRANSMISSION":
                    vMat.use_screen_refraction = True
                    vMat.refraction_depth = 1

                vTName = f_FName(vTexs[vMap])
                if vTName in bpy.data.images.keys():
                    vImage = bpy.data.images[vTName]
                else:
                    vImage = bpy.data.images.load(vTexs[vMap])
                    vImage.name = vTName

                vN.image = vImage
                if vMap in [
                    "AO",
                    "BUMP",
                    "BUMP16",
                    "DISP",
                    "DISP16",
                    "GLOSS",
                    "MASK",
                    "METALNESS",
                    "ROUGHNESS",
                    "NRM",
                    "NRM16",
                    "TRANSMISSION",
                    "OVERLAY"
                ]:
                    if hasattr(vN, "color_space"):
                        vN.color_space = "NONE"
                    elif vN.image and hasattr(vN.image, "colorspace_settings"):
                        vN.image.colorspace_settings.name = "Non-Color"

            else:
                for vNT in vNTrees:
                    try:
                        vNT.remove(vN)
                    except:
                        pass

        if vMFabricGroup is not None:
            vMLinks.new(vMAdjustGroup.outputs["Base Color"],
                        vMFabricGroup.inputs["Base Color"])
            vMLinks.new(vMAdjustGroup.outputs["Roughness"],
                        vMFabricGroup.inputs["Roughness"])
            vMLinks.new(vMAdjustGroup.outputs["Normal"],
                        vMFabricGroup.inputs["Normal"])
            vMLinks.new(vMFabricGroup.outputs["Base Color"],
                        vOutput.inputs["Base Color"])
            vMLinks.new(vMFabricGroup.outputs["Roughness"],
                        vOutput.inputs["Roughness"])

        if vOperator is not None:
            vOperator.report(
                {"INFO"}, f"Material Created : {vAsset}_{vSize}")

        cTB.print_debug(0, "=" * 100)

        return vMat

    def f_BuildBackplate(self, vAsset, vName, vFile):
        """Create the backplate mateiral and apply to existing or a new obj."""
        dbg = 0
        self.print_separator(dbg, "f_BuildBackplate")

        if vName in bpy.data.materials:
            vMat = bpy.data.materials[vName]

            vImage = bpy.data.images[vName]

        else:
            # TODO: Move material definition into a material handler.
            bpy.data.materials.new(vName)

            vMat = bpy.data.materials[vName]

            vMat.use_nodes = 1

            vMNodes = vMat.node_tree.nodes
            vMLinks = vMat.node_tree.links

            vMNodes.remove(vMNodes["Principled BSDF"])

            vCoords = vMNodes.new(type="ShaderNodeTexCoord")
            vCoords.location = mathutils.Vector((-650, 360))

            vTex = vMNodes.new("ShaderNodeTexImage")
            vTex.name = "DIFF"
            vTex.label = "DIFF"
            vTex.location = mathutils.Vector((-450, 360))

            vBG = vMNodes.new("ShaderNodeBackground")
            vBG.location = mathutils.Vector((-145, 225))
            vBG.inputs[1].default_value = 2

            vMix = vMNodes.new("ShaderNodeMixShader")
            vMix.location = mathutils.Vector((60, 300))

            vLight = vMNodes.new("ShaderNodeLightPath")
            vLight.location = mathutils.Vector((-145, 570))

            if vName in bpy.data.images:
                vImage = bpy.data.images[vName]
            else:
                vImage = bpy.data.images.load(vFile)
                vImage.name = vName
            vTex.image = vImage

            vMLinks.new(vCoords.outputs["UV"], vTex.inputs["Vector"])
            vMLinks.new(vTex.outputs["Color"], vBG.inputs["Color"])
            vMLinks.new(vBG.outputs[0], vMix.inputs[2])
            vMLinks.new(vLight.outputs[0], vMix.inputs[0])
            vMLinks.new(vMix.outputs[0], vMNodes["Material Output"].inputs[0])

        vMat.poliigon = "Textures;" + vAsset

        if bpy.context.selected_objects:
            # If there are objects selected, apply backplate to those
            vObjs = list(bpy.context.selected_objects)

        else:
            # Otherwise, create a new object.
            prior_objs = [vO for vO in bpy.data.objects]

            bpy.ops.mesh.primitive_plane_add(
                size=1.0, enter_editmode=False,
                location=bpy.context.scene.cursor.location, rotation=(0, 0, 0)
            )

            vObj = [vO for vO in bpy.data.objects if vO not in prior_objs][0]
            vObjs = [vObj]  # For assignment of material later.
            vObj.name = vName

            vObj.rotation_euler = mathutils.Euler((radians(90.0), 0.0, 0.0), "XYZ")

            vRatio = vImage.size[0] / vImage.size[1]

            vH = 5.0
            if bpy.context.scene.unit_settings.length_unit == "KILOMETERS":
                vH = 5.0 / 1000
            elif bpy.context.scene.unit_settings.length_unit == "CENTIMETERS":
                vH = 5.0 * 100
            elif bpy.context.scene.unit_settings.length_unit == "MILLIMETERS":
                vH = 5.0 * 1000
            elif bpy.context.scene.unit_settings.length_unit == "MILES":
                vH = 16.0 / 5280
            elif bpy.context.scene.unit_settings.length_unit == "FEET":
                vH = 16.0
            elif bpy.context.scene.unit_settings.length_unit == "INCHES":
                vH = 16.0 * 12

            vW = vH * vRatio

            vObj.dimensions = mathutils.Vector((vW, vH, 0))

            vObj.delta_scale[0] = 1
            vObj.delta_scale[1] = 1
            vObj.delta_scale[2] = 1

            bpy.ops.object.select_all(action="DESELECT")
            try:
                vObj.select_set(True)
            except:
                vObj.select = True

            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        for obj in vObjs:
            obj.active_material = vMat

    # .........................................................................

    def f_GetLocalAssets(self, force=0):
        dbg = 0
        self.print_separator(dbg, "f_GetLocalAssets")

        # This function was taking 3.5s to run at startup, so thrown it into a thread

        if not force and (time.time() - self.vGotLocalAssets) < 60 * 5:
            return

        if not self.vGettingLocalAssets:
            self.vGettingLocalAssets = 1

            vThread = threading.Thread(target=self.f_GetLocalAssetsThread)
            vThread.daemon = 1
            vThread.start()
            self.vThreads.append(vThread)
        else:
            self.print_debug(1, "Flagging to check local assets again.")
            self.vRerunGetLocalAssets = True

    @reporting.handle_function(silent=True)
    def f_GetLocalAssetsThread(self):
        dbg = 0
        self.print_separator(dbg, "f_GetLocalAssetsThread")

        for vType in self.vAssetTypes:
            self.vAssets["local"][vType] = {}

        vGetAssets = {}
        vModels = []
        vHDRIs = []
        vBrushes = []

        vPrevs = {}
        gLatest = {}
        for vDir in [self.vSettings["library"]] + self.vSettings["add_dirs"]:
            if vDir in self.vSettings["disabled_dirs"]:
                continue

            for vPath, vDirs, vFiles in os.walk(vDir):
                vPath = vPath.replace("\\", "/")

                if "Software" in vPath and not "Blender" in vPath:
                    continue

                for vF in vFiles:
                    if vF.startswith("."):
                        continue  # Ignore hidden system files like .DS_Store
                    if f_FExt(vF) in ["", ".zip"]:
                        continue

                    vName, vExt = f_FNameExt(vF)
                    vName = vName.split("_")[0]

                    if vName.startswith("Hdr"):
                        vHDRIs.append(vName)

                    elif vName.startswith("Brush"):
                        vBrushes.append(vName)

                    if any(
                        f_FName(vF).lower().endswith(vS)
                        for vS in [
                            "_atlas",
                            "_sphere",
                            "_cylinder",
                            "_fabric",
                            "_preview1",
                        ]
                    ):
                        if vName not in vGetAssets.keys():
                            vGetAssets[vName] = []

                        vGetAssets[vName].append(vPath + "/" + vF)

                        vFTime = os.path.getctime(vPath + "/" + vF)
                        vFDate = int(
                            (
                                str(datetime.datetime.fromtimestamp(vFTime)).split(" ")[
                                    0
                                ]
                            ).replace("-", "")
                        )

                        if vName not in gLatest.keys():
                            gLatest[vName] = vFTime
                        elif gLatest[vName] < vFTime:
                            gLatest[vName] = vFTime

                    elif vExt.lower() in self.vTexExts:
                        if any(vM in vF for vM in self.vMaps):
                            if vName not in vGetAssets.keys():
                                vGetAssets[vName] = []

                            vGetAssets[vName].append(vPath + "/" + vF)

                    elif vExt.lower() in self.vModExts:
                        if vName not in vGetAssets.keys():
                            vGetAssets[vName] = []

                        vGetAssets[vName].append(vPath + "/" + vF)

                        vGetAssets[vName] += [
                            vPath + "/" + vFl
                            for vFl in vFiles
                            if f_FExt(vFl) in self.vTexExts
                        ]

                        if vName not in vModels:
                            vModels.append(vName)

        for vA in sorted(list(vGetAssets.keys())):
            if any(vS in vA for vS in self.vModSecondaries):
                vPrnt = vA
                for vS in self.vModSecondaries:
                    vPrnt = vPrnt.replace(vS, "")

                if vPrnt in list(vGetAssets.keys()):
                    vGetAssets[vPrnt] += vGetAssets[vA]

                    del vGetAssets[vA]

        for vA in sorted(list(vGetAssets.keys())):
            vType = "Textures"
            if vA in vModels:
                vType = "Models"
            elif vA in vHDRIs:
                vType = "HDRIs"
            elif vA in vBrushes:
                vType = "Brushes"

            if vType not in self.vAssets["local"].keys():
                self.vAssets["local"][vType] = {}

            # updating the global asset dict here for better UI responsiveness
            self.vAssets["local"][vType][vA] = self.build_local_asset_data(vA, vType, vGetAssets[vA])

        vSLatest = {}
        for vK in gLatest.keys():
            vSLatest[gLatest[vK]] = vK

        gLatest = [vSLatest[vK] for vK in reversed(sorted(vSLatest.keys()))]

        # Need to tag redraw, can't directlly call refresh_ui since
        # this runs on startup.
        self.vRedraw = 1

        self.vGettingLocalAssets = 0

        self.vGotLocalAssets = time.time()
        if self.vRerunGetLocalAssets:
            self.vRerunGetLocalAssets = False
            self.f_GetLocalAssets()

    def build_local_asset_data(self, asset, type, files):
        """Builds data dict for asset"""
        files = sorted(list(set(files)))

        maps = []
        lods = []
        sizes = []
        vars = []
        preview = None
        for file in files:
            if any(
                f_FName(file).lower().endswith(string)
                for string in [
                    "_atlas",
                    "_sphere",
                    "_cylinder",
                    "_fabric",
                    "_preview1",
                ]
            ):
                preview = file
            else:
                maps += [map for map in self.vMaps if map in f_FName(file).split("_")]
                lods += [lod for lod in self.vLODs if lod in f_FName(file).split("_") and f_FExt(file) == '.fbx']
                sizes += [size for size in self.vSizes if size in f_FName(file).split("_")]
                vars += [var for var in self.vVars if var in f_FName(file).split("_")]

        asset_data = {}
        asset_data["name"] = asset
        # asset_data["id"] = 0  # Don't populate id, it's not available here.
        asset_data["type"] = type
        asset_data["files"] = files
        asset_data["maps"] = sorted(list(set(maps)))
        asset_data["lods"] = [lod for lod in self.vLODs if lod in lods]  #sort
        asset_data["sizes"] = [size for size in self.vSizes if size in sizes]  #sort
        asset_data["vars"] = sorted(list(set(vars)))
        asset_data["date"] = max(os.path.getctime(file) for file in files)
        asset_data["credits"] = None
        asset_data["preview"] = preview
        asset_data["thumbnails"] = [preview]
        asset_data["quick_preview"] = []

        return asset_data

    def f_GetSceneAssets(self):
        dbg = 0
        self.print_separator(dbg, "f_GetSceneAssets")

        vImportedAssets = {}
        for vType in self.vAssetTypes:
            vImportedAssets[vType] = {}

        for vM in bpy.data.materials:
            try:
                vType, vAsset = vM.poliigon.split(";")
                vAsset = vAsset.split("_")[0]
                if vType == "Textures" and vAsset != "":
                    self.print_debug(dbg, "f_GetSceneAssets", vAsset)

                    if vAsset not in vImportedAssets["Textures"].keys():
                        vImportedAssets["Textures"][vAsset] = []

                    if vM not in vImportedAssets["Textures"][vAsset]:
                        vImportedAssets["Textures"][vAsset].append(vM)
            except:
                pass

        for vO in bpy.data.objects:
            try:
                vType, vAsset = vO.poliigon.split(";")
                vAsset = vAsset.split("_")[0]
                if vType == "Models" and vAsset != "":
                    self.print_debug(dbg, "f_GetSceneAssets", vAsset)

                    if vAsset not in vImportedAssets["Models"].keys():
                        vImportedAssets["Models"][vAsset] = []

                    if vO not in vImportedAssets["Models"][vAsset]:
                        vImportedAssets["Models"][vAsset].append(vO)
            except:
                pass

        for vI in bpy.data.images:
            try:
                vType, vAsset = vI.poliigon.split(";")
                vAsset = vAsset.split("_")[0]
                if vType in ["HDRIs", "Brushes"] and vAsset != "":
                    self.print_debug(dbg, "f_GetSceneAssets", vAsset)

                    if vAsset not in vImportedAssets[vType].keys():
                        vImportedAssets[vType][vAsset] = []

                    vImportedAssets[vType][vAsset].append(vI)
            except:
                pass

        self.vAssets["imported"] = vImportedAssets

    def f_GetActiveData(self):
        dbg = 0
        self.print_separator(dbg, "f_GetActiveData")

        self.vActiveMatProps = {}
        self.vActiveTextures = {}
        self.vActiveMixProps = {}

        if self.vActiveMat == None:
            return

        vMat = bpy.data.materials[self.vActiveMat]

        if self.vActiveMode == "mixer":
            vMNodes = vMat.node_tree.nodes
            vMLinks = vMat.node_tree.links
            for vN in vMNodes:
                if vN.type == "GROUP":
                    if "Mix Texture Value" in [vI.name for vI in vN.inputs]:
                        vMat1 = None
                        vMat2 = None
                        vMixTex = None
                        for vL in vMLinks:
                            if vL.to_node == vN:
                                if vL.to_socket.name in ["Base Color1", "Base Color2"]:
                                    vProps = {}
                                    for vI in vL.from_node.inputs:
                                        if vI.is_linked:
                                            continue
                                        if vI.type == "VALUE":
                                            vProps[vI.name] = vL.from_node

                                    if vL.to_socket.name == "Base Color1":
                                        vMat1 = [vL.from_node, vProps]
                                    elif vL.to_socket.name == "Base Color2":
                                        vMat2 = [vL.from_node, vProps]
                                elif vL.to_socket.name == "Mix Texture":
                                    if vN.inputs["Mix Texture"].is_linked:
                                        vMixTex = vL.from_node

                        vProps = {}
                        for vI in vN.inputs:
                            if vI.is_linked:
                                continue
                            if vI.type == "VALUE":
                                vProps[vI.name] = vN

                        self.vActiveMixProps[vN.name] = [
                            vN,
                            vMat1,
                            vMat2,
                            vProps,
                            vMixTex,
                        ]

            if self.vSettings["mix_props"] == []:
                vK = list(self.vActiveMatProps.keys())[0]
                self.vSettings["mix_props"] = list(self.vActiveMatProps[vK][3].keys())
        else:
            vMNodes = vMat.node_tree.nodes
            for vN in vMNodes:
                if vN.type == "GROUP":
                    for vI in vN.inputs:
                        if vI.type == "VALUE":
                            self.vActiveMatProps[vI.name] = vN
                elif vN.type == "BUMP" and vN.name == "Bump":
                    for vI in vN.inputs:
                        if vI.type == "VALUE" and vI.name == "Strength":
                            self.vActiveMatProps[vI.name] = vN

            if self.vSettings["mat_props"] == []:
                self.vSettings["mat_props"] = list(self.vActiveMatProps.keys())

            if vMat.use_nodes:
                for vN in vMat.node_tree.nodes:
                    if vN.type == "TEX_IMAGE":
                        if vN.image == None:
                            continue
                        vFile = vN.image.filepath.replace("\\", "/")
                        if f_Ex(vFile):
                            # pType = [vT for vT in vTypes if vT in f_FName(vFile).split('_')]
                            vType = vN.name
                            if vType == "COLOR":
                                vType = "COL"
                            elif vType == "DISPLACEMENT":
                                vType = "DISP"
                            elif vType == "NORMAL":
                                vType = "NRM"
                            elif vType == "OVERLAY":
                                vType = "OVERLAY"

                            self.vActiveTextures[vType] = vN

                    elif vN.type == "GROUP":
                        for vN1 in vN.node_tree.nodes:
                            if vN1.type == "TEX_IMAGE":
                                if vN1.image == None:
                                    continue
                                vFile = vN1.image.filepath.replace("\\", "/")
                                if f_Ex(vFile):
                                    # pType = [vT for vT in vTypes if vT in f_FName(vFile).split('_')]
                                    vType = vN1.name
                                    if vType == "COLOR":
                                        vType = "COL"
                                    if vType == "OVERLAY":
                                        vType = "OVERLAY"
                                    elif vType == "DISPLACEMENT":
                                        vType = "DISP"
                                    elif vType == "NORMAL":
                                        vType = "NRM"
                                    self.vActiveTextures[vType] = vN1
                            elif vN1.type == "BUMP" and vN1.name == "Bump":
                                for vI in vN1.inputs:
                                    if vI.type == "VALUE" and vI.name == "Distance":
                                        self.vActiveMatProps[vI.name] = vN1

    def f_GetSelected(self):
        dbg = 0
        self.print_separator(dbg, "f_GetSelected")

        vAObjects = []
        vAMats = []
        vAFaces = {}
        vAAsset = None
        vAMat = None

        if len(bpy.context.selected_objects):
            for vO in bpy.context.selected_objects:
                vMats = [vM.material for vM in vO.material_slots]
                if any(vM for vM in vMats if vM in self.vAllMats):
                    if vAMat in [vM.name for vM in vMats if vM != None]:
                        for vA in self.vAssets["imported"]["Textures"].keys():
                            if vAMat in [
                                vSM.name for vSM in self.vAssets["imported"]["Textures"][vA]
                            ]:
                                vAObjects.append(vO)
                                vAAsset = vA
                                vAMats = vMats
                                self.f_GetActiveData()
                                break
                    else:
                        vAAsset = None
                        for vMat in vMats:
                            if vMat == None:
                                continue
                            if vAAsset != None:
                                break
                            for vA in self.vAssets["imported"]["Textures"].keys():
                                if vMat in self.vAssets["imported"]["Textures"][vA]:
                                    if vAAsset != None:
                                        break
                                    vAObjects.append(vO)
                                    vAAsset = vA
                                    vAMat = vMat.name
                                    vAMats = vMats
                                    self.f_GetActiveData()
                                    break
        else:
            for vO in bpy.context.scene.objects:
                if not vO.mode == "EDIT":
                    continue

                vMats = [vM.material for vM in vO.material_slots]
                if any(vM for vM in vMats if vM in self.vAllMats):
                    if vAMat in [vM.name for vM in vMats if vM != None]:
                        for vA in self.vAssets["imported"]["Textures"].keys():
                            if vAMat in [
                                vSM.name for vSM in self.vAssets["imported"]["Textures"][vA]
                            ]:
                                vAObjects.append(vO)
                                vAAsset = vA
                                vAMats = vMats
                                self.f_GetActiveData()
                                break
                    else:
                        vAAsset = None
                        for vMat in vMats:
                            if vMat == None:
                                continue
                            if vAAsset != None:
                                break
                            for vA in self.vAssets["imported"]["Textures"].keys():
                                if vMat in self.vAssets["imported"]["Textures"][vA]:
                                    if vAAsset != None:
                                        break
                                    vAObjects.append(vO)
                                    vAAsset = vA
                                    vAMat = vMat.name
                                    vAMats = vMats
                                    self.f_GetActiveData()
                                    break

        if len(vAObjects):
            vAFaces = {}
            for vO in vAObjects:
                vAFaces[vO.name] = []
                if vO.mode == "EDIT":
                    vMesh = vO.data
                    vBMesh = bmesh.from_edit_mesh(vMesh)
                    for vF in vBMesh.faces:
                        if vF.select:
                            vAFaces[vO.name].append(vF.index)

        self.vActiveMats = vAMats
        self.vActiveFaces = vAFaces

        if self.vActiveObjects != vAObjects:
            self.vActiveObjects = vAObjects
            self.vActiveMode = "model"
            self.vActiveAsset = vAAsset
            self.vActiveMat = vAMat

    def f_CheckAssets(self):
        dbg = 0
        self.print_separator(dbg, "f_CheckAssets")

        if time.time() - self.vTimer < 5:
            return
        self.vTimer = time.time()

        vAssetNames = []
        for vType in self.vAssets["my_assets"].keys():
            vAssetNames += self.vAssets["my_assets"][vType]

        self.print_debug(dbg, "f_CheckAssets", "New Assets :")

        vZips = []
        self.vNewAssets = []
        for vDir in [self.vSettings["library"]] + self.vSettings["add_dirs"]:
            for vPath, vDirs, vFiles in os.walk(vDir):
                vPath = vPath.replace("\\", "/")
                for vF in vFiles:
                    if vF.endswith(".zip"):
                        if vPath + vF not in vZips:
                            vZips.append(vPath + vF)

                    elif "COL" in vF or vF.startswith("Back"):
                        vName = f_FName(vF).split("_")
                        if vName[-1] == "SPECULAR":
                            continue
                        if vName[0] not in vAssetNames:
                            self.vNewAssets.append(vName[0])

                            # if vDBG : print(vDBGi,"-",vName[0])

        if len(vZips) and self.vSettings["unzip"]:
            self.print_debug(dbg, "f_CheckAssets", "Zips :")

            for vZFile in vZips:
                vName = f_FName(vZFile).split("_")[0]
                self.print_debug(dbg, "f_CheckAssets", "-", vName, " from ", vZFile)

                gLatest = 0
                for vType in self.vAssets["local"].keys():
                    if vName in self.vAssets["local"][vType].keys():
                        for vF in self.vAssets["local"][vType][vName]["files"]:
                            try:
                                vFDate = datetime.datetime.fromtimestamp(
                                    os.path.getctime(vF)
                                )
                                vFDate = str(vFDate).split(" ")[0].replace("-", "")
                                vFDate = int(vFDate)
                                if vFDate > gLatest:
                                    gLatest = vFDate
                            except:
                                pass

                        vZDate = int(
                            (
                                str(
                                    datetime.datetime.fromtimestamp(
                                        os.path.getctime(vF)
                                    )
                                ).split(" ")[0]
                            ).replace("-", "")
                        )
                        if vZDate < vFDate:
                            continue

        self.f_GetLocalAssets()

    # .........................................................................

    def f_Label(self, vWidth, vText, vContainer, vIcon=None, vAddPadding=False):
        """Text wrap a label based on indicated width."""
        # TODO: Move this to UI class ideally.
        dbg = 0
        self.print_separator(dbg, "f_Label")

        vWords = [vW.replace("!@#", " ") for vW in vText.split(" ")]
        vContainerRow = vContainer.row()
        vParent = vContainerRow.column(align=True)
        vParent.scale_y = 0.8  # To make vertical height more natural for text.
        if vAddPadding:
            vParent.label(text="")

        if vIcon:
            vWidth -= 25 * self.get_ui_scale()

        vLine = ""
        vFirst = True
        for vW in vWords:
            vLW = 15
            vLineN = vLine + vW + " "
            for vC in vLineN:
                if vC in "ABCDEFGHKLMNOPQRSTUVWXYZmw":
                    vLW += 9
                elif vC in "abcdeghknopqrstuvxyz0123456789":
                    vLW += 6
                elif vC in "IJfijl .":
                    vLW += 3

            vLW *= self.get_ui_scale()

            if vLW > vWidth:
                if vFirst:
                    if vIcon == None:
                        vParent.label(text=vLine)
                    else:
                        vParent.label(text=vLine, icon=vIcon)
                    vFirst = False

                else:
                    if vIcon == None:
                        vParent.label(text=vLine)
                    else:
                        vParent.label(text=vLine, icon="BLANK1")

                vLine = vW + " "

            else:
                vLine += vW + " "

        if vLine != "":
            if vIcon == None:
                vParent.label(text=vLine)
            else:
                if vFirst:
                    vParent.label(text=vLine, icon=vIcon)
                else:
                    vParent.label(text=vLine, icon="BLANK1")        
        if vAddPadding:
            vParent.label(text="")

    # .........................................................................

    def f_GetThumbnailPath(self, asset, index):
        """Return the best fitting thumbnail preview for an asset.

        The primary grid UI preview will be named asset_preview1.png,
        all others will be named such as asset_preview1_1K.png
        """
        if index == 0:
            # 0 is the small grid preview version of _preview1.

            # Support legacy option of loading .jpg files, check that first.
            thumb = os.path.join(self.gOnlinePreviews, asset + "_preview1.jpg")
            if not os.path.exists(thumb):
                thumb = os.path.join(
                    self.gOnlinePreviews, asset + "_preview1.png")
        else:
            thumb = os.path.join(
                self.gOnlinePreviews,
                asset + f"_preview{index}_1K.png")
        return thumb

    def f_GetPreview(self, vAsset, index=0):
        """Queue download for a preview if not already local.

        Use a non-zero index to fetch another preview type thumbnail.
        """
        dbg = 0
        self.print_separator(dbg, "f_GetPreview")

        if vAsset == "dummy":
            return

        if vAsset in self.vPreviews:
            return self.vPreviews[vAsset].icon_id

        f_MDir(self.gOnlinePreviews)

        vPrev = self.f_GetThumbnailPath(vAsset, index)

        if os.path.exists(vPrev):
            try:
                self.vPreviews.load(vAsset, vPrev, "IMAGE")
                self.vPreviews[vAsset].reload()
            except KeyError:
                pass  # Already exists.

            self.print_debug(dbg, "f_GetPreview", vPrev)

            return self.vPreviews[vAsset].icon_id

        if vAsset not in self.vPreviewsDownloading:
            self.vPreviewsDownloading.append(vAsset)
            self.f_QueuePreview(vAsset, index)

        return None

    def f_GetClosestSize(self, vSizes, vSize):
        if vSize not in vSizes:
            x = self.vSizes.index(vSize)
            for i in range(len(self.vSizes)):
                if x - i >= 0:
                    if self.vSizes[x - i] in vSizes:
                        vSize = self.vSizes[x - i]
                        break
                if x + i < len(self.vSizes):
                    if self.vSizes[x + i] in vSizes:
                        vSize = self.vSizes[x + i]
                        break

        return vSize

    def f_GetSize(self, vName):
        for vSz in self.vSizes:
            if vSz in vName.split('_'):
                return vSz

        return None

    def f_GetClosestLod(self, vLods, vLod):
        if vLod not in vLods:
            x = self.vLODs.index(vLod)
            for i in range(len(self.vLODs)):
                if x - i >= 0:
                    if self.vSizes[x - i] in vLods:
                        vLod = self.vLODs[x - i]
                        break
                if x + i < len(self.vLODs):
                    if self.vLODs[x + i] in vLods:
                        vLod = self.vLODs[x + i]
                        break

        return vLod

    def f_GetLod(self, vName):
        for vL in self.vLODs:
            if vL in vName:
                return vL
        return None

    def f_GetVar(self, vName):
        vVar = None
        for vV in self.vVars:
            if vV in vName:
                return vV
        return vVar

    # .........................................................................

    def check_icon_reload_interval(self):
        """Checks if too little time has elapsed since last page change.

        If user cycles through pages too quickly, icons can fail to load even
        if already downloaded. This is a blender limitation.
        """
        now = time.time()
        if now - self.vLastPageChange < self.vReloadTriggerInterval:
            bpy.app.timers.register(f_icon_refresh_interval,
                                    first_interval=self.vReloadTriggerInterval)
        self.vLastPageChange = now

    # .........................................................................
    def get_verbose(self):
        """User preferences call wrapper, separate to support test mocking."""
        prefs = bpy.context.preferences.addons.get(__package__, None)
        # Fallback, if command line and using the standard install name.
        if not prefs:
            addons = bpy.context.preferences.addons
            prefs = addons.get("poliigon-addon-blender", None)

        if prefs and prefs.preferences:
            return prefs.preferences.verbose_logs
        else:
            return None

    def get_prefs(self):
        """User preferences call wrapper, separate to support test mocking."""
        prefs = bpy.context.preferences.addons.get(__package__, None)
        # Fallback, if command line and using the standard install name.
        if not prefs:
            addons = bpy.context.preferences.addons
            prefs = addons.get("poliigon-addon-blender", None)
        if prefs:
            return prefs.preferences
        else:
            return None

    @reporting.handle_function(silent=True, transact=False)
    def print_separator(self, dbg, logvalue):
        """Print out a separator log line with a string value logvalue.

        Cache based on args up to a limit, to avoid excessive repeat prints.
        All args must be flat values, such as already casted to strings, else
        an error will be thrown.
        """
        if self.get_verbose() or dbg:
            self._cached_print("-" * 50 + "\n" + str(logvalue))

    @reporting.handle_function(silent=True, transact=False)
    def print_debug(self, dbg, *args):
        """Print out a debug statement with no separator line.

        Cache based on args up to a limit, to avoid excessive repeat prints.
        All args must be flat values, such as already casted to strings, else
        an error will be thrown.
        """
        if self.get_verbose() or (dbg and dbg > 0):
            # Ensure all inputs are hashable, otherwise lru_cache fails.
            stringified = [str(arg) for arg in args]
            self._cached_print(*stringified)

    @lru_cache(maxsize=32)
    def _cached_print(self, *args):
        """A safe-to-cache function for printing."""
        print(*args)

    def update_files(self, path):
        """Updates files in the specified path within the addon."""
        dbg = 0
        update_key = "_update"
        files_to_update = [f for f in os.listdir(path)
                           if os.path.isfile(os.path.join(path, f))
                           and os.path.splitext(f)[0].endswith(update_key)]

        for f in files_to_update:
            f_split = os.path.splitext(f)
            tgt_file = f_split[0][:-len(update_key)] + f_split[1]

            try:
                os.replace(os.path.join(path, f), os.path.join(path, tgt_file))
                self.print_debug(dbg, f"Updated {tgt_file}")
            except PermissionError as e:
                reporting.capture_message("file_permission_error", e, "error")
            except OSError as e:
                reporting.capture_message("os_error", e, "error")

        return len(files_to_update) > 0

    def check_update_callback(self):
        """Callback run by the updater instance."""
        # Hack to force it to think update is available
        fake_update = False
        if fake_update:
            self.updater.update_ready = True
            self.updater.update_data = updater.VersionData(
                version=(1, 0, 0),
                url="https://github.com/poliigon/poliigon-blender-toolbox/")

        # Build notifications and refresh UI.
        if self.updater.update_ready:
            notice = build_update_notification()
            self.register_notification(notice)
        self.refresh_ui()

    def update_api_status_banners(self, status_name):
        """Updates notifications according the to the form of the API event.

        This is called by API's event_listener when API events occur.
        """
        reset_ids = [
            "PROXY_CONNECTION_ERROR",
            "NO_INTERNET_CONNECTION"
        ]
        if status_name == api.ApiStatus.CONNECTION_OK:
            for existing in self.notifications:
                if existing.notification_id in reset_ids:
                    self.notifications.remove(existing)

        elif status_name == api.ApiStatus.NO_INTERNET:
            notice = build_no_internet_notification()
            self.register_notification(notice)

        elif status_name == api.ApiStatus.PROXY_ERROR:
            notice = build_proxy_notification()
            self.register_notification(notice)


# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


def f_icon_refresh_interval() -> int:
    """Force refresh all icons if no new requests have occurred."""
    now = time.time()
    if now - cTB.vLastPageChange < cTB.vReloadTriggerInterval:
        return  # Don't trigger, another page change has occurred.
    cTB.refresh_data(icons_only=True)


def f_tick_handler() -> int:
    """Called on by blender timer handlers to check toolbox status.

    The returned value signifies how long until the next execution.
    """
    next_call_s = 60  # Long to prevent frequent checks for updates.
    if cTB.vRunning:  # and not self.vExit
        cTB.vExit = 0

        # TODO: Move into an async function
        try:
            # Disabled to improve performance
            #self.f_CheckAssets()
            pass
        except Exception:
            err = traceback.format_exc()
            print("Check assets encountered an error:")
            print(err)

        # Thread cleanup.
        for vT in list(cTB.vThreads):
            if not vT.is_alive():
                cTB.vThreads.remove(vT)

        # Updater callback.
        if cTB.prefs and cTB.prefs.auto_check_update:
            if cTB.updater.has_time_elapsed(hours=24):
                cTB.updater.async_check_for_update(cTB.check_update_callback)

    return next_call_s


def f_download_handler() -> int:
    """Called on by blender timer handlers to redraw the UI while downloading.

    The returned value signifies how long until the next execution.
    """
    next_call_s = 1
    combined_keys = list(cTB.vDownloadQueue.keys()) + list(cTB.vQuickPreviewQueue.keys())
    if len(combined_keys) or cTB.vRedraw:
        cTB.vRedraw = 0
        next_call_s = 0.1
        cTB.refresh_ui()

        # Automatic import after download
        imports = [
            asset for asset in list(cTB.vDownloadQueue.keys())
            if 'import' in cTB.vDownloadQueue[asset].keys()]
        if len(imports):
            asset = imports[0]
            asset_data = cTB.vDownloadQueue[asset]
            del(cTB.vDownloadQueue[asset])
            if asset_data['data']['type'] == 'Textures':
                bpy.ops.poliigon.poliigon_material(
                    "INVOKE_DEFAULT", vAsset=asset, vSize=asset_data['size'],
                    vData='@_@_', vType=asset_data['data']['type'], vApply=0)
            elif asset_data['data']['type'] == 'HDRIs':
                bpy.ops.poliigon.poliigon_hdri(
                    "INVOKE_DEFAULT", vAsset=asset, vSize=asset_data['size'])

    return next_call_s


@persistent
def f_load_handler(*args):
    """Runs when a new file is opened to refresh data"""
    if cTB.vRunning:
        cTB.f_GetSceneAssets()


# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


cTB = c_Toolbox()


@atexit.register
def blender_quitting():
    global cTB
    cTB.vRunning = 0


def register(bl_info):
    addon_version = ".".join([str(vV) for vV in bl_info["version"]])
    cTB.register(addon_version)

    cTB.vRunning = 1

    bpy.app.timers.register(
        f_tick_handler, first_interval=0.05, persistent=True)

    bpy.app.timers.register(
        f_download_handler, first_interval=1, persistent=True)

    if f_load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(f_load_handler)


def unregister():
    if bpy.app.timers.is_registered(f_tick_handler):
        bpy.app.timers.unregister(f_tick_handler)

    if bpy.app.timers.is_registered(f_download_handler):
        bpy.app.timers.unregister(f_download_handler)

    if f_load_handler in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(f_load_handler)

    cTB.vRunning = 0

    # Don't block unregister or closing blender.
    # for vT in cTB.vThreads:
    #    vT.join()

    cTB.vIcons.clear()
    bpy.utils.previews.remove(cTB.vIcons)

    cTB.vPreviews.clear()
    bpy.utils.previews.remove(cTB.vPreviews)
