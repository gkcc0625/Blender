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

import mathutils
import os
import random
import re
import subprocess
import threading
import time
import webbrowser


import addon_utils
from bpy.types import Operator
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    StringProperty,
)
import bpy.utils.previews
import bmesh


from .toolbox import cTB
from .utils import *
from . import ui
from . import reporting


USER_COMMENT_LENGTH = 512  # Max length for user submitted error messages.


class POLIIGON_OT_setting(Operator):
    bl_idname = "poliigon.poliigon_setting"
    bl_label = ""
    bl_description = "Edit Poliigon Addon Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: bpy.props.StringProperty(default="", options={"HIDDEN"})
    vMode: bpy.props.StringProperty(default="", options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        cTB.get_ui_scale()  # Force update DPI check for scale.
        cTB.print_debug(0, "POLIIGON_OT_setting", self.vMode)

        # ...............................................................................

        vUpdate = 0
        vClearCache = 0

        if self.vMode in ["none", ""]:
            return {"FINISHED"}

        # ...............................................................................

        elif self.vMode == "set_library":
            tmp_path = cTB.vSettings["set_library"]
            cTB.register(cTB.version)  # Force reloading of variables as if startup.
            cTB.vSettings["set_library"] = tmp_path
            cTB.vWorking["startup"] = 1

            cTB.vSettings["library"] = cTB.vSettings["set_library"]

            vUpdate = 1

            f_MDir(cTB.vSettings["set_library"])

        # ...............................................................................

        elif self.vMode.startswith("area_"):
            cTB.check_icon_reload_interval()
            cTB.vSettings["area"] = self.vMode.replace("area_", "")

            vUpdate = 2

            # This was causing the delay when switching between Poliigon/My Assets
            # vClearCache = 1

            cTB.vSettings["show_settings"] = 0
            cTB.vSettings["show_user"] = 0
            cTB.vActiveAsset = None

            cTB.track_screen_from_area()

        # ...............................................................................

        elif self.vMode == "my_account":
            # TODO: Poll for online status in background thread.

            cTB.vSettings["show_settings"] = 0
            cTB.vSettings["show_user"] = 1
            cTB.vActiveAsset = None
            # cTB.vPage = 0
            # cTB.vPages = 1
            cTB.vGoTop = 1
            cTB.vRedraw = 1

            return {"FINISHED"}

        # ...............................................................................

        elif self.vMode == "settings":
            cTB.vSettings["show_settings"] = 1
            cTB.vSettings["show_user"] = 0
            cTB.vActiveAsset = None
            cTB.vGoTop = 1

            return {"FINISHED"}

        # ...............................................................................

        elif self.vMode.startswith("category_"):
            vFlt = self.vMode.split("_")
            i = int(vFlt[1])
            vF = vFlt[2]
            if i < len(cTB.vSettings["category"][cTB.vSettings["area"]]):
                cTB.vSettings["category"][cTB.vSettings["area"]][i] = vF
            else:
                cTB.vSettings["category"][cTB.vSettings["area"]].append(vF)
            cTB.vSettings["category"][cTB.vSettings["area"]] = cTB.vSettings[
                "category"
            ][cTB.vSettings["area"]][: i + 1]

            categories = cTB.vSettings["category"][cTB.vSettings["area"]]
            if len(categories) > 1 and categories[-1].startswith("All "):
                categories = categories[:-1]
            cTB.vSettings["category"][cTB.vSettings["area"]] = categories

            vUpdate = 1

            cTB.vActiveAsset = None
            cTB.vActiveMat = None
            cTB.vActiveMode = None
            # Do we want to clear searches when switching between areas?
            cTB.vSearch["poliigon"] = bpy.context.window_manager.poliigon_props.search_poliigon
            cTB.vSearch["my_assets"] = bpy.context.window_manager.poliigon_props.search_my_assets
            cTB.vSearch["imported"] = bpy.context.window_manager.poliigon_props.search_imported

        # ...............................................................................

        elif self.vMode.startswith("page_"):
            cTB.check_icon_reload_interval()
            vP = self.vMode.split("_")[-1]
            if cTB.vPage[cTB.vSettings["area"]] == vP:
                return {"FINISHED"}

            elif vP == "-":
                if cTB.vPage[cTB.vSettings["area"]] > 0:
                    cTB.vPage[cTB.vSettings["area"]] -= 1

            elif vP == "+":
                if cTB.vPage[cTB.vSettings["area"]] < cTB.vPages[cTB.vSettings["area"]]:
                    cTB.vPage[cTB.vSettings["area"]] += 1

            else:
                cTB.vPage[cTB.vSettings["area"]] = int(vP)

            vUpdate = 2

        # ...............................................................................

        elif self.vMode.startswith("page@"):
            vPerPage = int(self.vMode.split("@")[1])
            if cTB.vSettings["page"] != vPerPage:
                cTB.vSettings["page"] = vPerPage
                
                vUpdate = 1
                vClearCache = 1

        # ...............................................................................

        elif self.vMode.startswith("clear_search_"):
            if self.vMode.endswith("poliigon"):
                bpy.context.window_manager.poliigon_props.search_poliigon = ""
            elif self.vMode.endswith("my_assets"):
                bpy.context.window_manager.poliigon_props.search_my_assets = ""
            elif self.vMode.endswith("imported"):
                bpy.context.window_manager.poliigon_props.search_imported = ""

        # ...............................................................................

        elif self.vMode == "clear_email":
            bpy.context.window_manager.poliigon_props.vEmail = ""

        # ...............................................................................

        elif self.vMode == "clear_pass":
            bpy.context.window_manager.poliigon_props.vPassHide = ""
            bpy.context.window_manager.poliigon_props.vPassShow = ""

        # ...............................................................................
        
        # Can be removed if we're not going use the "show password" button
        elif self.vMode == "show_pass":
            if cTB.vSettings["show_pass"]:
                bpy.context.window_manager.poliigon_props.vPassHide = (
                    bpy.context.window_manager.poliigon_props.vPassShow
                )
            else:
                bpy.context.window_manager.poliigon_props.vPassShow = (
                    bpy.context.window_manager.poliigon_props.vPassHide
                )

            cTB.vSettings["show_pass"] = not cTB.vSettings["show_pass"]

        # ...............................................................................

        elif self.vMode in [
            "apply_subdiv",
            "auto_download",
            "download_lods",
            "mat_props_edit",
            "new_top",
            "show_active",
            "show_add_dir",
            "show_asset_info",
            "show_credits",
            "show_default_prefs",
            "show_display_prefs",
            "show_import_prefs",
            "show_mat_ops",
            "show_mat_props",
            "show_mat_texs",
            "show_plan",
            "show_settings",
            "show_user",
            "use_16",
        ]:
            cTB.vSettings[self.vMode] = not cTB.vSettings[self.vMode]

        # ...............................................................................

        elif self.vMode.startswith("default_"):
            vK = self.vMode.split("_")[1]
            vR = self.vMode.split("_")[2]
            cTB.vSettings[vK] = vR

        # ...............................................................................

        elif self.vMode.startswith("disable_dir_"):
            vDir = self.vMode.replace("disable_dir_", "")
            if vDir in cTB.vSettings["disabled_dirs"]:
                cTB.vSettings["disabled_dirs"].remove(vDir)
                cTB.print_debug(0, "Enabled directory: ", vDir)
            else:
                cTB.vSettings["disabled_dirs"].append(vDir)
                cTB.print_debug(0, "Disabled directory: ", vDir)
            cTB.f_GetLocalAssets(force=1)

        # ...............................................................................

        elif self.vMode.startswith("del_dir_"):
            vDir = self.vMode.replace("del_dir_", "")
            if vDir in cTB.vSettings["add_dirs"]:
                cTB.vSettings["add_dirs"].remove(vDir)
            cTB.f_GetLocalAssets(force=1)

        # ...............................................................................

        elif self.vMode.startswith("prop@"):
            vProp = self.vMode.split("@")[1]
            if vProp in cTB.vSettings["mat_props"]:
                cTB.vSettings["mat_props"].remove(vProp)
            else:
                cTB.vSettings["mat_props"].append(vProp)

        # ...............................................................................

        elif self.vMode.startswith("preset@"):
            if cTB.vEditPreset == self.vMode.split("@")[1]:
                try:
                    cTB.vPresets[cTB.vEditPreset] = [
                        float(vV)
                        for vV in context.scene.vEditText.replace(" ", "").split(";")
                    ]
                    cTB.vEditPreset = None
                except:
                    return {"FINISHED"}
            else:
                cTB.vEditPreset = self.vMode.split("@")[1]
                context.scene.vEditText = self.vMode.split("@")[2]
                return {"FINISHED"}

        # ...............................................................................

        elif self.vMode == "view_more":
            prev_area = cTB.vSettings["area"]
            cTB.vSettings["area"] = "poliigon"
            cTB.vSettings["category"][cTB.vSettings["area"]] = cTB.vSettings["category"][prev_area]

            vUpdate = 2

            cTB.vSettings["show_settings"] = 0
            cTB.vSettings["show_user"] = 0
            cTB.vSearch["poliigon"] = cTB.vSearch[prev_area]
            bpy.context.window_manager.poliigon_props.search_poliigon = cTB.vSearch[prev_area]
            cTB.vActiveAsset = None

        # ...............................................................................

        else:
            reporting.capture_message("invalid_setting_mode", self.vMode)
            self.report({"WARNING"}, f"Invalid setting mode {self.vMode}")
            return {'CANCELLED'}

        # ...............................................................................

        if vClearCache:
            cTB.vAssetsIndex["poliigon"] = {}
            cTB.vAssetsIndex["my_assets"] = {}
            cTB.vAssetsIndex["imported"] = {}

        if vUpdate:
            if vUpdate == 1:
                cTB.vPage[cTB.vSettings["area"]] = 0
                cTB.vPages[cTB.vSettings["area"]] = 1

            # Not setting cursor as it can lead to being stuck on "wait".
            # bpy.context.window.cursor_set("WAIT")

            # TODO: refactor to cache raw API request, also validate if this
            # needs re-requesting (has calls to f_GetCategoryChildren).
            cTB.f_GetCategories()

            cTB.vInterrupt = time.time()
            #cTB.vGettingData = 1

            cTB.f_GetSceneAssets()
            
            if cTB.vSettings["area"] == "poliigon":
                cTB.f_GetAssets()

            elif cTB.vSettings["area"] == "my_assets":
                cTB.f_GetLocalAssets()
                cTB.f_GetAssets()

            cTB.vGoTop = 1
            cTB.vRedraw = 1

        # ...............................................................................

        cTB.f_SaveSettings()

        return {"FINISHED"}


class POLIIGON_OT_user(Operator):
    bl_idname = "poliigon.poliigon_user"
    bl_label = ""
    bl_description = ""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vMode: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        cTB.vWorking["login"] = 1

        cTB.vRedraw = 1

        if self.vMode == "login":
            if (
                "@" not in bpy.context.window_manager.poliigon_props.vEmail
                or len(bpy.context.window_manager.poliigon_props.vPassHide) < 6
            ):
                cTB.clear_user_invalidated()
                cTB.vLoginError = cTB.ERR_CREDS_FORMAT
                return {"CANCELLED"}

        bpy.context.window.cursor_set("WAIT")
        cTB.print_debug(0, "Sending login request")

        vThread = threading.Thread(target=cTB.f_Login, args=(self.vMode,))
        vThread.daemon = 1
        vThread.start()
        cTB.vThreads.append(vThread)

        return {"FINISHED"}


class POLIIGON_OT_link(Operator):
    bl_idname = "poliigon.poliigon_link"
    bl_label = ""
    bl_description = "(Find asset on Poliigon.com in your default browser)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vMode: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        if self.vMode.startswith("notify"):
            _, vURL, action, notification_id = self.vMode.split("@")
            cTB.click_notification(notification_id, action)

        elif self.vMode == "signup":
            vURL = "https://www.poliigon.com/register"

        elif self.vMode == "subscribe":
            vURL = "https://www.poliigon.com/pricing"

        elif self.vMode == "forgot":
            vURL = "https://www.poliigon.com/password/reset"

        elif self.vMode == "credits":
            vURL = "https://www.poliigon.com/pricing#credit_pack"

        elif self.vMode == "privacy":
            vURL = "https://www.poliigon.com/privacy"

        elif self.vMode == "terms":
            vURL = "https://www.poliigon.com/terms"

        elif self.vMode.startswith("feedback"):
            vURL = self.vMode.split("@")[1]
            while cTB.vSettings["notify"] < cTB.vSettings["open_count"]:
                if cTB.vSettings["notify"] == 5:
                    cTB.vSettings["notify"] += 10
                elif cTB.vSettings["notify"] == 15:
                    cTB.vSettings["notify"] += 35
                else:
                    cTB.vSettings["notify"] += 50
            cTB.vNotify = None
            cTB.f_SaveSettings()

        else:
            # Assume passed in asset id, open asset page.
            asset_id = int(self.vMode)

            data = cTB.get_data_for_asset_id(asset_id)
            cTB.print_debug(0, "Data for asset id:", str(data))

            # TODO: Switch to using soon-to-deploy data["url"] api field.
            slug = data["slug"]
            if data["type"] == "Models":
                url_category = "model"
            elif data["type"] == "Brushes":
                url_category = "brush"
            elif data["type"] == "Textures":
                url_category = "texture"
            elif data["type"] == "HDRIs":
                url_category = "hdr"
            else:
                url_category = "texture"

            slug = f"{slug}/{asset_id}"
            vURL = f"https://www.poliigon.com/{url_category}/{slug}"

        final_url = cTB._api.add_utm_suffix(vURL)
        webbrowser.open(final_url)

        return {"FINISHED"}


class POLIIGON_OT_download(Operator):
    bl_idname = "poliigon.poliigon_download"
    bl_label = ""
    bl_description = "(Download Asset from Poliigon.com)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vAsset: StringProperty(options={"HIDDEN"})
    vType: StringProperty(options={"HIDDEN"})
    vMode: StringProperty(options={"HIDDEN"})
    vCredits: StringProperty(options={"HIDDEN"})
    vSize: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):

        if self.vMode == "download":
            cTB.reset_asset_error(asset_name=self.vAsset)
            if ";" in self.vSize:
                vTTips = [
                    "Download " + vS + " Textures" for vS in self.vSize.split(";")
                ]
                if self.vType == "Models":
                    vTTips = [
                        "Download with " + vS + " Textures"
                        for vS in self.vSize.split(";")
                    ]

                ui.f_Dropdown(
                    cTB,
                    vTitle="Choose Extra Texture Size to Download :",
                    vBtns=self.vSize.split(";"),
                    vTooltips=vTTips,
                    vCmd="poliigon.poliigon_download",
                    vAsset=self.vAsset,
                    vType=self.vType,
                    vMode=self.vMode,
                )

                return {"FINISHED"}

            asset_data = cTB.vAssets[cTB.vSettings["area"]][self.vType][self.vAsset]
            asset_id = asset_data["id"]

            size = None
            if self.vSize != '':
                size = self.vSize 

            cTB.vDownloadQueue[asset_id] = {
                "data": asset_data,
                "size": size,
                "download_size": None
            }

            cTB.print_debug(0, f"Queue download asset {asset_id}")
            cTB.queue_download(asset_id)

        elif self.vMode == "purchase":
            asset, asset_id = self.vAsset.split("@")
            asset_id = int(asset_id)
            cTB.reset_asset_error(asset_id=asset_id)

            asset_data = cTB.vAssets[cTB.vSettings["area"]][self.vType][asset]

            # keeping this for access to the data
            cTB.print_debug(0, f"Purchase asset {asset_id}")
            cTB.queue_purchase(asset_id, asset_data)

        cTB.refresh_ui()

        return {"FINISHED"}


class POLIIGON_OT_cancel_download(Operator):
    bl_idname = "poliigon.cancel_download"
    bl_label = "Cancel download"
    bl_description = "Cancel downloading this asset"
    bl_options = {"INTERNAL"}

    asset_id: IntProperty(default=0, options={'SKIP_SAVE'})

    @reporting.handle_operator(silent=True)
    def execute(self, context):
        if self.asset_id == 0:
            return {'CANCELLED'}
        cTB.vDownloadCancelled.add(self.asset_id)
        cTB.print_debug(0, "Cancelled download", self.asset_id)
        self.report({'WARNING'}, "Cancelling download")
        return {'FINISHED'}


class POLIIGON_OT_options(Operator):
    bl_idname = "poliigon.poliigon_asset_options"
    bl_label = ""
    bl_description = "Asset Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vType: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        if self.vData.startswith("size@"):
            cTB.vSetup["size"] = self.vData.split("@")[1]

        elif self.vData == "disp":
            cTB.vSetup["disp"] = not cTB.vSetup["disp"]

        elif "@" not in self.vData:
            ui.f_Dropdown(
                cTB,
                vBtns=["Open Asset Folder(s)", "Find Asset on Poliigon.com"],
                vCmd="poliigon.poliigon_asset_options",
                vData=self.vData,
            )

        else:
            vAsset, vMode = self.vData.split("@")

            vAData = cTB.vAssets["my_assets"][self.vType][vAsset]

            if vMode == "dir":
                vDirs = sorted(
                    list(set([os.path.dirname(vF) for vF in vAData["files"]]))
                )
                for i in range(len(vDirs)):
                    if vAsset in vDirs[i]:
                        vDirs[i] = vDirs[i].split(vAsset)[0] + vAsset
                vDirs = sorted(list(set(vDirs)))

                for vDir in vDirs:
                    try:
                        os.startfile(vDir)
                    except:
                        try:
                            subprocess.Popen(("open", vDir))
                        except:
                            try:
                                subprocess.Popen(("xdg-open", vDir))
                            except:
                                pass

            elif vMode == "link":
                vName = vAsset
                vAssetType = "T"
                vMods = [
                    vF for vF in vAData["files"] if f_FExt(vF) in [".fbx", ".blend"]
                ]
                if len(vMods):
                    vAssetType = "M"
                vName = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", vName)
                vName = (
                    (re.sub(r"(?<=[a-z])(?=[0-9])", " ", vName))
                    .lower()
                    .replace(" ", "-")
                )
                if vAssetType == "T":
                    vURL = "https://www.poliigon.com/texture/" + vName
                elif vAssetType == "M":
                    vURL = "https://www.poliigon.com/model/" + vName
                webbrowser.open(vURL)

        return {"FINISHED"}


class POLIIGON_OT_active(Operator):
    bl_idname = "poliigon.poliigon_active"
    bl_label = ""
    bl_description = "Set Active Asset"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vMode: StringProperty(options={"HIDDEN"})
    vType: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        if self.vData == "":
            cTB.vActiveType = None
            cTB.vActiveAsset = None
            cTB.vActiveMat = None
            cTB.vActiveMode = None

        elif self.vMode == "asset":
            cTB.vActiveType = self.vType
            cTB.vActiveAsset = self.vData
            if cTB.vActiveAsset in cTB.vAssets["imported"]["Textures"].keys():
                cTB.vActiveMat = cTB.vAssets["imported"]["Textures"][cTB.vActiveAsset][0].name
                context.scene.vEditMatName = cTB.vActiveMat
            else:
                cTB.vActiveMat = None
            cTB.vActiveMode = "asset"
            cTB.vSettings["show_active"] = 1
            cTB.vGoTop = 1

        elif self.vMode == "mat":
            cTB.vActiveType = self.vType
            if "@" in self.vData:
                cTB.vActiveAsset, cTB.vActiveMat = self.vData.split("@")
            else:
                cTB.vActiveMat = self.vData
            cTB.vActiveMode = "asset"

        elif self.vMode == "mixer":
            cTB.vActiveType = self.vType
            cTB.vActiveAsset = self.vData
            context.scene.vEditMatName = cTB.vActiveAsset
            cTB.vActiveMat = self.vData
            cTB.vActiveMode = "mixer"
            cTB.vSettings["show_active"] = 1
            cTB.vGoTop = 1

        elif self.vMode == "mix":
            cTB.vActiveMode = "mixer"
            cTB.vActiveMix = self.vData

        elif self.vMode == "mixmat":
            cTB.vActiveMode = "mixer"
            cTB.vActiveMixMat = self.vData

        elif self.vMode == "poliigon":
            cTB.vActiveMode = "poliigon"
            cTB.vActiveAsset = self.vData

        elif self.vMode == "settings":
            # f_Settings()

            return {"FINISHED"}

        elif self.vMode == "info":
            ui.f_AssetInfo(self.vData)

            return {"FINISHED"}

        cTB.vSuggestions = []
        cTB.vSuggest = ""
        """for vF in sorted(list(cTB.vCategories["poliigon"][cTB.vSettings["category"]["poliigon"][0]].keys())):
            if cTB.vActiveAsset.startswith(vF.replace("/", "")):
                cTB.vSuggest = vF

        if cTB.vSuggest != "":
            cTB.vSuggestions = [
                vA
                for vA in cTB.vCategories["poliigon"][
                    cTB.vSettings["category"]["poliigon"][0]
                ][cTB.vSuggest]
                if vA != cTB.vActiveAsset and vA not in cTB.vPurchased
            ]
            cTB.vSuggestions.sort()"""

        cTB.f_GetActiveData()

        return {"FINISHED"}


class POLIIGON_OT_preset(Operator):
    bl_idname = "poliigon.poliigon_preset"
    bl_label = ""
    bl_description = "Reset Property to Default"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})
    vMode: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        vProp = self.vData
        vVal = 0.0

        if vProp.startswith("detail@"):
            vVal = float(self.vData.split("@")[1])
            for vO in context.selected_objects:
                vO.cycles.dicing_rate = vVal
                if "Subdivision" in vO.modifiers.keys():
                    vO.modifiers["Subdivision"].subdivision_type = "SIMPLE"
            return {"FINISHED"}
        elif "@" in vProp:
            vSplit = self.vData.split("@")
            if len(vSplit) > 2:
                ui.f_Dropdown(
                    cTB,
                    vBtns=vSplit[1:],
                    vCmd="poliigon.poliigon_preset",
                    vData=vSplit[0],
                )
                return {"FINISHED"}
            vProp = vSplit[0]
            if vSplit[1] == "Random":
                vVal = random.random()
            elif vSplit[1] == "Real World":
                vDimen = "?"
                if vDimen == "?":
                    return {"FINISHED"}
                else:
                    vScaleMult = bpy.context.scene.unit_settings.scale_length

                    if bpy.context.scene.unit_settings.length_unit == "KILOMETERS":
                        vScaleMult *= 1000.0
                    elif bpy.context.scene.unit_settings.length_unit == "CENTIMETERS":
                        vScaleMult *= 1.0 / 100.0
                    elif bpy.context.scene.unit_settings.length_unit == "MILLIMETERS":
                        vScaleMult *= 1.0 / 1000.0
                    elif bpy.context.scene.unit_settings.length_unit == "MILES":
                        vScaleMult *= 1.0 / 0.000621371
                    elif bpy.context.scene.unit_settings.length_unit == "FEET":
                        vScaleMult *= 1.0 / 3.28084
                    elif bpy.context.scene.unit_settings.length_unit == "INCHES":
                        vScaleMult *= 1.0 / 39.3701

                    vScale = (
                        bpy.context.selected_objects[0].scale * vScaleMult
                    ) / vDimen
                    vVal = vScale[0]
            else:
                vVal = float(vSplit[1])
        elif vProp in cTB.vPropDefaults:
            vVal = cTB.vPropDefaults[vProp]

        if cTB.vActiveMode == "mixer":
            if self.vMode == "mix_mat":
                if cTB.vActiveMixProps[cTB.vActiveMix][1][0].name == cTB.vActiveMixMat:
                    vN = cTB.vActiveMixProps[cTB.vActiveMix][1][1][vProp]
                elif (
                    cTB.vActiveMixProps[cTB.vActiveMix][2][0].name == cTB.vActiveMixMat
                ):
                    vN = cTB.vActiveMixProps[cTB.vActiveMix][2][1][vProp]
            else:
                vN = cTB.vActiveMixProps[cTB.vActiveMix][3][vProp]
        else:
            vN = cTB.vActiveMatProps[vProp]

        vN.inputs[vProp].default_value = vVal

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class POLIIGON_OT_texture(Operator):
    bl_idname = "poliigon.poliigon_texture"
    bl_label = ""
    bl_description = "Texture Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vType: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        vAssetType = cTB.vSettings["category"][cTB.vSettings["area"]][0]

        vAData = cTB.vAssets["local"][self.vType][cTB.vActiveAsset]

        vSplit = self.vData.split("@")

        vAllSizes = ["1K", "2K", "3K", "4K", "6K", "8K", "16K"]

        if vSplit[0] == "size":
            if "#" in vSplit[1]:
                vSizes = vSplit[1].split("#")
                ui.f_Dropdown(
                    cTB,
                    vBtns=vSizes,
                    vCmd="poliigon.poliigon_texture",
                    vType=self.vType,
                    vData=vSplit[0],
                )
            else:
                vSize = vSplit[1]

                vTexs = [vF for vF in vAData["files"] if vSize in os.path.basename(vF)]
                if not len(vTexs):
                    return {"FINISHED"}
                vTNames = [f_FName(vF) for vF in vTexs]

                vMat = bpy.data.materials[cTB.vActiveMat]
                vName = cTB.vActiveMat
                for vS in vAllSizes:
                    vName = vName.replace(vS, vSize)
                vMat.name = vName
                cTB.vActiveMat = vName

                for vM in cTB.vActiveTextures.keys():
                    vMap = vM
                    if vM == "COL":
                        if "ALPHAMASKED" in str(vTNames):
                            vMap = "ALPHAMASKED"
                        else:
                            vMap = "COL"
                    elif (
                        vM == "BUMP"
                        and cTB.vSettings["use_16"]
                        and "BUMP16" in str(vTNames)
                    ):
                        vMap = "BUMP16"
                    elif (
                        vM == "DISP"
                        and cTB.vSettings["use_16"]
                        and "DISP16" in str(vTNames)
                    ):
                        vMap = "DISP16"
                    elif (
                        vM == "NRM"
                        and cTB.vSettings["use_16"]
                        and "NRM16" in str(vTNames)
                    ):
                        vMap = "NRM16"

                    vTex = [vF for vF in vTexs if vM in f_FName(vF).split("_")]
                    cTB.vActiveTextures[vM].image.filepath = vTex[0]

            return {"FINISHED"}

        vImage = vSplit[0]
        vTex = bpy.data.images[vImage]
        vMap = vSplit[1]

        vNSplit = f_FName(vTex.filepath).split("_")

        vSize = ""
        for i in range(len(vNSplit)):
            if vNSplit[i] in vAllSizes:
                vSize = vNSplit[i]

        vVars = vAData["vars"]

        if len(vSplit) < 3:
            vBtns = ["Replace"]
            vTTips = ["Replace Texture file"]

            if len(vVars) > 1:
                vBtns.append("-")
                vTTips.append("-")

                for vV in vVars:
                    vBtns.append(f_FName(vV))
                    vTTips.append("-")

            ui.f_Dropdown(
                cTB,
                vBtns=vBtns,
                vTooltips=vTTips,
                vCmd="poliigon.poliigon_texture",
                vType=self.vType,
                vData=self.vData,
            )
            return {"FINISHED"}

        vMode = vSplit[2]

        if vMode == "Replace":
            bpy.ops.poliigon.poliigon_file(
                "INVOKE_DEFAULT", filepath=vTex.filepath, vMode=vMode, vData=vImage
            )
        elif "VAR" in vMode:
            vFile = [vF for vF in vAData["files"] if f_FName(vF) == vMode]
            if len(vFile):
                if vFile[0] != vTex.filepath:
                    vTex.filepath = vFile[0]

        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


class POLIIGON_OT_detail(Operator):
    bl_idname = "poliigon.poliigon_detail"
    bl_label = ""
    bl_description = "Reset Property to Default"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    @reporting.handle_operator()
    def execute(self, context):
        if context.object.cycles.dicing_rate != context.scene.vDispDetail:
            context.object.cycles.dicing_rate = context.scene.vDispDetail
            context.object.modifiers["Subdivision"].subdivision_type = "SIMPLE"

        return {"FINISHED"}


class POLIIGON_OT_folder(Operator):
    bl_idname = "poliigon.poliigon_folder"
    bl_label = "Open Asset Folder"
    bl_description = "Open Asset Folder in system browser"
    bl_options = {"INTERNAL"}

    vAsset: StringProperty(options={"HIDDEN"})

    @reporting.handle_operator()
    def execute(self, context):
        asset_data = cTB.get_data_for_asset_name(self.vAsset)
        files = asset_data["files"]

        if not files:
            msg = f"No files found to open for {self.vAsset}"
            avail_keys = str(asset_data.keys())
            self.report({"ERROR"}, msg)
            reporting.capture_message(
                "open_folder_failed",
                f"{msg}, data: {avail_keys}")
            cTB.print_debug(0, msg)
            return {'CANCELLED'}

        dirs = [os.path.dirname(path) for path in files]
        dirs = list(set(dirs))
        if len(dirs) > 1:
            cTB.print_debug(0, "Opening more than one directory:", dirs)

        # Open folder, different methods for different operating systems.
        did_open = False
        for vDir in dirs:
            try:
                os.startfile(vDir)
                did_open = True
            except:
                try:
                    subprocess.Popen(("open", vDir))
                    did_open = True
                except:
                    try:
                        subprocess.Popen(("xdg-open", vDir))
                        did_open = True
                    except:
                        pass

        if not did_open:
            reporting.capture_message("open_folder_failed", vDir)
            self.report({"ERROR"}, f"Open folder here: {vDir}")
            return {'CANCELLED'}

        return {"FINISHED"}


class POLIIGON_OT_file(Operator):
    bl_idname = "poliigon.poliigon_file"
    bl_label = "Select File"
    bl_description = "Select File"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    filepath: StringProperty(subtype="FILE_PATH")
    vMode: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        vFile = self.filepath.replace("\\", "/")
        if not os.path.exists(vFile):
            return {"FINISHED"}

        if self.vMode == "Replace":
            vTex = bpy.data.images[self.vData].filepath = vFile
        elif self.vMode == "mixer":
            cTB.vMixTexture = vFile
            bpy.ops.poliigon.poliigon_mix("INVOKE_DEFAULT", vData=self.vData)
        elif self.vMode == "mixtex":
            cTB.vMixTexture = vFile
            bpy.ops.poliigon.poliigon_mix_tex("INVOKE_DEFAULT", vMode=self.vData)

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class POLIIGON_OT_library(Operator):
    bl_idname = "poliigon.poliigon_library"
    bl_label = "Poliigon Library"
    bl_description = "(Set Poliigon Library Location)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    directory: StringProperty(subtype="DIR_PATH")
    vMode: EnumProperty(
        items=[
            ("set_library", "set_library", "Set path on first load"),
            ("update_library", "update_library", "Update path from preferences")],
        options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    def execute(self, context):
        global cTB

        vDir = self.directory.replace("\\", "/")

        if self.vMode == "set_library":
            # Stage for confirmation on startup (or after deleted)
            cTB.vSettings["set_library"] = vDir

        else:  # update_library, from user preferences
            cTB.vSettings["library"] = vDir

            cTB.f_GetLocalAssets(1)
            cTB.vRedraw = 1
            cTB.f_SaveSettings()

        # if os.path.exists(vDir):
        #    bpy.ops.poliigon.poliigon_setting("INVOKE_DEFAULT")

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class POLIIGON_OT_directory(Operator):
    bl_idname = "poliigon.poliigon_directory"
    bl_label = "Add Additional Directory"
    bl_description = "Add Additional Directory to search for assets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    directory: StringProperty(subtype="DIR_PATH")

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        vDir = self.directory.replace("\\", "/")
        cTB.print_debug(0, vDir)

        if not os.path.exists(vDir) or vDir in cTB.vSettings["add_dirs"]:
            return {"FINISHED"}

        cTB.vSettings["add_dirs"].append(vDir)
        if vDir in cTB.vSettings["disabled_dirs"]:
            cTB.vSettings["disabled_dirs"].remove(vDir)

        cTB.f_GetLocalAssets(1)

        bpy.ops.poliigon.poliigon_setting("INVOKE_DEFAULT")

        return {"FINISHED"}

    def invoke(self, context, event):
        cTB.print_debug(0, self.directory)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class POLIIGON_OT_category(Operator):
    bl_idname = "poliigon.poliigon_category"
    bl_label = "Select a Category"
    bl_description = "Select a Category"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    def execute(self, context):
        vIdx = self.vData.split("@")[0]
        vFlts = self.vData.split("@")[1:]

        ui.show_categories_menu(
            cTB,
            categories=vFlts,
            index=vIdx
        )

        return {"FINISHED"}


# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class POLIIGON_OT_preview(Operator):
    """Quick asset preview by downloading download and applying watermark."""
    bl_idname = "poliigon.poliigon_preview"
    bl_label = ""
    bl_description = "Preview Material"
    bl_options = {"GRAB_CURSOR", "BLOCKING", "REGISTER", "INTERNAL", "UNDO"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vType: StringProperty(options={"HIDDEN"})
    vAsset: StringProperty(options={"HIDDEN"})

    _is_backplate = None
    _name = None
    _asset_id = None

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        cTB.reset_asset_error(asset_name=self.vAsset)
        t_start = time.time()
        files = self.download_preview(context)
        t_downloaded = time.time()

        if not files:
            self.report({'ERROR'}, "Failed to download preview files")
            struc_str = f"asset_name: {self.vAsset}"
            reporting.capture_message(
                "quick_preview_download_failed", struc_str, "error")
            return {'CANCELLED'}

        # Warn user on viewport change before post process, so that any later
        # warnings will popup and take priority to be visible to user. Blender
        # shows the last "self.report" message only (but all print to console).
        self.report_viewport(context)
        cTB.refresh_ui()

        if self._is_backplate:
            res = self.post_process_backplate(context, files)
        else:
            res = self.post_process_material(context, files)

        t_post_processed = time.time()
        total_time = t_post_processed - t_start
        download_time = t_downloaded - t_start

        debug_str = f"Preview Total time: {total_time}, download: {download_time}"
        cTB.print_debug(0, "POLIIGON_OT_preview", debug_str)

        cTB.signal_preview_asset(asset_id=self._asset_id)
        return res

    def download_preview(self, context):
        """Download a preview and return expected files."""
        vAData = cTB.get_poliigon_asset(self.vType, self.vAsset)
        self._is_backplate = cTB.check_backplate(self.vAsset)
        self._asset_id = vAData.get("id", 0)

        self._name = "PREVIEW_" + self.vAsset

        if self._is_backplate:
            bpy.context.window.cursor_set("WAIT")
            vFile = os.path.join(
                cTB.gOnlinePreviews, self.vAsset + "_quickpreview.jpg")

            files = [vFile]
            if not os.path.exists(vFile):
                vURL = cTB.vAssets["poliigon"][self.vType][self.vAsset]["preview"]
                vTemp = os.path.join(
                    cTB.gOnlinePreviews, self.vAsset + "_quickpreviewX.jpg")
                self.run_download_backplate(vURL, vTemp, vFile)
            return files

        elif len(vAData["quick_preview"]):
            bpy.context.window.cursor_set("WAIT")
            vDir = os.path.join(
                cTB.gSettingsDir.replace("Blender", "OnlinePreviews"),
                self.vAsset)
            f_MDir(vDir)

            files = []
            download_files = []
            for vURL in vAData["quick_preview"]:
                vFName = os.path.basename(vURL.split("?")[0])

                # Might need to skip certain maps to improve performance
                # if any(vM in vFName for vM in ['BUMP','DISP']+[f'VAR{i}' for i in range(2,9)]) :
                #    continue

                vFile = os.path.join(vDir, vFName)
                if not os.path.exists(vFile):
                    download_files.append([vURL, vFile])
                files.append(vFile)

            if download_files:
                # cTB.vQuickPreviewQueue[vAsset] = [vD[1] for vD in vDownload]
                self.run_download_material(download_files)
            return files
        else:
            return []

    def run_download_material(self, download_files):
        """Synchronous function to download material preview."""

        urls = []
        files = []
        for preview_set in download_files:
            urls.append(preview_set[0])
            basename, ext = f_FSplit(preview_set[1])
            tmp_name = f"{basename}X{ext}"
            files.append(tmp_name)

        req = cTB._api.pooled_preview_download(urls, files)

        if not req.ok:
            self.report({"ERROR"}, req.error)
            # Continue, as some may have worked.

        for vURL, vFile in download_files:
            vTemp, vExt = f_FSplit(vFile)
            vTemp += "X" + vExt

            try:
                if os.path.exists(vFile):
                    os.remove(vFile)
                os.rename(vTemp, vFile)
            except FileExistsError:
                msg = f"File {vFile} already exists, failed to rename"
                reporting.capture_message(
                    "download_mat_existing_file", msg, "error")
                self.report({"ERROR"}, msg)
            except Exception as e:
                reporting.capture_exception(e)
                self.report({"ERROR"}, "Failed to rename file")

    def run_download_backplate(self, vURL, vTemp, vFile):
        """Synchronous function to download backplate preview."""
        vReq = cTB._api.download_preview(vURL, vTemp)
        if vReq.ok:
            try:
                if os.path.exists(vFile):
                    os.remove(vFile)
                os.rename(vTemp, vFile)
            except FileExistsError:
                msg = f"File {vFile} already exists"
                reporting.capture_message(
                    "download_backplate_exists", msg, "error")
                self.report({"ERROR"}, msg)
            except Exception as e:
                reporting.capture_exception(e)
                self.report({"ERROR"}, "Failed to rename file")
        else:
            reporting.capture_message(
                "download_backplate_resp_err", vReq.error, "error")
            self.report({"ERROR"}, vReq.error)

    def post_process_backplate(self, context, files):
        if not files:  # API error from above.
            reporting.capture_message(
                "preview_file_not_populated",
                "Preview file not populated",
                "error")
            return {'CANCELLED'}
        vFile = files[0]
        cTB.f_BuildBackplate(self.vAsset, self._name, vFile)
        bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}

    def post_process_material(self, context, files):
        """Run after the download has completed."""
        bpy.context.window.cursor_set("DEFAULT")
        vMat = cTB.f_BuildMat(
            self.vAsset, "PREVIEW", files, "Textures", self)

        if vMat is None:
            self.report({"ERROR"}, "Material could not be created.")
            reporting.capture_message(
                "could_not_create_preview_mat", self.vAsset, 'error')
            return {"CANCELLED"}

        try:
            vSel = [vObj for vObj in context.scene.objects if vObj.select_get()]
        except:
            vSel = [vObj for vObj in context.scene.objects if vObj.select]

        if len(vSel):
            for vObj in vSel:
                vObj.active_material = vMat

        else:
            vObjs = [vO for vO in bpy.data.objects]

            # TODO: Remove operator calls in favor of direct creation/manip,
            # for speed and stability.
            bpy.ops.mesh.primitive_plane_add(
                size=1.0, location=context.scene.cursor.location,
                enter_editmode=False, rotation=(0, 0, 0)
            )

            vObj = [vO for vO in bpy.data.objects if vO not in vObjs][0]

            vObj.active_material = vMat

            vImage = None
            for vI in bpy.data.images:
                if vI.filepath in files:
                    vImage = vI

            if vImage != None:
                vW = vImage.size[0] / vImage.size[1]

                vObj.dimensions = mathutils.Vector((vW, 1.0, 0))

                vObj.delta_scale[0] = 1
                vObj.delta_scale[1] = 1
                vObj.delta_scale[2] = 1

                bpy.ops.object.select_all(action="DESELECT")
                try:
                    vObj.select_set(True)
                except:
                    vObj.select = True

                bpy.ops.object.transform_apply(
                    location=False, rotation=False, scale=True
                )

        bpy.context.window.cursor_set("DEFAULT")
        return {"FINISHED"}

    def report_viewport(self, context):
        """Send the appropriate report based on the current shading mode."""
        any_mat_or_render = False
        for vA in context.screen.areas:
            if vA.type == "VIEW_3D":
                for vSpace in vA.spaces:
                    if vSpace.type == "VIEW_3D":
                        if vSpace.shading.type in ["MATERIAL", "RENDERED"]:
                            any_mat_or_render = True
        if not any_mat_or_render:
            self.report({'WARNING'},
                        ("Enter material or rendered mode to view applied "
                        "quick preview"))


class POLIIGON_OT_view_thumbnail(Operator):
    bl_idname = "poliigon.view_thumbnail"
    bl_label = ""
    bl_description = "View larger thumbnail"
    bl_options = {"INTERNAL"}

    tooltip: StringProperty(options={"HIDDEN"})
    asset: StringProperty(options={"HIDDEN"})
    thumbnail_index: IntProperty(min=0, options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.tooltip

    @reporting.handle_operator()
    def execute(self, context):
        cTB.reset_asset_error(asset_name=self.asset)

        # Check if index count is valid, noting that index 0 is should be the
        # low resolution preview, and index 1 the same image at 1K.
        asset_data = cTB.get_data_for_asset_name(self.asset)
        count = len(asset_data["thumbnails"])
        if self.thumbnail_index > count + 1:
            msg = f"Invalid thumbnail index: {self.thumbnail_index}"
            self.report({"ERROR"}, msg)
            reporting.capture_message("bad_thumbnail_index", msg, 'info')
            return {'CANCELLED'}

        # We use the show render operator to hack setting an explicit size,
        # be sure to capture the resolution to revert back.
        render = bpy.context.scene.render
        init_res_x = render.resolution_x
        init_res_y = render.resolution_y
        if hasattr(context.preferences.view, "render_display_type"):
            init_display = bpy.context.preferences.view.render_display_type
        else:
            init_display = context.scene.render.display_mode

        # Don't modify by get_ui_scale(), as it uses physical pixel size. Also
        # making it smaller than 1024 to minimize margins around image.
        pixels = int(1000)

        try:
            # Modify render settings to force new window to appear.
            render.resolution_x = pixels
            render.resolution_y = pixels
            if hasattr(context.preferences.view, "render_display_type"):
                context.preferences.view.render_display_type = "WINDOW"
            else:
                context.scene.render.display_mode = "WINDOW"

            # Main loading steps
            area = self.create_window()
            self.download_thumbnail()
            res = self.load_preview(area)

        except Exception as e:
            # If exception occurs, will run after the finally block below.
            raise e

        finally:
            # Ensure we always restore render settings and preferences.
            render.resolution_x = init_res_x
            render.resolution_y = init_res_y
            if hasattr(context.preferences.view, "render_display_type"):
                context.preferences.view.render_display_type = init_display
            else:
                context.scene.render.display_mode = init_display

        return res

    def create_window(self):
        # Call image editor window
        bpy.ops.render.view_show("INVOKE_DEFAULT")

        # Set up the window as needed.
        area = None
        for window in bpy.context.window_manager.windows:
            this_area = window.screen.areas[0]
            if this_area.type == "IMAGE_EDITOR":
                area = this_area
                break
        if not area:
            return None

        i = self.thumbnail_index if self.thumbnail_index > 0 else 1
        asset_data = cTB.get_data_for_asset_name(self.asset)
        count = len(asset_data["thumbnails"])
        # TODO: Showcase index/count once button exists to flip through.
        # area.header_text_set(f"Asset thumbnail: {self.asset} ({i}/{count})")
        area.header_text_set(f"Asset thumbnail: {self.asset}")
        area.show_menus = False
        return area

    def download_thumbnail(self):
        """Download the target thumbnail if not local, no threading."""
        cTB.print_debug(0, "Download thumbnail index", self.thumbnail_index)
        bpy.context.window.cursor_set("WAIT")
        try:
            cTB.f_DownloadPreview(self.asset, self.thumbnail_index)
        except Exception as e:
            raise e
        finally:
            bpy.context.window.cursor_set("DEFAULT")

    def load_preview(self, area):
        """Load in the image preview based on the area."""
        path = cTB.f_GetThumbnailPath(self.asset, self.thumbnail_index)

        if not os.path.isfile(path):
            self.report({'ERROR'}, "Could not find image preview")
            msg = f"Could not find image preview {path}"
            reporting.capture_message("thumbnail_file_missing", msg, 'error')
            return {'CANCELLED'}

        thumbnail = bpy.data.images.load(path)

        if area:
            area.spaces[0].image = thumbnail
        else:
            msg = "Open the image now loaded in an image viewer"
            self.report({"ERROR"}, msg)
            err = "Failed to open window for preview"
            reporting.capture_message("img_window_failed_open", err, 'info')

        # Tag this image with a property, could be used to trigger UI draws in
        # the viewer in the future.
        thumbnail["poliigon_thumbnail"] = True

        return {'FINISHED'}


class POLIIGON_OT_material(Operator):
    bl_idname = "poliigon.poliigon_material"
    bl_label = ""
    bl_description = "Create Material"
    bl_options = {"GRAB_CURSOR", "BLOCKING", "REGISTER", "INTERNAL", "UNDO"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vAsset: StringProperty(options={"HIDDEN"})
    vSize: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})
    vType: StringProperty(options={"HIDDEN"})
    vApply: IntProperty(options={"HIDDEN"}, default=1)

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        cTB.reset_asset_error(asset_name=self.vAsset)

        if self.vData == "rename":
            vMat = bpy.data.materials[cTB.vActiveMat]
            cTB.vActiveMat = bpy.context.scene.vEditMatName
            vMat.name = cTB.vActiveMat
            return {"FINISHED"}

        vSel = [vO for vO in context.selected_objects]
        vAddDisp = [vO for vO in vSel if "Subdivision" not in vO.modifiers]

        vAsset = self.vAsset
        vSize = self.vSize
        vSubdiv = 0

        vBackplate = cTB.check_backplate(vAsset)

        if self.vType not in cTB.vAssets["local"]:
            self.report({"ERROR"}, (
                f"Asset type {self.vType} not loaded, "
                "try searching for asset first"))
            return {'CANCELLED'}
        if vAsset not in cTB.vAssets["local"][self.vType]:
            self.report(
                {"ERROR"},
                f"Asset {vAsset} not loaded, try searching for asset first")
            return {'CANCELLED'}
        vAData = cTB.vAssets["local"][self.vType][vAsset]

        if self.vType in cTB.vAssets["my_assets"].keys():
            vSizes = vAData["sizes"]
            if vSize not in vSizes:
                cTB.print_debug(0, "apply_mat_size_not_local", vAData, vSize)
                self.report({"ERROR"}, f"Use quick menu to download {vSize}")
                reporting.capture_message("apply_mat_size_not_local", vAsset)
                return {"CANCELLED"}

        cTB.print_debug(0, "Size :", vSize)

        vMatName = vAsset + "_" + vSize
        if vMatName in bpy.data.materials.keys():
            # prevent duplicate materials from being created unintentionally
            # but we probably want to provide an option for that at some point.
            self.report({"WARNING"}, "Applying existing material")

            rtn = bpy.ops.poliigon.poliigon_apply(
                "INVOKE_DEFAULT", vAsset=vAsset, vMat=vMatName
            )
            if rtn == {"CANCELLED"}:
                self.report({"WARNING"}, "Could not apply materials to selection")

            return {"FINISHED"}

        vTexs = [vF for vF in vAData["files"] if vSize in os.path.basename(vF)]

        if not len(vTexs):
            self.report({"WARNING"}, "No Textures found.")
            reporting.capture_message("apply_mat_tex_not_found", vAsset)
            return {"CANCELLED"}

        vDir = os.path.dirname(vTexs[0])

        # BACKPLATE ...............................................................................................

        if vBackplate:
            cTB.f_BuildBackplate(vAsset, vAsset, vTexs[0])

            return {"FINISHED"}
        
        # DISPLACEMENT ...............................................................................................
        
        if cTB.vSettings["use_disp"]:
            if cTB.prefs and cTB.prefs.use_micro_displacements:
                vSubdiv = 1

        # ...............................................................................................

        vMat = cTB.f_BuildMat(vAsset, vSize, vAData["files"], "Textures", self)

        if vMat is None:
            reporting.capture_message(
                "could_not_create_mat", vAsset, 'error')
            self.report({"ERROR"}, "Material could not be created.")
            return {"CANCELLED"}

        cTB.f_GetSceneAssets()

        cTB.vActiveType = self.vType
        cTB.vActiveAsset = vAsset
        cTB.vActiveMat = vMat.name

        bpy.ops.poliigon.poliigon_active(
            vMode="mat", vType=cTB.vActiveType, vData=cTB.vActiveMat
        )
        
        if not self.vApply:
            cTB.vGoTop = 1
            return {"FINISHED"}

        rtn = bpy.ops.poliigon.poliigon_apply(
            "INVOKE_DEFAULT", vAsset=vAsset, vMat=vMat.name
        )
        if rtn == {"CANCELLED"}:
            self.report({"WARNING"}, "Could not apply materials to selection")

        cTB.vGoTop = 1
        return {"FINISHED"}


class POLIIGON_OT_show_quick_menu(Operator):
    bl_idname = "poliigon.show_quick_menu"
    bl_label = ""
    bl_description = "Show quick menu"

    vTooltip: StringProperty(options={"HIDDEN"})
    vAsset: StringProperty(options={"HIDDEN"})
    vAssetId: IntProperty(options={"HIDDEN"})
    vAssetType: StringProperty(options={"HIDDEN"})
    vSizes: StringProperty(options={"HIDDEN"})  # e.g. 1K;2K;HIGHRES

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        if bpy.app.background:
            return {'CANCELLED'}  # Don't popup menus when running headless.
        sizes = self.vSizes.split(";") if self.vSizes else []
        ui.show_quick_menu(cTB,
                           asset_name=self.vAsset,
                           asset_id=self.vAssetId,
                           asset_type=self.vAssetType,
                           sizes=sizes)
        return {'FINISHED'}


class POLIIGON_OT_apply(Operator):
    bl_idname = "poliigon.poliigon_apply"
    bl_label = "Apply Material :"
    bl_description = "Apply Material to Selection"
    bl_options = {"REGISTER", "INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vType: StringProperty(options={"HIDDEN"})
    vAsset: StringProperty(options={"HIDDEN"})
    vMat: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        vSel = [vO for vO in context.selected_objects]
        if not len(vSel):
            for vObj in context.scene.objects:
                if vObj.mode == "EDIT":
                    vMesh = vObj.data
                    vBMesh = bmesh.from_edit_mesh(vMesh)
                    for vF in vBMesh.faces:
                        if vF.select:
                            vSel.append(vObj)
                            break

        vAddDisp = [vO for vO in vSel if "Subdivision" not in vO.modifiers]

        vAsset = self.vAsset
        vMatN = self.vMat
        vSubdiv = 0

        # ...............................................................................................

        if vMatN != "":
            vMat = bpy.data.materials[vMatN]

        elif vAsset in cTB.vAssets["imported"]["Textures"].keys():
            if len(cTB.vAssets["imported"]["Textures"][vAsset]) == 1:
                vMat = cTB.vAssets["imported"]["Textures"][vAsset][0]
                vMatN = vMat.name

            else:
                # Unexpected need to download local, should avoid happening.
                reporting.capture_message(
                    "triggered_popup_mid_apply", vAsset, level='info')
                ui.f_Dropdown(
                    cTB,
                    vBtns=[vM.name for vM in cTB.vAssets["imported"]["Textures"][vAsset]],
                    vCmd="poliigon.poliigon_apply",
                    vType=self.vType,
                    vAsset=self.vAsset,
                    vMat=self.vMat,
                )
                return {"FINISHED"}

        # ...............................................................................................

        if cTB.vSettings["use_disp"] and len(vAddDisp):
            if cTB.prefs and cTB.prefs.use_micro_displacements:
                vSubdiv = 1

        # ...............................................................................................

        if vSubdiv or len(vSel) > len(vAddDisp):
            bpy.context.scene.render.engine = "CYCLES"
            bpy.context.scene.cycles.feature_set = "EXPERIMENTAL"

            vMNodes = vMat.node_tree.nodes
            for vN in vMNodes:
                if vN.type == "GROUP":
                    for vI in vN.inputs:
                        if vI.type == "VALUE":
                            if vI.name == "Displacement Strength":
                                if vN.inputs[vI.name].default_value == 0.0:
                                    vN.inputs[vI.name].default_value = 0.05

        vAllFaces = []
        for vK in cTB.vActiveFaces.keys():
            vAllFaces += cTB.vActiveFaces[vK]

        valid_objects = 0
        for vObj in vSel:
            if hasattr(vObj.data, "materials"):
                valid_objects += 1
            else:
                continue

            if vObj.mode != "EDIT":
                vObj.active_material = vMat
            else:
                vMats = [vM.material for vM in vObj.material_slots if vM != None]
                if vMat not in vMats:
                    vObj.data.materials.append(vMat)
                vMesh = vObj.data
                vBMesh = bmesh.from_edit_mesh(vMesh)
                for i in range(len(vObj.material_slots)):
                    if vObj.material_slots[i].material == vMat:
                        vObj.active_material_index = i
                        bpy.ops.object.material_slot_assign()

            if vSubdiv and vObj in vAddDisp:
                vMod = vObj.modifiers.new(name="Subdivision", type="SUBSURF")
                vMod.subdivision_type = "SIMPLE"
                vMod.levels = 0  # Don't do subdiv in viewport
                vObj.cycles.use_adaptive_subdivision = 1

            # Scale ...............................................................................................

            vDimen = "?"
            if vDimen != "?":
                vScaleMult = bpy.context.scene.unit_settings.scale_length

                if bpy.context.scene.unit_settings.length_unit == "KILOMETERS":
                    vScaleMult *= 1000.0
                elif bpy.context.scene.unit_settings.length_unit == "CENTIMETERS":
                    vScaleMult *= 1.0 / 100.0
                elif bpy.context.scene.unit_settings.length_unit == "MILLIMETERS":
                    vScaleMult *= 1.0 / 1000.0
                elif bpy.context.scene.unit_settings.length_unit == "MILES":
                    vScaleMult *= 1.0 / 0.000621371
                elif bpy.context.scene.unit_settings.length_unit == "FEET":
                    vScaleMult *= 1.0 / 3.28084
                elif bpy.context.scene.unit_settings.length_unit == "INCHES":
                    vScaleMult *= 1.0 / 39.3701

                vScale = (vObj.scale * vScaleMult) / vDimen

                vMNodes = vMat.node_tree.nodes
                for vN in vMNodes:
                    if vN.type == "GROUP":
                        for vI in vN.inputs:
                            if vI.type == "VALUE":
                                if vI.name == "Scale":
                                    vN.inputs[vI.name].default_value = vScale[0]

        # ...............................................................................................

        cTB.vActiveType = self.vType
        cTB.vActiveAsset = vAsset
        cTB.vActiveMat = vMat.name
        bpy.ops.poliigon.poliigon_active(
            vMode="mat", vType=self.vType, vData=cTB.vActiveMat
        )

        # Attempt to fetch id.
        data = cTB.get_data_for_asset_name(vAsset)
        if data and data.get("id"):
            cTB.signal_import_asset(asset_id=data["id"])
        else:
            cTB.signal_import_asset(asset_id=0)
        return {"FINISHED"}


# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class POLIIGON_OT_model(Operator):
    bl_idname = "poliigon.poliigon_model"
    bl_label = "Import model"
    bl_description = "Import Model"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vType: StringProperty(options={"HIDDEN"})
    vAsset: StringProperty(options={"HIDDEN"})
    vSize: StringProperty(options={"HIDDEN"})
    vLod: StringProperty(options={"HIDDEN"})
    vUseCollection: BoolProperty(
        name="Import as collection",
        description="Instance model from a reusable collection",
        default=False)
    vReuseMaterials: BoolProperty(
        name="Reuse materials",
        description="Reuse already imported materials to avoid duplicates",
        default=False)

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    def draw(self, context):
        self.layout.prop(self, "vUseCollection")
        self.layout.prop(self, "vReuseMaterials")

    @reporting.handle_operator()
    def execute(self, context):
        vAsset = self.vAsset
        cTB.reset_asset_error(asset_name=vAsset)

        if vAsset not in cTB.vAssets["local"][self.vType].keys():
            err = f"Asset not found locally: {vAsset}"
            reporting.capture_message("model_texture_missing", err, "error")
            self.report({'ERROR'}, err)
            return {"CANCELLED"}

        asset_id, fbx_files, textures, size, lod = self.get_model_data()

        asset_name = construct_model_name(vAsset, size, lod)
        did_fresh_import = False
        inst = None
        new_objs = []

        # Import the model.
        if self.vUseCollection is False:
            ok, new_objs, mats = self.run_fresh_import(
                context, fbx_files, textures, size, lod)
            did_fresh_import = True
        elif not bpy.data.collections.get(asset_name):
            ok, new_objs, mats = self.run_fresh_import(
                context, fbx_files, textures, size, lod)
            did_fresh_import = True

        # If imported, perform these steps regardless of collection or not.
        if did_fresh_import:
            empty = self.setup_empty_parent(context, new_objs)
        else:
            empty = None

        if self.vUseCollection is True:
            # Move the objects into a subcollection, and place in scene.
            if did_fresh_import:
                # Always create a new collection if did a fresh import.
                cache_coll = bpy.data.collections.new(asset_name)
                # Ensure all objects are only part of this new collection.
                for obj in [empty] + new_objs:
                    for vC in obj.users_collection:
                        vC.objects.unlink(obj)
                    cache_coll.objects.link(obj)

                # Now add the cache collection to the layer, but unchecked.
                layer = context.view_layer.active_layer_collection
                layer.collection.children.link(cache_coll)
                for ch in layer.children:
                    if ch.collection == cache_coll:
                        ch.exclude = True
            else:
                cache_coll = bpy.data.collections.get(asset_name)

            # Now finally add the instance to the scene.
            if cache_coll:
                inst = self.create_instance(context, cache_coll, size, lod)
                # layer = context.view_layer.active_layer_collection
                # layer.collection.objects.link(inst)
            else:
                # Raise error, TODO.
                err = "Failed to get new collection to instance"
                self.report({"ERROR"}, err)
                return {"CANCELLED"}

        else:
            # Make sure the objects improted are all part of the same coll.
            self.append_cleanup(context, empty)

        # Final notifications and reporting.
        cTB.f_GetSceneAssets()

        if did_fresh_import is True:
            self.report({"INFO"}, "Model Imported : " + asset_name)
        elif self.vUseCollection and inst is not None:
            self.report({"INFO"}, "Instance created : " + inst.name)
        else:
            err = "Failed to import model correctly : " + asset_name
            self.report({"ERROR"}, err)
            reporting.capture_message("import-model-failed", err, "error")
            return {"CANCELLED"}

        cTB.signal_import_asset(asset_id=asset_id)
        return {"FINISHED"}

    def get_model_data(self):
        vAData = cTB.vAssets["local"][self.vType][self.vAsset]
        asset_id = vAData.get("id", 0)

        # Get the intended material size and LOD import to use.
        if self.vSize:
            vSize = cTB.f_GetClosestSize(vAData["sizes"], self.vSize)
        else:
            vSize = cTB.f_GetClosestSize(vAData["sizes"],
                                         cTB.vSettings["mres"])

        vLod = self.vLod
        if len(vAData["lods"]):
            vLod = cTB.vSettings["lod"] if vLod == "default" else vLod
            vLod = cTB.f_GetClosestLod(vAData["lods"], vLod)
        else:
            vLod = None

        vLODFBXs = [
            vF for vF in vAData["files"]
            if f_FExt(vF) == ".fbx" and str(vLod) in f_FName(vF).split("_")]
        vFBXs = []
        vFNames = [self.vAsset]
        for vF in vAData["files"]:
            if f_FExt(vF) != ".fbx":
                continue

            if vLod is not None and len(vLODFBXs):
                if vF not in vLODFBXs:
                    continue

            vFN = f_FName(vF).split("_")[0]
            vFBXs.append(vF)
            if vFN not in vFNames:
                vFNames.append(vFN)

            cTB.print_debug(0, os.path.basename(vF))

        vTextures = []
        for vT in vAData["files"]:
            if f_FExt(vT) not in cTB.vTexExts:
                continue

            if vSize not in f_FName(vT).split("_"):
                continue

            if any(
                vL in f_FName(vT).split("_") for vL in cTB.vLODs
            ) and vLod not in f_FName(vT).split("_"):
                continue

            vTextures.append(vT)

        return asset_id, vFBXs, vTextures, vSize, vLod

    def run_fresh_import(self, context, vFBXs, vTextures, vSize, vLod):
        """Performs a fresh import of the whole model.

        There can be multiple FBX models, therefore we want to import all of
        them and verify each one was properly imported.
        """
        vAllMeshes = []
        vAllMaterials = []
        imported_fbx = []
        for vFBX in vFBXs:
            vFBXName = f_FName(vFBX)

            if not f_Ex(vFBX):
                err = f"Couldn't load .fbx file : {vFBX}"
                self.report({"ERROR"}, err)
                reporting.capture_message("model_fbx_missing", err, "info")
                continue

            vObjs = list(context.scene.objects)
            bpy.ops.import_scene.fbx(filepath=vFBX, axis_up="-Z")
            imported_fbx.append(vFBX)
            vMeshes = [vM for vM in list(context.scene.objects)
                       if vM not in vObjs]

            vAllMeshes += vMeshes

            for vMesh in vMeshes:
                vMeshName = vMesh.name.split(".")[0].split("_")[0]

                vMVar = cTB.f_GetVar(vMesh.name)

                vMatName = vMeshName
                vTexs = []
                for vCheck in [vMeshName, vFBXName.split("_")[0], self.vAsset]:
                    if not len(vTexs):
                        vTexs = [
                            vT
                            for vT in vTextures
                            if os.path.basename(vT).startswith(vCheck)
                            if cTB.f_GetVar(f_FName(vT)) in [None, vMVar]
                        ]
                        vMatName = vCheck

                if not len(vTexs):
                    err = f"No Textures found for : {vMesh.name}"
                    reporting.capture_message(
                        "model_texture_missing", err, "info")
                    continue

                vMatName += f"_{vSize}"

                if vMVar is not None:
                    vMatName += f"_{vMVar}"

                # if vMatName in bpy.data.materials and self.vReuseMaterials:
                #     vMat = bpy.data.materials[vMatName]
                # else:
                vMat = cTB.f_BuildMat(
                    vMatName, vSize, vTexs, "Models", self,
                    vLOD=vLod, vReuse=self.vReuseMaterials)

                if vMat is None:
                    reporting.capture_message(
                        "could_not_create_fbx_mat", vMatName, 'error')
                    self.report({"ERROR"}, "Material could not be created.")
                    imported_fbx.remove(vFBX)
                    break

                vAllMaterials.append(vMat)
                vMesh.active_material = vMat

                if vMVar is not None:
                    # TODO: replace operator call with direct iteration.
                    bpy.ops.object.select_all(action="DESELECT")
                    vMesh.select_set(True)

                    try:
                        vMesh.material_slots[0].link = "OBJECT"
                    except:
                        bpy.ops.object.material_slot_add()
                        vMesh.material_slots[0].link = "OBJECT"

                    # Is there a better way to do this? Some objects have
                    # multiple mats.
                    vMesh.material_slots[0].material = vMat

                # Ensure we can identify the mesh & LOD even on name change.
                vMesh.poliigon = f"Models;{self.vAsset}"
                if vLod is not None:
                    vMesh.poliigon_lod = vLod

        # There could have been multiple FBXs, consider fully imported
        # for user-popup reporting if all FBX files imported.
        did_full_import = len(imported_fbx) == len(vFBXs)

        return did_full_import, vAllMeshes, vAllMaterials

    def setup_empty_parent(self, context, new_meshes):
        """Parents newly imported objects to a central empty object."""
        radius = 0
        for vMesh in new_meshes:
            vBnds = vMesh.dimensions
            if vBnds.x > radius:
                radius = vBnds.x
            if vBnds.y > radius:
                radius = vBnds.y

        empty = bpy.data.objects.new(
            name=f"{self.vAsset}_Empty", object_data=None)
        if self.vUseCollection:
            empty.empty_display_size = 0.01
        else:
            empty.empty_display_size = radius * 0.5

        layer = context.view_layer.active_layer_collection
        layer.collection.objects.link(empty)

        for mesh in new_meshes:
            mesh.parent = empty

        return empty

    def create_instance(self, context, coll, size, lod):
        """Creates an instance of an existing collection int he active view."""
        inst_name = construct_model_name(self.vAsset, size, lod) + "_Instance"
        inst = bpy.data.objects.new(name=inst_name, object_data=None)
        inst.instance_collection = coll
        inst.instance_type = "COLLECTION"
        lc = context.view_layer.active_layer_collection
        lc.collection.objects.link(inst)
        inst.location = context.scene.cursor.location
        inst.empty_display_size = 0.01

        # Set selection and active object.
        for obj in context.scene.collection.all_objects:
            obj.select_set(False)
        inst.select_set(True)
        context.view_layer.objects.active = inst

        return inst

    def append_cleanup(self, context, root_empty):
        """Performs selection and placement cleanup after an import/append."""
        if not root_empty:
            print("root_empty was not a valid object, exiting cleanup")
            return

        # Set empty location
        root_empty.location = context.scene.cursor.location

        # Deselect all others in scene (faster than using operator call).
        for obj in context.scene.collection.all_objects:
            obj.select_set(False)

        # Make empty active and select it + children.
        root_empty.select_set(True)
        context.view_layer.objects.active = root_empty
        for obj in root_empty.children:
            obj.select_set(True)


class POLIIGON_OT_select(Operator):
    bl_idname = "poliigon.poliigon_select"
    bl_label = ""
    bl_description = "Select Model"
    bl_options = {"REGISTER", "INTERNAL", "UNDO"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vMode: StringProperty(options={"HIDDEN"})
    vData: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        if self.vMode == "faces":
            vObj = context.active_object

            self.deselect(context)

            i = int(self.vData)
            vMat = vObj.material_slots[i].material

            bpy.ops.object.mode_set(mode="EDIT")

            vMesh = vObj.data
            vBMesh = bmesh.from_edit_mesh(vMesh)
            for vF in vBMesh.faces:
                vF.select = 0

            vObj.active_material_index = i
            bpy.ops.object.material_slot_select()

        elif self.vMode == "object":
            self.deselect(context)
            vObj = context.scene.objects[self.vData]
            try:
                vObj.select_set(True)
            except RuntimeError:
                pass  # Might not be in view layer

        elif "@" in self.vData:
            vSplit = self.vData.split("@")
            self.deselect(context)
            try:
                context.scene.objects[vSplit[1]].select_set(1)
            except RuntimeError:
                pass  # Might not be in view layer

        elif self.vMode == "model":
            if not context.mode == "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            self.deselect(context)
            to_select = []

            key = self.vData
            print(key)
            for obj in context.scene.objects:
                split = obj.name.rsplit("_")[0]

                # For instance collections
                if split == key and obj.instance_type == "COLLECTION":
                    to_select.append(obj)
                # For empty parents
                ref_key = key + "_empty"
                if obj.name.lower().startswith(ref_key.lower()):
                    to_select.append(obj)
                # For the objects within the empty tree
                if key in obj.poliigon.split(";")[-1]:
                    to_select.append(obj)

            for obj in to_select:
                try:
                    obj.select_set(True)
                except RuntimeError:
                    pass  # Might not be in view layer

        elif self.vMode == "mat_objs":
            vMat = bpy.data.materials[self.vData]

            vObjs = [vO for vO in context.scene.objects if vO.active_material == vMat]

            if len(vObjs) == 1:
                self.deselect(context)
                try:
                    vObjs[0].select_set(True)
                except RuntimeError:
                    pass  # Might not be in view layer

            else:
                ui.f_Dropdown(
                    cTB,
                    vBtns=sorted([vObj.name for vObj in vObjs]),
                    vCmd="poliigon.poliigon_select",
                    vMode=self.vMode,
                    vData=self.vData,
                )
                return {"FINISHED"}

        return {"FINISHED"}

    def deselect(self, context):
        """Deselects objects in a lower api, faster, context-invaraint way."""
        for obj in context.scene.collection.all_objects:
            try:
                obj.select_set(False)
            except RuntimeError:
                pass  # Might not be in view layer


# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class POLIIGON_OT_hdri(Operator):
    bl_idname = "poliigon.poliigon_hdri"
    bl_label = ""
    bl_description = "Import HDRI"
    bl_options = {"GRAB_CURSOR", "BLOCKING", "REGISTER", "INTERNAL", "UNDO"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vAsset: StringProperty(options={"HIDDEN"})
    vSize: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        vAsset = self.vAsset
        vSize = self.vSize

        cTB.reset_asset_error(asset_name=vAsset)

        vAData = cTB.get_data_for_asset_name(vAsset)
        if not vAData:
            # Force non-threaded fetch to load local assets.
            cTB.f_GetLocalAssetsThread()
            vAData = cTB.get_data_for_asset_name(vAsset)
            reporting.capture_message(
                "hdri_force_fetched_data", vAsset, "info")

        if not vAData:
            msg = f"Failed to load data for {vAsset}"
            reporting.capture_message("failed_load_data_hdri", msg)
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}

        # Must ensure we copy the dict, otherwise we are inadvertently updating
        # the other datastructures (poliigon, my_assets) with data from (local)
        vAData = vAData.copy()

        if cTB.vAssets["local"]["HDRIs"].get(vAsset):
            vAData.update(cTB.vAssets["local"]["HDRIs"].get(vAsset))
        vLIName = vAsset + "_Light"
        vBIName = vAsset + "_Background"

        cTB.print_debug(0, vAData, vLIName, vBIName)

        if "HDRIs" in cTB.vAssets["imported"]:
            existing = cTB.vAssets["imported"]["HDRIs"].get(vAsset)
        else:
            existing = None

        # Whenever an HDR is loaded, it fully replaces the prior loaded
        # resolutions. Thus, if we are "applying" an already imported one,
        # we don't need to worry about resolution selection.

        if self.vSize != "apply" or not existing:
            # Remove existing images to force load this resolution.
            if vLIName in bpy.data.images.keys():
                bpy.data.images.remove(bpy.data.images[vLIName])

            if vBIName in bpy.data.images.keys():
                bpy.data.images.remove(bpy.data.images[vBIName])

        light_exists = vLIName in bpy.data.images.keys()
        bg_exists = vBIName in bpy.data.images.keys()
        if not light_exists or not bg_exists:
            if not self.vSize:
                # Edge case that shouldn't occur as the resolution should be
                # explicit set, or just applying a local tex already,
                # but fallback if needed.
                vSize = cTB.vSettings["hdri"]

            vLSize = cTB.f_GetClosestSize(vAData["sizes"], vSize)

            vLTex = [vF for vF in vAData["files"]
                     if vLSize in os.path.basename(vF)
                     and vF.lower().endswith(".exr")]  # Permits .EXR too
            if not len(vLTex):
                vLTex = [vF for vF in vAData["files"]
                         if vLSize in os.path.basename(vF)
                         and vF.lower().endswith(".jpg")]  # Permits .JPG too

            if not len(vLTex):
                cTB.f_GetLocalAssets()  # Refresh local assets data structure.
                msg = f"Unable to locate image {vLIName} with size {vLSize}"
                reporting.capture_message("failed_load_light_hdri", msg)
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
            vLTex = vLTex[0]

            vBSize = cTB.f_GetClosestSize(vAData["sizes"], vSize)

            vBTex = [vF for vF in vAData["files"]
                     if vBSize in os.path.basename(vF)
                     and vF.lower().endswith(".jpg")]  # Permits .JPG too

            if not len(vBTex):
                cTB.f_GetLocalAssets()  # Refresh local assets data structure.
                msg = f"Unable to locate image {vBIName} with size {vBSize}"
                reporting.capture_message("failed_load_bg_hdri", msg)
                self.report({"ERROR"}, msg)
                reporting.capture_message("hdr_file_not_found", msg, 'info')
                return {"CANCELLED"}
            vBTex = vBTex[0]

        # ...............................................................................................

        vTCoordNode = None
        vMapNode = None

        vEnvNodeL = None
        vBGNodeL = None

        vEnvNodeB = None
        vBGNodeB = None

        vMixNode = None
        vLightNode = None

        vWorldNode = None

        if not bpy.context.scene.world:
            bpy.ops.world.new()
            bpy.context.scene.world = bpy.data.worlds[-1]

        context.scene.world.use_nodes = True

        vWNodes = context.scene.world.node_tree.nodes
        vWLinks = context.scene.world.node_tree.links
        for vN in vWNodes:
            if vN.type == "TEX_COORD":
                if vN.label == "Mapping":
                    vTCoordNode = vN

            elif vN.type == "MAPPING":
                if vN.label == "Mapping":
                    vMapNode = vN

            elif vN.type == "TEX_ENVIRONMENT":
                if vN.label == "Lighting":
                    vEnvNodeL = vN
                elif vN.label == "Background":
                    vEnvNodeB = vN

            elif vN.type == "BACKGROUND":
                if vN.label == "Lighting":
                    vBGNodeL = vN
                elif vN.label == "Background":
                    vBGNodeB = vN
                elif len(vWNodes) == 2:
                    vBGNodeL = vN
                    vBGNodeL.label = "Lighting"
                    vBGNodeL.location = mathutils.Vector((-110, 200))

            elif vN.type == "MIX_SHADER":
                vMixNode = vN

            elif vN.type == "LIGHT_PATH":
                vLightNode = vN

            elif vN.type == "OUTPUT_WORLD":
                vWorldNode = vN

        if vTCoordNode is None:
            vTCoordNode = vWNodes.new("ShaderNodeTexCoord")
            vTCoordNode.label = "Mapping"
            vTCoordNode.location = mathutils.Vector((-1080, 420))

        if vMapNode is None:
            vMapNode = vWNodes.new("ShaderNodeMapping")
            vMapNode.label = "Mapping"
            vMapNode.location = mathutils.Vector((-870, 420))

        if vEnvNodeL is None:
            vEnvNodeL = vWNodes.new("ShaderNodeTexEnvironment")
            vEnvNodeL.label = "Lighting"
            vEnvNodeL.location = mathutils.Vector((-470, 420))

        if vEnvNodeB is None:
            vEnvNodeB = vWNodes.new("ShaderNodeTexEnvironment")
            vEnvNodeB.label = "Background"
            vEnvNodeB.location = mathutils.Vector((-470, 100))

        if vBGNodeL is None:
            vBGNodeL = vWNodes.new("ShaderNodeBackground")
            vBGNodeL.label = "Lighting"
            vBGNodeL.location = mathutils.Vector((-110, 200))

        if vBGNodeB is None:
            vBGNodeB = vWNodes.new("ShaderNodeBackground")
            vBGNodeB.label = "Background"
            vBGNodeB.location = mathutils.Vector((-110, 70))

        if vMixNode is None:
            vMixNode = vWNodes.new("ShaderNodeMixShader")
            vMixNode.location = mathutils.Vector((110, 300))

        if vLightNode is None:
            vLightNode = vWNodes.new("ShaderNodeLightPath")
            vLightNode.location = mathutils.Vector((-110, 550))

        vWLinks.new(vTCoordNode.outputs["Generated"], vMapNode.inputs["Vector"])
        vWLinks.new(vMapNode.outputs["Vector"], vEnvNodeL.inputs["Vector"])
        vWLinks.new(vEnvNodeL.outputs["Color"], vBGNodeL.inputs["Color"])
        vWLinks.new(vBGNodeL.outputs[0], vMixNode.inputs[1])

        vWLinks.new(vTCoordNode.outputs["Generated"], vMapNode.inputs["Vector"])
        vWLinks.new(vMapNode.outputs["Vector"], vEnvNodeB.inputs["Vector"])
        vWLinks.new(vEnvNodeB.outputs["Color"], vBGNodeB.inputs["Color"])
        vWLinks.new(vBGNodeB.outputs[0], vMixNode.inputs[2])

        vWLinks.new(vLightNode.outputs[0], vMixNode.inputs[0])

        vWLinks.new(vMixNode.outputs[0], vWorldNode.inputs[0])

        if vLIName in bpy.data.images.keys():
            vImageL = bpy.data.images[vLIName]

        else:
            vImageL = bpy.data.images.load(vLTex)
            vImageL.name = vLIName
            vImageL.poliigon = "HDRIs;" + vAsset

        if vBIName in bpy.data.images.keys():
            vImageB = bpy.data.images[vBIName]

        else:
            vImageB = bpy.data.images.load(vBTex)
            vImageB.name = vBIName

        vEnvNodeL.image = vImageL

        vEnvNodeB.image = vImageB

        cTB.signal_import_asset(asset_id=vAData.get("id", 0))
        return {"FINISHED"}


# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


class POLIIGON_OT_brush(Operator):
    bl_idname = "poliigon.poliigon_brush"
    bl_label = ""
    bl_description = "Import Brush"
    bl_options = {"GRAB_CURSOR", "BLOCKING", "REGISTER", "INTERNAL", "UNDO"}

    vTooltip: StringProperty(options={"HIDDEN"})
    vAsset: StringProperty(options={"HIDDEN"})
    vSize: StringProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    @reporting.handle_operator()
    def execute(self, context):
        global cTB

        vAsset = self.vAsset
        vSize = self.vSize

        cTB.reset_asset_error(asset_name=vAsset)

        if vSize == "apply":
            vTex = cTB.vAssets["imported"]["Brushes"][vAsset].filepath

            vIName = cTB.vAssets["imported"]["Brushes"][vAsset].name

        else:
            vAData = cTB.vAssets["my_assets"]["Brushes"][vAsset]

            vTex = [vF for vF in vAData["files"] if vSize in os.path.basename(vF)]

            if not len(vTex):
                return {"FINISHED"}

            vTex = vTex[0]

            vIName = os.path.basename(vTex)

        # ...............................................................................................

        vName = f_FName(vTex)

        if "Poliigon" in bpy.data.textures.keys():
            vTexture = bpy.data.textures["Poliigon"]
        else:
            vTexture = bpy.data.textures.new("Poliigon", "IMAGE")

        if vName in bpy.data.images.keys():
            vImage = bpy.data.images[vName]
        else:
            vImage = bpy.data.images.load(vTex)
            vImage.name = vName

        vImage.poliigon = "Brushes;" + vAsset

        vTexture.image = vImage

        if "Poliigon" in bpy.data.brushes:
            vBrush = bpy.data.brushes["Poliigon"]
        else:
            vBrush = bpy.data.brushes.new("Poliigon")
            vBrush.strength = 0.3
            vBrush.blend = "MIX"
            vBrush.texture_slot.map_mode = "VIEW_PLANE"
            vBrush.stroke_method = "AIRBRUSH"

        vBrush.texture = vTexture

        cTB.f_GetSceneAssets()

        valid_context = context.object and context.object.type == "MESH"
        if valid_context:
            if context.mode not in ["SCULPT"]:
                bpy.ops.sculpt.sculptmode_toggle()

            for vA in context.screen.areas:
                if vA.type == "PROPERTIES":
                    for vR in vA.spaces:
                        if vR.type == "PROPERTIES":
                            vR.context = "TOOL"

            context.tool_settings.sculpt.brush = vBrush
            context.tool_settings.sculpt.use_symmetry_x = False
            context.tool_settings.unified_paint_settings.size = 200
        else:
            msg = (
                "Select a mesh object first to activate sculpt mode "
                "with this brush."
            )
            self.report({"INFO"}, msg)

        cTB.signal_import_asset(asset_id=vAData.get("id", 0))
        return {"FINISHED"}


class POLIIGON_OT_show_preferences(bpy.types.Operator):
    """Open user preferences and display Poliigon settings"""
    bl_idname = "poliigon.open_preferences"
    bl_label = "Show Poliigon preferences"

    @reporting.handle_operator()
    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_AREA')
        bpy.data.window_managers["WinMan"].addon_search = "Poliigon Addon"
        prefs = context.preferences
        try:
            prefs.active_section = "ADDONS"
        except TypeError as err:
            reporting.capture_message(
                "assign_preferences_tab", str(err), 'error')

        addons_ids = [
            mod for mod in addon_utils.modules(refresh=False)
            if mod.__name__ == __package__]
        if not addons_ids:
            msg = "Failed to directly load and open Poliigon preferences"
            reporting.capture_message(
                "preferences_open_no_id", msg, 'error')
            return {'CANCELLED'}

        addon_blinfo = addon_utils.module_bl_info(addons_ids[0])
        if not addon_blinfo["show_expanded"]:
            has_prefs = hasattr(bpy.ops, "preferences")
            has_prefs = has_prefs and hasattr(bpy.ops.preferences, "addon_expand")

            if has_prefs:  # later 2.8 buids
                bpy.ops.preferences.addon_expand(module=__package__)
            else:
                self.report(
                    {"INFO"},
                    "Search for and expand the Poliigon addon in preferences")

        cTB.track_screen("settings")
        return {'FINISHED'}


class POLIIGON_OT_close_notification(Operator):
    bl_idname = "poliigon.close_notification"
    bl_label = ""
    bl_description = "Close notification"
    bl_options = {"INTERNAL"}

    notification_index: IntProperty(options={"HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return "Close notification"  # Avoids having an extra blank line.

    @reporting.handle_operator()
    def execute(self, context):
        if self.notification_index < 0:
            self.report(
                {'ERROR'},
                f"Invalid notification index {self.notification_index} to dismiss.")
            return {'CANCELLED'}
        if len(cTB.notifications) <= self.notification_index:
            self.report(
                {'ERROR'}, "Could not dismiss notificaiton, out of bounds.")
            return {'CANCELLED'}
        cTB.dismiss_notification(notification_index=self.notification_index)
        return {'FINISHED'}


class POLIIGON_OT_report_error(Operator):
    bl_idname = "poliigon.report_error"
    bl_label = "Report error"
    bl_description = "Report an error to the developers"
    bl_options = {"INTERNAL"}

    error_report: StringProperty(options={"HIDDEN"})
    user_message: StringProperty(
        default="",
        maxlen=USER_COMMENT_LENGTH,
        options={'SKIP_SAVE'})

    target_width = 600

    def invoke(self, context, event):
        width = self.target_width  # Blender handles scaling to ui.
        return context.window_manager.invoke_props_dialog(self, width=width)

    @reporting.handle_draw()
    def draw(self, context):
        layout = self.layout

        # Display the error message (no word wrapping in case too long)
        box = layout.box()
        box.scale_y = 0.5
        box_wrap = self.target_width * cTB.get_ui_scale()
        box_wrap -= 20 * cTB.get_ui_scale()
        lines = self.error_report.split("\n")
        if len(lines) > 10:  # Prefer the last few lines.
            lines = lines[-10:]
        for ln in lines:
            if not ln:
                continue
            box.label(text=ln)

        # Display instructions to submit a comment.
        label_txt = "(Optional) What were you doing when this error occurred?"
        target_wrap = self.target_width * cTB.get_ui_scale()
        target_wrap -= 10 * cTB.get_ui_scale()
        cTB.f_Label(target_wrap, label_txt, layout)
        layout.prop(self, "user_message", text="")

        cTB.f_Label(target_wrap, "Press OK to send report", layout)

    @reporting.handle_operator(silent=True)
    def execute(self, context):
        if bpy.app.background:  # No user to give feedback anyways.
            return {'CANCELLED'}
        reporting.user_report(self.error_report, self.user_message)
        self.report({"INFO"}, "Thanks for sharing this report")
        return {'FINISHED'}


class POLIIGON_OT_check_update(Operator):
    bl_idname = "poliigon.check_update"
    bl_label = "Check for update"
    bl_description = "Check for any addon updates"
    bl_options = {"INTERNAL"}

    @reporting.handle_operator(silent=True)
    def execute(self, context):
        cTB.print_debug(0, "Started check for update with",
                        cTB.updater.addon_version,
                        cTB.updater.software_version)
        cTB.updater.async_check_for_update(callback=cTB.check_update_callback)
        cTB.print_debug(0, "Update ready?",
                        cTB.updater.update_ready, cTB.updater.update_data)

        return {'FINISHED'}


class POLIIGON_OT_refresh_data(Operator):
    bl_idname = "poliigon.refresh_data"
    bl_label = "Refresh data"
    bl_description = "Refresh and reload data"
    bl_options = {"INTERNAL"}

    @reporting.handle_operator(silent=True)
    def execute(self, context):
        cTB.refresh_data()
        return {'FINISHED'}


class POLIIGON_OT_popup_message(Operator):
    bl_idname = "poliigon.popup_message"
    bl_label = "User Message"
    bl_options = {"INTERNAL"}

    vTooltip: StringProperty(options={"HIDDEN"})
    message_body: StringProperty(options={"HIDDEN"})
    message_url: StringProperty(options={"HIDDEN"})

    target_width = 400

    @classmethod
    def description(cls, context, properties):
        return properties.vTooltip

    def invoke(self, context, event):
        width = self.target_width  # Blender handles scaling to ui.
        return context.window_manager.invoke_props_dialog(self, width=width)

    @reporting.handle_draw()
    def draw(self, context):
        layout = self.layout
        target_wrap = self.target_width * cTB.get_ui_scale()
        target_wrap -= 10 * cTB.get_ui_scale()
        cTB.f_Label(target_wrap, self.message_body, layout)

    @reporting.handle_operator(silent=True)
    def execute(self, context):
        if self.message_url:
            bpy.ops.wm.url_open(url=self.message_url)
        return {'FINISHED'}


classes = (
    POLIIGON_OT_setting,
    POLIIGON_OT_user,
    POLIIGON_OT_link,
    POLIIGON_OT_download,
    POLIIGON_OT_cancel_download,
    POLIIGON_OT_options,
    POLIIGON_OT_active,
    POLIIGON_OT_preset,
    POLIIGON_OT_texture,
    POLIIGON_OT_detail,
    POLIIGON_OT_folder,
    POLIIGON_OT_file,
    POLIIGON_OT_library,
    POLIIGON_OT_directory,
    POLIIGON_OT_category,
    POLIIGON_OT_preview,
    POLIIGON_OT_view_thumbnail,
    POLIIGON_OT_material,
    POLIIGON_OT_show_quick_menu,
    POLIIGON_OT_apply,
    POLIIGON_OT_model,
    POLIIGON_OT_select,
    POLIIGON_OT_hdri,
    POLIIGON_OT_brush,
    POLIIGON_OT_show_preferences,
    POLIIGON_OT_close_notification,
    POLIIGON_OT_report_error,
    POLIIGON_OT_check_update,
    POLIIGON_OT_refresh_data,
    POLIIGON_OT_popup_message,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
