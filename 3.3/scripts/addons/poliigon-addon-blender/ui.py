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

from datetime import datetime
import os
import platform
import re
import time

from bpy.types import Panel
import bpy

from . import reporting
from .toolbox import cTB, Notification
from .utils import *


def f_BuildUI(vUI, vContext):
    """Primary draw function used to build the main panel."""
    dbg = 0
    cTB.print_separator(dbg, "f_BuildUI")

    if cTB.check_if_working():
        bpy.context.window.cursor_set("WAIT")
    elif cTB.vWasWorking:
        # No longer working, reset cursor. It is important that this is the
        # only place that the vWasWorking var is reset.
        cTB.vWasWorking = False
        bpy.context.window.cursor_set("DEFAULT")

    # ...............................................................................................

    cTB.vUI = vUI
    cTB.vContext = vContext

    if not len(cTB.vAssets["imported"].keys()):
        cTB.f_GetSceneAssets()

    cTB.vBtns = []

    for vA in bpy.context.screen.areas:
        if vA.type == "VIEW_3D":
            for vR in vA.regions:
                if vR.type == "UI":
                    panel_padding = 15 * cTB.get_ui_scale()  # Left padding.
                    sidebar_width = 15 * cTB.get_ui_scale()  # Tabname width.

                    # Mac blender 3.x up seems to be reported wider than
                    # reality; it does not seem affected by UI scale or HDPI.
                    ex_pad = "mac" in platform.platform()
                    ex_pad = ex_pad or "darwin" in platform.platform()
                    ex_pad = ex_pad and bpy.app.version >= (3, 0)
                    if ex_pad:
                        sidebar_width += 17 * cTB.get_ui_scale()
                    vWidth = vR.width - panel_padding - sidebar_width
                    if vWidth != cTB.vWidth:
                        cTB.vWidth = vWidth
                        cTB.check_dpi()

    vSpc = 1.0 / cTB.vWidth

    vProps = bpy.context.window_manager.poliigon_props

    cTB.vSearch["poliigon"] = vProps.search_poliigon
    cTB.vSearch["my_assets"] = vProps.search_my_assets
    cTB.vSearch["imported"] = vProps.search_imported

    vArea = cTB.vSettings["area"]

    if cTB.vSearch[vArea] != cTB.vLastSearch:
        cTB.vPage[vArea] = 0
        cTB.vPages[vArea] = 0

        cTB.vInterrupt = time.time()
        cTB.f_GetAssets()

        cTB.vLastSearch = cTB.vSearch[vArea]

    vLayout = vUI.layout
    vLayout.alignment = "CENTER"

    vBaseRow = vLayout.row()

    cTB.vBase = vBaseRow.column()

    # NOTIFY ..................................................................

    f_NotificationBanner(cTB.notifications, cTB.vBase)

    # LOGIN ...................................................................

    if not cTB.is_logged_in():
        f_BuildLogin(cTB)
        return

    # LIBRARY .................................................................

    if not f_Ex(cTB.vSettings["library"]) or cTB.vWorking["startup"]:
        f_BuildLibrary(cTB)

        return

    # AREAS ...................................................................

    cTB.print_debug(dbg, "f_BuildUI", "f_BuildAreas")
    f_BuildAreas(cTB)

    # Credit balance ..........................................................

    split_fac = 1.0 - (70.0 / cTB.vWidth * cTB.get_ui_scale())
    vSplit = cTB.vBase.split(factor=split_fac)

    vSplit.label(text=cTB.vUser["name"])

    vOpCredits = vSplit.operator(
        "poliigon.poliigon_setting",
        text=str(cTB.vUser["credits"] + cTB.vUser["credits_od"]) + " C",
    )
    vOpCredits.vTooltip = "Total Credit Balance: " + str(
        cTB.vUser["credits"] + cTB.vUser["credits_od"]
    )
    vOpCredits.vMode = "show_user"

    cTB.vBase.separator()

    # USER ....................................................................

    if cTB.vSettings["show_user"]:
        f_BuildUser(cTB)
        return

    # SEARCH ..................................................................

    vRow = cTB.vBase.row()

    vRow1 = vRow.row(align=1)

    # NEED SEPARATE PROPS FOR SPECIFIC DESCRIPTIONS

    vRow1.prop(vProps, f"search_{cTB.vSettings['area']}", icon="VIEWZOOM")

    vShowX = 0
    if vArea == 'poliigon' and len(vProps.search_poliigon):
        vShowX = 1
    elif vArea == 'my_assets' and len(vProps.search_my_assets):
        vShowX = 1
    elif vArea == 'imported' and len(vProps.search_imported):
        vShowX = 1

    if vShowX:
        vOp = vRow1.operator(
            "poliigon.poliigon_setting",
            text="",
            icon="X",
        )
        vOp.vTooltip = "Clear Search"
        vOp.vMode = f"clear_search_{cTB.vSettings['area']}"

    # ASSET LIST ...............................................................................................

    cTB.vActiveCat = cTB.vSettings["category"][vArea]

    cTB.vAssetType = cTB.vActiveCat[0]

    # ACTIVE ASSET ...............................................................................................
    
    # ADVANCED SETTINGS
    """
    if vArea == "imported":
        f_BuildActive(cTB)
    """
    
    # GO TOP ...............................................................................................
    
    # This is used to force the UI back to the top if necessary - must be a better way???
    """
    if cTB.vGoTop:
       if vDBG : print(vDBGi,'Go Top')
       cTB.vGoTop = 0
       return
    """

    # CATEGORY ...............................................................................................

    cTB.print_debug(dbg, "f_BuildUI", "f_BuildCategories")
    f_BuildCategories(cTB)

    # ASSETS ...............................................................................................

    cTB.print_debug(dbg, "f_BuildUI", "f_BuildAssets")
    f_BuildAssets(cTB)


# .............................................................................
# Draw utilities
# .............................................................................


#@timer
def f_BuildLogin(cTB):
    dbg = 0
    cTB.print_separator(dbg, "f_BuildLogin")

    vSpc = 1.0 / cTB.vWidth

    vProps = bpy.context.window_manager.poliigon_props

    if cTB.vLoginError:
        cTB.vWorking["login"] = 0

    # ...............................................................................................

    if cTB.user_invalidated():
        cTB.vBase.separator()

        cTB.f_Label(
            cTB.vWidth,
            "Warning : You have been logged out as this account was signed in on another device.",
            cTB.vBase,
            vIcon="ERROR",
        )

    else:
        cTB.f_Label(
            cTB.vWidth,
            "Welcome to the Poliigon Addon!",
            cTB.vBase,
        )

        cTB.vBase.separator()

        cTB.f_Label(
            cTB.vWidth,
            "Log in below to get started.",
            cTB.vBase,
        )

    cTB.vBase.separator()

    # ...............................................................................................

    vBRow = cTB.vBase.box().row()
    vBRow.separator(factor=vSpc)
    vCol = vBRow.column()
    vBRow.separator(factor=vSpc)

    # ...............................................................................................

    vCol.label(text="Email")

    vRow = vCol.row(align=1)
    
    vRow.prop(vProps, "vEmail")
    
    vXCol = vRow.column(align=1)
    #vXCol.enabled = len(vProps.vEmail) > 0

    vOp = vXCol.operator(
        "poliigon.poliigon_setting",
        text="",
        icon="X",
    )
    vOp.vTooltip = "Clear Email"
    vOp.vMode = "clear_email"
    
    vEr = 0

    if cTB.vLoginError and "@" not in vProps.vEmail:
        vEr = 1

        vCol.separator()
        
        cTB.f_Label(
            cTB.vWidth - 40 * cTB.get_ui_scale(),
            "Email format is invalid e.g. john@example.org",
            vCol,
            vIcon="ERROR",
        )

    vCol.separator()

    # ...............................................................................................

    vCol.label(text="Password")

    vRow = vCol.row(align=1)

    if cTB.vSettings["show_pass"]:
        vRow.prop(vProps, "vPassShow")
        vPass = vProps.vPassShow

    else:
        vRow.prop(vProps, "vPassHide")
        vPass = vProps.vPassHide

    vXCol = vRow.column(align=1)

    vOp = vXCol.operator(
        "poliigon.poliigon_setting",
        text="",
        icon="X",
    )
    vOp.vTooltip = "Clear Password"
    vOp.vMode = "clear_pass"

    # If we're not going to use this, then we can remove the vPassShow property.
    # vPassOp = vRow.operator("poliigon.poliigon_setting", text="", icon=(
    #     "HIDE_OFF" if cTB.vSettings["show_pass"] else "HIDE_ON"))
    # vPassOp.vMode = "show_pass"

    if cTB.vLoginError and len(vPass) < 6:
        vEr = 1

        vCol.separator()

        cTB.f_Label(
            cTB.vWidth - 40 * cTB.get_ui_scale(),
            "Password should be at least 6 characters.",
            vCol,
            vIcon="ERROR",
        )

    vCol.separator()

    # ...............................................................................................

    vEn = len(vProps.vEmail) > 0 and len(vPass) > 0

    # Show terms of service, optin/out.
    opt_row = vCol.row()
    opt_row.alignment = "LEFT"
    prefs = bpy.context.preferences.addons.get(__package__, None)
    opt_row.prop(prefs.preferences, "reporting_opt_in", text="")
    twidth = cTB.vWidth - 42 * cTB.get_ui_scale()
    cTB.f_Label(twidth, "Share addon errors / usage", opt_row)

    vRow = vCol.row()
    vRow.scale_y = 1.25

    if cTB.vWorking["login"]:
        vLoginOp = vRow.operator(
            "poliigon.poliigon_setting", text="Logging In...", depress=vEn
        )
        vLoginOp.vMode = "none"
        vLoginOp.vTooltip = "Logging In..."
        vRow.enabled = False
    else:
        vLoginOp = vRow.operator("poliigon.poliigon_user", text="Log In")
        vLoginOp.vMode = "login"
        vLoginOp.vTooltip = "Log In"

        vRow.enabled = vEn

    # ...............................................................................................
    if cTB.vLoginError == cTB.ERR_CREDS_FORMAT:
        # Will draw above with more specific messages if condition true, like
        # invalid email format or password length.
        pass
    elif cTB.vLoginError and not vEr:
        vCol.separator()

        cTB.f_Label(
            cTB.vWidth - 40 * cTB.get_ui_scale(),
            cTB.vLoginError,
            vCol,
            vIcon="ERROR",
        )

    vCol.separator()

    # ...............................................................................................

    vForgotOp = vCol.operator(
        "poliigon.poliigon_link", text="Forgot Password?", emboss=False
    )
    vForgotOp.vMode = "forgot"
    vForgotOp.vTooltip = "Reset your Poliigon password"

    # ...............................................................................................

    cTB.vBase.separator()

    cTB.f_Label(
        cTB.vWidth,
        "Don't have an account?",
        cTB.vBase,
    )

    vSignupOp = cTB.vBase.operator("poliigon.poliigon_link", text="Sign Up")
    vSignupOp.vMode = "signup"
    vSignupOp.vTooltip = "Create a Poliigon account"

    cTB.vBase.separator()

    row = cTB.vBase.row()
    col = row.column(align=True)

    vTermsOp = col.operator(
        "poliigon.poliigon_link", text="Terms & Conditions", emboss=False)
    vTermsOp.vTooltip = "View the terms and conditions page"
    vTermsOp.vMode = "terms"

    vPrivacyOp = col.operator(
        "poliigon.poliigon_link", text="Privacy Policy", emboss=False)
    vPrivacyOp.vTooltip = "View the Privacy Policy "
    vPrivacyOp.vMode = "privacy"


#@timer
def f_BuildLibrary(cTB):
    dbg = 0
    cTB.print_separator(dbg, "f_BuildLibrary")
    vSpc = 1.0 / cTB.vWidth

    # ...............................................................................................

    cTB.f_Label(
        cTB.vWidth,
        "Welcome to the Poliigon Addon!",
        cTB.vBase,
    )

    cTB.vBase.separator()

    cTB.f_Label(
        cTB.vWidth,
        "Select where you will store Poliigon assets.",
        cTB.vBase,
    )

    cTB.vBase.separator()

    # ...............................................................................................

    vBRow = cTB.vBase.box().row()
    vBRow.separator(factor=vSpc)
    vCol = vBRow.column()
    vBRow.separator(factor=vSpc)

    # ...............................................................................................

    vCol.label(text="Library Location")

    vLbl = cTB.vSettings["set_library"]
    if vLbl == "":
        vLbl = "Select Location"

    vOp = vCol.operator(
        "poliigon.poliigon_library",
        icon="FILE_FOLDER",
        text=vLbl,
    )
    vOp.vMode = "set_library"
    vOp.directory = cTB.vSettings["set_library"]
    vOp.vTooltip = "Select Location"

    vCol.separator()
    vConformRow = vCol.row()
    vConformRow.scale_y = 1.5

    if cTB.vWorking["startup"]:
        vOp = vConformRow.operator(
            "poliigon.poliigon_setting", text="Confirming...", depress=1
        )
        vOp.vMode = "none"
        vOp.vTooltip = "Confirming Library Location..."
        vConformRow.enabled = False
    else:
        vOp = vConformRow.operator("poliigon.poliigon_setting", text="Confirm")
        vOp.vMode = "set_library"
        vOp.vTooltip = "Confirm Library location"

    vCol.separator()

    # ...............................................................................................

    cTB.f_Label(
        cTB.vWidth - 30 * cTB.get_ui_scale(),
        "You can change this and add more directories in the settings at any time.",
        vCol,
    )

    vCol.separator()

    # ...............................................................................................

    cTB.vBase.separator()

    cTB.vWorking["startup"] = False


#@timer
def f_BuildUser(cTB):
    dbg = 0
    cTB.print_separator(dbg, "f_BuildUser")

    vSpc = 1.0 / cTB.vWidth

    # YOUR CREDITS ............................................................

    vBox = cTB.vBase.box()

    vOp = vBox.operator(
        "poliigon.poliigon_setting",
        text="Your Credits    ",
        icon="DISCLOSURE_TRI_DOWN"
        if cTB.vSettings["show_credits"]
        else "DISCLOSURE_TRI_RIGHT",
        emboss=0,
    )
    vOp.vMode = "show_credits"
    if cTB.vSettings["show_credits"]:
        vOp.vTooltip = "Hide Your Credits"
    else:
        vOp.vTooltip = "Show Your Credits"

    if cTB.vSettings["show_credits"]:
        vBRow = vBox.row()
        vBRow.separator(factor=vSpc)
        vCol = vBRow.column()
        vBRow.separator(factor=vSpc)

        if cTB.vUser["credits"] + cTB.vUser["credits_od"] == 0:
            vCol.label(text="0 Credits")

        else:
            cTB.f_Label(
                cTB.vWidth - 40 * cTB.get_ui_scale(),
                "Subscription!@#Credits!@#: " + str(cTB.vUser["credits"]),
                vCol,
            )

            cTB.f_Label(
                cTB.vWidth - 40 * cTB.get_ui_scale(),
                "On!@#Demand!@#Credits!@#: " + str(cTB.vUser["credits_od"]),
                vCol,
            )

        # View how many credits to expect in certian number of days.
        if cTB.vUser["plan_name"]:
            next_credits = cTB.vUser["plan_next_credits"]
            amount = cTB.vUser["plan_credit"]
            try:
                dt = datetime.strptime(next_credits, "%Y-%m-%d")
            except ValueError:
                dt = None

            amount = cTB.vUser["plan_credit"]
            now = datetime.now()

            # Compute diffs only on overall day.
            if dt is not None:
                now = now.replace(hour=0, minute=0, second=0, microsecond=0)
                dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)

                diff = dt - now
                in_days = diff.days

                if in_days >= 0:
                    cTB.f_Label(
                        cTB.vWidth - 40 * cTB.get_ui_scale(),
                        f"+{amount} in {in_days} days",
                        vCol)

        vCol.separator()

        vOp = vCol.operator("poliigon.poliigon_link", text="Add Credits", depress=1)
        vOp.vMode = "credits"
        vOp.vTooltip = "Add more Credits to your account"

        vCol.separator()

    cTB.vBase.separator()

    # YOUR PLAN ...............................................................

    vBox = cTB.vBase.box()

    vOp = vBox.operator(
        "poliigon.poliigon_setting",
        text="Your Plan     ",
        icon="DISCLOSURE_TRI_DOWN"
        if cTB.vSettings["show_plan"]
        else "DISCLOSURE_TRI_RIGHT",
        emboss=0,
    )
    vOp.vMode = "show_plan"
    if cTB.vSettings["show_plan"]:
        vOp.vTooltip = "Hide Your Plan Details"
    else:
        vOp.vTooltip = "Show Your Plan Details"

    if cTB.vSettings["show_plan"]:
        vBRow = vBox.row()
        vBRow.separator(factor=vSpc)
        vCol = vBRow.column()
        vBRow.separator(factor=vSpc)

        vCol.separator()

        if not cTB.vUser["plan_name"]:
            cTB.f_Label(
                cTB.vWidth - 20 * cTB.get_ui_scale(),
                "Subscribe to a Poliigon Plan and start downloading assets.",
                vCol,
            )

            vCol.separator()

            vOp = vCol.operator("poliigon.poliigon_link", text="Subscribe Now")
            vOp.vMode = "subscribe"
            vOp.vTooltip = "Start a Poliigon subscription"

        else:
            plan_name = cTB.vUser["plan_name"]

            cTB.f_Label(
                cTB.vWidth - 40 * cTB.get_ui_scale(),
                f"Plan: {plan_name}",
                vCol)

            next_renew = cTB.vUser["plan_next_renew"]
            cTB.f_Label(
                cTB.vWidth - 40 * cTB.get_ui_scale(),
                f"(Renews on {next_renew})",
                vCol)

            vCol.separator()

            credits = cTB.vUser["plan_credit"]
            cTB.f_Label(
                cTB.vWidth - 40 * cTB.get_ui_scale(),
                f"Monthly Credits : {credits}",
                vCol)

            vCol.separator()

            vOp = vCol.operator("poliigon.poliigon_link", text="Change Plan")
            vOp.vMode = "credits"
            vOp.vTooltip = "Change your Poliigon Plan Online"

        vCol.separator()

        cTB.vBase.separator()

    vOp = cTB.vBase.operator("poliigon.poliigon_user", text="Log Out")
    vOp.vMode = "logout"
    vOp.vTooltip = "Log Out of Poliigon"


#@timer
def f_BuildAreas(cTB):
    dbg = 0
    cTB.print_separator(dbg, "f_BuildAreas")
    cTB.initial_view_screen()

    vRow = cTB.vBase.row(align=True)
    vRow.scale_x = 1.1
    vRow.scale_y = 1.1

    vDep = not cTB.vSettings["show_user"] and not cTB.vSettings["show_settings"]

    vLbl = " ".join([vS.capitalize() for vS in cTB.vSettings["area"].split("_")])
    if cTB.vSettings["show_settings"]:
        vLbl = "Settings"
    elif cTB.vSettings["show_user"]:
        vLbl = "My Account"
    vRow.label(text=vLbl)

    vCol = vRow.column(align=True)
    vDep1 = cTB.vSettings["area"] == "poliigon"
    vOp = vCol.operator(
        "poliigon.poliigon_setting",
        text="",
        icon_value=cTB.vIcons["ICON_poliigon"].icon_id,
        depress=vDep1 and vDep,
    )
    vOp.vMode = "area_poliigon"
    vOp.vTooltip = "Show Poliigon Assets"

    vCol = vRow.column(align=True)
    vDep1 = cTB.vSettings["area"] == "my_assets"
    vOp = vCol.operator(
        "poliigon.poliigon_setting",
        text="",
        icon_value=cTB.vIcons["ICON_myassets"].icon_id,
        depress=vDep1 and vDep,
    )
    vOp.vMode = "area_my_assets"
    vOp.vTooltip = "Show My Assets"

    vCol = vRow.column(align=True)
    vDep1 = cTB.vSettings["area"] == "imported"
    vOp = vCol.operator(
        "poliigon.poliigon_setting",
        text="",
        icon="OUTLINER_OB_GROUP_INSTANCE",
        depress=vDep1 and vDep,
    )
    vOp.vMode = "area_imported"
    vOp.vTooltip = "Show Imported Assets"

    vOp = vRow.operator(
        "poliigon.poliigon_setting",
        text="",
        icon="COMMUNITY",
        depress=cTB.vSettings["show_user"],
    )
    vOp.vMode = "my_account"
    vOp.vTooltip = "Show Your Account Details"

    vSRow = vRow.row(align=False)
    vOp = vSRow.operator(
        "poliigon.open_preferences",
        text="",
        icon="PREFERENCES",
    )

    cTB.vBase.separator()


#@timer
def f_BuildCategories(cTB):
    dbg = 0
    cTB.print_separator(dbg, "f_BuildCategories")

    vSpc = 1.0 / cTB.vWidth

    vCats = []
    vCategories = []
    vSubs = []
    if cTB.vAssetType != "All Assets":
        for vType in cTB.vCategories["poliigon"].keys():
            if cTB.vAssetType in ["All Assets", vType]:
                vCategories += cTB.vCategories["poliigon"][vType].keys()
        vCategories = sorted(list(set(vCategories)))

        if len(vCategories):
            vCategory = ""
            vCats = []
            for i in range(1, len(cTB.vActiveCat)):
                vCategory += "/" + cTB.vActiveCat[i]
                vCats.append(vCategory)

            vSubs = [
                vC.split("/")[-1]
                for vC in vCategories
                if vC.startswith(vCategory) and vC != vCategory
            ]
            if len(vSubs):
                vCats.append("sub")

    gCatsCol = cTB.vBase.column()

    width_factor = len(vCats) + 1
    if cTB.vWidth >= max(width_factor, 2) * 160 * cTB.get_ui_scale():
        vRow = gCatsCol.row()
    else:
        vRow = gCatsCol

    vRow1 = vRow.row(align=True)

    vTypes = ["All Assets", "Textures", "Models", "HDRIs", "Brushes"]

    vOp = vRow1.operator(
        "poliigon.poliigon_category", text=cTB.vAssetType, icon="TRIA_DOWN"
    )
    vOp.vData = "0@" + "@".join(vTypes)

    if vCats:
        for i in range(len(vCats)):
            vCat = vCats[i]

            vRow1 = vRow.row(align=1)

            if i == 0:
                vSCats = [
                    vC.split("/")[-1]
                    for vC in vCategories
                    if len(vC.split("/")) == 2
                ]
            elif vCat == "sub":
                vSCats = vSubs
            else:
                vPCat = "/".join(vCat.split("/")[:-1])
                vSCats = [
                    vC.split("/")[-1]
                    for vC in vCategories
                    if vC.startswith(vPCat) and vC != vPCat
                ]

            vSCats = sorted(list(set(vSCats)))

            vLbl = vCat.split("/")[-1]
            if vCat == "sub":
                vLbl = "All " + cTB.vActiveCat[-1]

            vSCats.insert(0, "All " + cTB.vActiveCat[i])
            vData = str(i + 1) + "@" + "@".join(vSCats)

            vOp = vRow1.operator(
                "poliigon.poliigon_category", text=vLbl, icon="TRIA_DOWN"
            )
            vOp.vData = vData

    gCatsCol.separator()


#@timer
def f_BuildAssets(cTB):
    dbg = 0
    cTB.print_separator(dbg, "f_BuildAssets")

    if not cTB.vCheckScale:
        cTB.check_dpi()

        cTB.vCheckScale = 1
    
    vArea = cTB.vSettings["area"]    
    vPage = cTB.vPage[vArea]
    vNotFoundBox = None

    # .....................................................................

    vSortedAssets = cTB.f_GetAssetsSorted(vPage)

    cTB.print_debug(dbg, "vSortedAssets", len(vSortedAssets))

    # .....................................................................

    vSpc = 1.0 / cTB.vWidth

    category = cTB.vActiveCat[0].replace("All ", "")
    if len(cTB.vActiveCat) > 1:
        category = f"{cTB.vActiveCat[-1]} {category}"

    if not len(vSortedAssets):
        vNotFoundBox = cTB.vBase.box()

        vLbl = f"No Poliigon {category} found in Library"
        if cTB.vSearch[vArea] != "":
            vLbl = (
                "No results found."
                " Please try changing your filter or search term."
            )
        elif vArea == "imported":
            vLbl = f"No Poliigon {category} found in the Scene"
        elif vArea == "poliigon":
            vLbl = f"No Poliigon {category} found Online"

        cTB.f_Label(cTB.vWidth - 20 * cTB.get_ui_scale(), vLbl, vNotFoundBox, vAddPadding=True)   

    else:
        if cTB.vSettings["preview_size"] == 3:
            vGrid = cTB.vBase.column()

        else:
            if cTB.vSettings["preview_size"] == 5:
                vBWidth = 130
            elif cTB.vSettings["preview_size"] == 7:
                vBWidth = 170
            vBWidth *= cTB.get_ui_scale()

            vCols = int(cTB.vWidth / vBWidth)
            if vCols == 0:
                vCols = 1
            if vCols > len(vSortedAssets):
                vCols = len(vSortedAssets)

            vPad = (cTB.vWidth - (vCols * vBWidth)) / 2
            if vPad < 1.0 and vCols > 1:
                vCols -= 1
                vPad = (cTB.vWidth - (vCols * vBWidth)) / 2

            if vPad < 1.0 or vBWidth + 1 > cTB.vWidth:
                # Panel is narrower than a single preview width, single col.
                vGrid = cTB.vBase.grid_flow(
                    row_major=True, columns=vCols,
                    even_columns=True, even_rows=True, align=0
                )

            else:
                # Typical case, fit rows and columns.
                vFct = vPad / cTB.vWidth
                vSplit = cTB.vBase.split(factor=vFct)

                vSplit.separator()

                vFct = (cTB.vWidth - vPad - vPad) / (cTB.vWidth - vPad)
                vSplit1 = vSplit.split(factor=vFct)

                vGrid = vSplit1.grid_flow(
                    row_major=True, columns=vCols,
                    even_columns=True, even_rows=True, align=0
                )

                vSplit1.separator()

        vSel = bpy.context.selected_objects
        vIsSelection = len(vSel) > 0

        vSt = vPage * cTB.vSettings["page"]
        vEd = min(vSt + cTB.vSettings["page"], len(vSortedAssets))

        # Get Active Brush ...

        vBrush = None
        try:
            if bpy.context.tool_settings.sculpt.brush.name == "Poliigon":
                vBrush = bpy.context.tool_settings.sculpt.brush.texture.image.poliigon.split(
                    ";"
                )[
                    1
                ]
        except:
            pass

        # Build Asset Grid ...

        for i in range(len(vSortedAssets)):
            if i >= cTB.vSettings["page"]:
                break

            vAData = vSortedAssets[i]

            # See if there's any errors associated with this asset,
            # such as after or during download failure.
            errs = [
                err for err in cTB.ui_errors
                if vAData.get("id") and err.asset_id == vAData["id"]]
            error = errs[0] if errs else None
            del errs

            vSizes = vAData["sizes"]
            vSizesL = []

            if vAData["type"] in cTB.vAssets["local"].keys():
                if vAData["name"] in cTB.vAssets["local"][vAData["type"]].keys():
                    for vK in ["files", "lods"]:
                        vAData[vK] = cTB.vAssets["local"][vAData["type"]][vAData["name"]][vK]
                    
                    vSizesL = cTB.vAssets["local"][vAData["type"]][vAData["name"]]["sizes"]

            vBackplate = cTB.check_backplate(vAData["name"])

            cTB.f_GetPreview(vAData["name"])

            vDefSize = ""

            vCheckSizes = vSizes
            if len(vSizesL):
                vCheckSizes = vSizesL

            if len(vCheckSizes):
                if vAData["type"] == "Textures":
                    vDefSize = cTB.f_GetClosestSize(vCheckSizes, cTB.vSettings["res"])
                elif vAData["type"] == "Models":
                    vDefSize = cTB.f_GetClosestSize(vCheckSizes, cTB.vSettings["mres"])
                elif vAData["type"] == "HDRIs":
                    vDefSize = cTB.f_GetClosestSize(vCheckSizes, cTB.vSettings["hdri"])
                elif vAData["type"] == "Brushes":
                    vDefSize = cTB.f_GetClosestSize(vCheckSizes, cTB.vSettings["brush"])

            vCrdts = vAData["credits"]

            if cTB.vSettings["preview_size"] == 3:
                vFctr = 90 / cTB.vWidth

                vCell = vGrid.split(factor=vFctr, align=1)
            else:
                vCell = vGrid.column(align=1)

            vBox = vCell.box().column()

            # THUMBNAIL ...................................................

            if "THUMBNAIL":
                if vAData["name"] == "dummy":
                    vBox.template_icon(
                        icon_value=cTB.vIcons["GET_preview"].icon_id,
                        scale=cTB.vSettings["preview_size"],
                    )

                elif vAData["name"] in cTB.vPreviews.keys():
                    vBox.template_icon(
                        icon_value=cTB.vPreviews[vAData["name"]].icon_id,
                        scale=cTB.vSettings["preview_size"],
                    )

                    if vAData["name"] in cTB.vPreviewsDownloading:
                        cTB.vPreviewsDownloading.remove(vAData["name"])

                else:
                    if vAData["name"] in cTB.vPreviewsDownloading:
                        vBox.template_icon(
                            icon_value=cTB.vIcons["GET_preview"].icon_id,
                            scale=cTB.vSettings["preview_size"],
                        )

                        if f_Ex(vAData["preview"]):
                            if os.access(vAData["preview"], os.W_OK):
                                cTB.vPreviews.load(
                                    vAData["name"], vAData["preview"], "IMAGE"
                                )
                                cTB.vPreviewsDownloading.remove(vAData["name"])

                    else:
                        vBox.template_icon(
                            icon_value=cTB.vIcons["NO_preview"].icon_id,
                            scale=cTB.vSettings["preview_size"],
                        )

                        # if vArea == "poliigon":
                        cTB.f_GetPreview(vAData["name"])

            # .............................................................

            if cTB.vSettings["preview_size"] == 3:
                vCol = vCell.column(align=1)

                vIBox = vCol.box().column(align=1)

                vIBox.label(text=vAData["name"])

                vIBox.label(text="  ".join(vSizes))

                vRow = vCol.row(align=1)
            else:
                vRow = vCell.row(align=1)

            # DOWNLOADED ..................................................

            vDownloaded = False
            if vAData["type"] in cTB.vAssets["local"].keys():
                if vAData["name"] in cTB.vAssets["local"][vAData["type"]].keys():
                    vDownloaded = True

            # IN SCENE ....................................................
            
            vInScene = []
            if vAData["type"] in cTB.vAssets["imported"].keys():
                if vAData["name"] in cTB.vAssets["imported"][vAData["type"]].keys():
                    objlist = cTB.vAssets["imported"][vAData["type"]][vAData["name"]]
                    for i, obj in enumerate(objlist):
                        try:
                            vInScene.append(cTB.f_GetSize(obj.name))
                        except ReferenceError:
                            # Object was removed, so pop from the list.
                            cTB.vAssets["imported"][vAData["type"]][vAData["name"]].pop(i)
                        except AttributeError as err:
                            print("Failed to vInScene.append")
                            print(err)
                            # But continue to avoid complete UI breakage.
                    if vInScene and vDefSize not in vInScene and vInScene[0]:
                        vDefSize = vInScene[0]

            # LOADING .....................................................

            if vAData["name"] == "dummy":
                vOp = vRow.operator("poliigon.poliigon_setting", text="  ")
                vOp.vMode = "none"

            # PURCHASING ................................

            elif cTB.check_if_purchase_queued(vAData.get("id")):
                vOp = vRow.operator(
                    "poliigon.poliigon_setting",
                    text="Purchasing...",
                    emboss=1,
                    depress=1,
                )
                vOp.vMode = "none"
                vOp.vTooltip = "Purchasing..."

            # DOWNLOADING ................................

            elif cTB.check_if_download_queued(vAData.get("id")):
                download_data = cTB.vDownloadQueue[vAData['id']].copy()

                p = 0.01
                download_file = download_data.get('download_file', "")
                remaining_time = None
                if f_Ex(download_file):
                    if download_data.get("download_size") is not None:
                        file_size = os.path.getsize(download_file)
                        if file_size > 0:
                            p = (file_size / download_data["download_size"]) * 10
                            download_time = time.time() - os.path.getctime(download_file)
                            remaining_time = (download_time / file_size) * (download_data["download_size"] - file_size)
                            if remaining_time > 60*60 :
                                remaining_time = str(int(time.strftime('%H', time.gmtime(remaining_time)))) + 'h+'
                            elif remaining_time > 60 :
                                remaining_time = str(int(time.strftime('%M', time.gmtime(remaining_time)))) + 'm+'
                            elif remaining_time <= 60 :
                                remaining_time = str(int(time.strftime('%S', time.gmtime(remaining_time)))) + 's'

                elif f_Ex(os.path.join(cTB.vSettings["library"], vAData["name"] + ".zip")):
                    p = 10

                vRow.label(text="", icon="IMPORT")

                if remaining_time is not None:
                    vFct = 1.0 - ((35 * cTB.get_ui_scale()) / (vBWidth - 0))
                vCol = vRow.column()
                vCancelCol = vRow.column()
                # Display cancel button instead of time remaining.
                ops = vCancelCol.operator("poliigon.cancel_download",
                                          emboss=False, text="", icon="X")
                ops.asset_id = vAData["id"]

                vSpcT = vCol.row()
                vSpcT.scale_y = 0.2

                vSpcT.label(text="")

                vProg = vCol.row()
                vProg.scale_y = 0.4

                vSplit = vProg.split(factor=p / 10, align=1)

                vOp = vSplit.operator(
                    "poliigon.poliigon_setting", text="", emboss=1, depress=1
                )
                vOp.vMode = "none"
                vOp.vTooltip = f"Downloading {vAData['name']} @ {download_data['size']}..."

                vOp = vSplit.operator(
                    "poliigon.poliigon_setting", text="", emboss=1, depress=0
                )
                vOp.vMode = "none"
                vOp.vTooltip = f"Downloading {vAData['name']} @ {download_data['size']}..."

                vRow.separator()

            # DOWNLOADING QUICK PREVIEWS ................................

            elif vAData["name"] in cTB.vQuickPreviewQueue.keys():
                downloaded_files = [vF for vF in cTB.vQuickPreviewQueue[vAData["name"]] if f_Ex(vF)]
                p = len(downloaded_files) / len(cTB.vQuickPreviewQueue[vAData["name"]])

                vRow.label(text="", icon="IMPORT")

                vCol = vRow.column()

                vSpcT = vCol.row()
                vSpcT.scale_y = 0.2

                vSpcT.label(text="")

                vProg = vCol.row()
                vProg.scale_y = 0.4

                vSplit = vProg.split(factor=p / 10, align=1)

                vOp = vSplit.operator(
                    "poliigon.poliigon_setting", text="", emboss=1, depress=1
                )
                vOp.vMode = "none"
                vOp.vTooltip = "Downloading..."

                vOp = vSplit.operator(
                    "poliigon.poliigon_setting", text="", emboss=1, depress=0
                )
                vOp.vMode = "none"
                vOp.vTooltip = "Downloading..."

                vRow.separator()

                if p >= 9.9:
                    del cTB.vQuickPreviewQueue[vAData["name"]]
                    cTB.vRedraw = 1

            # ONLINE and MY ASSETS ............................................

            elif vArea in ["poliigon", "my_assets"]:

                # QUICK PREVIEW ................................

                if (
                    vAData["type"] == "Textures"
                    and vAData["name"] not in cTB.vPurchased
                ):
                    vShow = 0
                    if vBackplate and vAData["preview"] != "":
                        vShow = 1
                    elif len(vAData["quick_preview"]):
                        vShow = 1

                    if vShow:
                        vPRow = vRow.column(align=1)

                        vPRow.enabled = vIsSelection or vBackplate

                        vOp = vPRow.operator(
                            "poliigon.poliigon_preview",
                            text="",
                            icon="HIDE_OFF",
                            emboss=1,
                        )
                        vOp.vType = vAData["type"]
                        vOp.vAsset = vAData["name"]

                        if vIsSelection:
                            vOp.vTooltip = f'Preview {vAData["name"]} on Selected Object(s)'
                        else:
                            vOp.vTooltip = "Select an object to preview this texture"

                # ACQUIRED/IMPORTED CHECKMARK ................................

                elif vAData["name"] in cTB.vPurchased and vArea == "poliigon":
                    vPRow = vRow.column(align=1)
                    vPRow.enabled = False
                    icon_val = cTB.vIcons["ICON_acquired_check"].icon_id
                    vPRow.operator(
                        "poliigon.poliigon_setting",
                        text="",
                        icon_value=icon_val,
                        depress=False,
                        emboss=True
                    ).vTooltip = "Asset already acquired"

                # BUTTONS ................................

                asset_name = vAData["name"]
                asset_type = vAData["type"]
                if vAData["name"] in cTB.vPurchased:
                    if vDownloaded:

                        # MODELS ................................

                        if vAData["type"] == "Models":
                            if error:
                                icon = "ERROR"
                                label = error.button_label
                                lod = "default"
                                size = ""
                                tip = error.description
                            else:
                                if asset_type in cTB.vAssets["local"].keys():
                                    if asset_name in cTB.vAssets["local"][asset_type].keys():
                                        downloaded = cTB.vAssets["local"][asset_type][asset_name]["sizes"]

                                size = cTB.f_GetClosestSize(downloaded,
                                                            cTB.vSettings["mres"])

                                lod, label, tip = get_model_op_details(asset_name, asset_type, size)
                                label = "Import"
                                icon = "TRACKING_REFINE_BACKWARDS"

                            vOp = vRow.operator(
                                "poliigon.poliigon_model",
                                text=label,
                                icon=icon,
                            )
                            vOp.vAsset = asset_name
                            vOp.vSize = size
                            vOp.vTooltip = tip
                            vOp.vType = asset_type
                            vOp.vLod = lod

                        # TEXTURES ................................

                        elif vAData["type"] == "Textures":
                            vBtnRow = vRow.row(align=1)

                            vLbl = "Import " + vDefSize
                            vIcon = "TRACKING_REFINE_BACKWARDS"
                            vTTip = vAData["name"] + "\n(Import Material)"
                            if len(vInScene):
                                vBtnRow.enabled = vIsSelection
                                vLbl = "Apply " + vDefSize
                                vIcon = "TRACKING_REFINE_BACKWARDS"
                                vTTip = vAData["name"] + "\n(Apply Material)"
                            elif vIsSelection:
                                vLbl = "Apply " + vDefSize
                                vIcon = "TRACKING_REFINE_BACKWARDS"
                                vTTip = (
                                    vAData["name"]
                                    + "\n(Import + Apply Material)"
                                )

                            if error:
                                vOp = vBtnRow.operator(
                                    "poliigon.poliigon_material",
                                    text=error.button_label,
                                    icon="ERROR",
                                )
                                vOp.vTooltip = error.description
                            else:
                                vOp = vBtnRow.operator(
                                    "poliigon.poliigon_material",
                                    text=vLbl,
                                    icon=vIcon,
                                )
                                vOp.vTooltip = vTTip

                            vOp.vType = vAData["type"]
                            vOp.vAsset = vAData["name"]
                            vOp.vSize = vDefSize
                            vOp.vData = vAData["name"] + "@" + vDefSize

                        # HDRIs ................................

                        elif vAData["type"] == "HDRIs":
                            if error:
                                vOp = vRow.operator(
                                    "poliigon.poliigon_hdri",
                                    text=error.button_label,
                                    icon="ERROR",
                                )
                                vOp.vTooltip = error.description
                            else:
                                vOp = vRow.operator(
                                    "poliigon.poliigon_hdri",
                                    text="Import " + vDefSize,
                                    icon="TRACKING_REFINE_BACKWARDS",
                                )
                                vOp.vTooltip = vAData["name"] + "\n(Import HDRI)"
                            vOp.vAsset = vAData["name"]
                            vOp.vSize = vDefSize

                        # BRUSHES ................................

                        elif vAData["type"] == "Brushes":
                            if error:
                                vOp = vRow.operator(
                                    "poliigon.poliigon_brush",
                                    text=error.button_label,
                                    icon="ERROR",
                                )
                                vOp.vTooltip = error.description
                            else:
                                vOp = vRow.operator(
                                    "poliigon.poliigon_brush",
                                    text="Import " + vDefSize,
                                    icon="TRACKING_REFINE_BACKWARDS",
                                )
                                vOp.vTooltip = vAData["name"] + "\n(Import Brush)"
                            vOp.vAsset = vAData["name"]
                            vOp.vSize = vDefSize

                    else:
                        if error:
                            vOp = vRow.operator(
                                "poliigon.poliigon_download",
                                text=error.button_label,
                                icon="ERROR",
                            )
                            vOp.vTooltip = error.description
                        else:
                            vOp = vRow.operator(
                                "poliigon.poliigon_download",
                                text="Download",
                                icon="IMPORT",
                            )
                            vOp.vTooltip = vAData["name"] + "\nDownload Default"

                        vOp.vMode = "download"
                        vOp.vAsset = vAData["name"]
                        vOp.vType = vAData["type"]
                        vOp.vSize = vDefSize

                else:
                    if error:
                        vLbl = error.button_label
                    elif vCrdts == 0:
                        vLbl = "Purchase (FREE)"
                    else:
                        vLbl = f"Purchase ({vCrdts} C)"

                    vOp = vRow.operator(
                        "poliigon.poliigon_download", text=vLbl,
                        icon='ERROR' if error else 'NONE'
                    )
                    vOp.vAsset = vAData["name"] + "@" + str(vAData["id"])
                    vOp.vType = vAData["type"]
                    vOp.vSize = vDefSize
                    vOp.vMode = "purchase"
                    vOp.vCredits = str(vCrdts)
                    if error:
                        vOp.vTooltip = error.description
                    else:
                        vOp.vTooltip = f"Purchase {vAData['name']} for {vCrdts} Credits"

                # Quick menu
                quick_subtitle = "\n(options)" if vDownloaded else "\nSee More"

                vOp = vRow.operator(
                    "poliigon.show_quick_menu",
                    text="",
                    icon="TRIA_DOWN",
                )
                # print("What is this?", vAData, )
                vOp.vAsset = vAData["name"]
                vOp.vTooltip = vAData["name"] + quick_subtitle
                vOp.vAssetId = int(vAData["id"])
                vOp.vAssetType = vAData["type"]
                vOp.vSizes = ";".join(vAData["sizes"])

            # IMPORTED ....................................................

            elif vArea == "imported":

                # MODELS ................................

                if vAData["type"] == "Models":
                    vOp = vRow.operator(
                        "poliigon.poliigon_select",
                        text="Select",
                        icon="RESTRICT_SELECT_OFF",
                    )
                    vOp.vMode = "model"
                    vOp.vData = vAData["name"]
                    vOp.vTooltip = vAData["name"] + "\n(Select all instances)"

                # TEXTURES ................................

                elif vAData["type"] == "Textures":
                    vOp = vRow.operator(
                        "poliigon.poliigon_apply",
                        text="Apply",
                        icon="TRACKING_REFINE_BACKWARDS",
                    )
                    vOp.vType = vAData["type"]
                    vOp.vAsset = vAData["name"]
                    vOp.vMat = cTB.vAssets["imported"]["Textures"][vAData["name"]][0].name
                    vOp.vTooltip = vAData["name"] + "\n(Apply to selected models)"

                # HDRIS ................................

                elif vAData["type"] == "HDRIs":
                    vOp = vRow.operator(
                        "poliigon.poliigon_hdri",
                        text="Apply",
                        icon="TRACKING_REFINE_BACKWARDS",
                    )
                    vOp.vAsset = vAData["name"]
                    vOp.vSize = "apply"
                    vOp.vTooltip = vAData["name"] + "\n(Apply to Scene)"

                # BRUSHES ................................

                elif vAData["type"] == "Brushes":
                    vLbl = "Activate"
                    vTTip = vAData["name"] + "\n(Set as Active Brush)"
                    if vAData["name"] == vBrush:
                        vLbl = "Active"
                        vTTip = vAData["name"] + "\n(Currently Active Brush)"

                    vOp = vRow.operator(
                        "poliigon.poliigon_brush",
                        text=vLbl,
                        icon="BRUSH_DATA",
                    )
                    vOp.vAsset = vAData["name"]
                    vOp.vSize = "apply"
                    vOp.vTooltip = vTTip

            # .............................................................

            if cTB.vSettings["preview_size"] == 3:
                vGrid.separator()
            else:
                vCell.separator()

        # PAGES ...........................................................
        
        if cTB.vPages[vArea] > 1:
            cTB.vBase.separator()

            vRow = cTB.vBase.row(align=0)

            vSt = 0
            vEd = cTB.vPages[vArea]

            vPMax = int((cTB.vWidth / (30 * cTB.get_ui_scale())) - 5)
            if cTB.vPages[vArea] > vPMax:
                vSt = vPage - int(vPMax / 2)
                vEd = vPage + int(vPMax / 2)
                if vSt < 0:
                    vSt = 0
                    vEd = vPMax
                elif vEd >= cTB.vPages[vArea]:
                    vSt = cTB.vPages[vArea] - vPMax
                    vEd = cTB.vPages[vArea]

            vRowL = vRow.row(align=1)
            vRowL.enabled = vPage != 0

            vOp = vRowL.operator(
                "poliigon.poliigon_setting", text="", icon="TRIA_LEFT"
            )
            vOp.vMode = "page_-"
            vOp.vTooltip = "Go to Previous Page"

            vRowM = vRow.row(align=1)

            vOp = vRowM.operator(
                "poliigon.poliigon_setting", text="1", depress=(vPage == 0)
            )
            vOp.vMode = "page_0"
            vOp.vTooltip = "Go to Page 1"

            if vSt > 1:
                vRowM.label(
                    text="",
                    icon_value=cTB.vIcons["ICON_dots"].icon_id,
                )

            for i in range(vSt, vEd):
                if i in [0, cTB.vPages[vArea] - 1]:
                    continue

                # Make sure we have data for this page
                cTB.f_GetAssets(vArea, vPage=i, vBackground=1)

                vOp = vRowM.operator(
                    "poliigon.poliigon_setting",
                    text=str(i + 1),
                    depress=(i == vPage),
                )
                vOp.vMode = "page_" + str(i)
                vOp.vTooltip = "Go to Page " + str(i + 1)

            if vEd < cTB.vPages[vArea] - 1:
                vRowM.label(text="", icon_value=cTB.vIcons["ICON_dots"].icon_id)

            vOp = vRowM.operator(
                "poliigon.poliigon_setting",
                text=str(cTB.vPages[vArea]),
                depress=(vPage == (cTB.vPages[vArea] - 1)),
            )
            vOp.vMode = "page_" + str(cTB.vPages[vArea] - 1)
            vOp.vTooltip = "Go to Page " + str(cTB.vPages[vArea])

            cTB.f_GetAssets(vArea, vPage=cTB.vPages[vArea]-1, vBackground=1)

            vRowR = vRow.row(align=1)
            vRowR.enabled = vPage != (cTB.vPages[vArea] - 1)

            vOp = vRowR.operator(
                "poliigon.poliigon_setting", text="", icon="TRIA_RIGHT"
            )
            vOp.vMode = "page_+"
            vOp.vTooltip = "Go to Next Page"

    # VIEW MORE ...........................................................

    if vArea == "my_assets":
        if vNotFoundBox:
            vRow = vNotFoundBox.row(align=True)
            vRow.scale_y = 1.5

            vLbl = "View more online"
            use_padding = 500

            if cTB.vWidth >= use_padding * cTB.get_ui_scale():
                vRow.label(text="")

            vOp = vRow.operator(
                "poliigon.poliigon_setting",
                text=vLbl,
                icon_value=cTB.vIcons["ICON_poliigon"].icon_id
            )
            vOp.vMode = "view_more"

            if cTB.vWidth >= use_padding * cTB.get_ui_scale():
                vRow.label(text="")

    elif vArea == "imported":
        vImportedAssets = [vA for vT in cTB.vAssets["imported"].values() for vA in vT]

        if not len(vImportedAssets):
            cTB.vBase.separator()
            cTB.vBase.separator()

            if len(cTB.vPurchased):
                vRow = cTB.vBase.row(align=1)
                vOp = vRow.operator(
                    "poliigon.poliigon_setting",
                    text="Explore Your Assets",
                    icon_value=cTB.vIcons["ICON_myassets"].icon_id,
                )
                vOp.vMode = "area_my_assets"
                vOp.vTooltip = "Show My Assets"

            else:
                vRow = cTB.vBase.row(align=1)
                vOp = vRow.operator(
                    "poliigon.poliigon_setting",
                    text="Explore Poliigon Assets",
                    icon_value=cTB.vIcons["ICON_poliigon"].icon_id,
                )
                vOp.vMode = "area_poliigon"
                vOp.vTooltip = "Show Poliigon Assets"


#@timer
def f_BuildActive(cTB):
    dbg = 0
    cTB.print_separator(dbg, "f_BuildActive")

    if cTB.vActiveMat != None:
        if cTB.vActiveMat not in bpy.data.materials.keys():
            if cTB.vActiveAsset in cTB.vAssets["imported"]["Textures"].keys():
                cTB.vActiveMat = cTB.vAssets["imported"]["Textures"][cTB.vActiveAsset][
                    0
                ].name
            else:
                cTB.vActiveMat = None

    # .....................................................................

    vSpc = 1.0 / cTB.vWidth

    vSel = bpy.context.selected_objects

    vAllFaces = []
    for vK in cTB.vActiveFaces.keys():
        vAllFaces += cTB.vActiveFaces[vK]

    vSMats = [vM for vMs in cTB.vAssets["imported"]["Textures"].values() for vM in vMs]
    vSelMats = []
    vSelMixMats = []
    cTB.vActiveObjects = []
    for vObj in vSel:
        vM = vObj.active_material
        if vM in vSMats:
            vSelMats.append(vM)
            cTB.vActiveObjects.append(vObj)

    # ..................................................................................

    if len(cTB.vActiveObjects) > 1 and cTB.vActiveMode == "model":
        vBox = cTB.vBase.box()

        vOp = vBox.operator(
            "poliigon.poliigon_setting",
            text=str(len(cTB.vActiveObjects)) + " Selected Objects",
            icon="DISCLOSURE_TRI_DOWN"
            if cTB.vSettings["show_active"]
            else "DISCLOSURE_TRI_RIGHT",
            emboss=0,
        )
        vOp.vMode = "show_active"
        if cTB.vSettings["show_active"]:
            vOp.vTooltip = "Hide Active Settings"
        else:
            vOp.vTooltip = "Show Active Settings"

        if cTB.vSettings["show_active"]:
            for vO in cTB.vActiveObjects:
                vOp = vBox.operator(
                    "poliigon.poliigon_select",
                    text=vO.name,
                    icon="RESTRICT_SELECT_OFF",
                )
                vOp.vMode = "object"
                vOp.vData = vO.name
                vOp.vTooltip = "Select " + vO.name

    # .....................................................................

    elif cTB.vActiveAsset != None and cTB.vSettings["area"] != "poliigon":
        vName = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", cTB.vActiveAsset)
        vName = re.sub(r"(?<=[a-z])(?=[0-9])", " ", vName)

        vBox = cTB.vBase.box().column(align=1)

        vRow = vBox.row()

        vLbl = "Material Settings"

        vOp = vRow.operator(
            "poliigon.poliigon_setting",
            text=vLbl,
            icon="DISCLOSURE_TRI_DOWN"
            if cTB.vSettings["show_active"]
            else "DISCLOSURE_TRI_RIGHT",
            emboss=0,
        )
        vOp.vMode = "show_active"
        if cTB.vSettings["show_active"]:
            vOp.vTooltip = "Hide Material Settings"
        else:
            vOp.vTooltip = "Show Material Settings"

        # .................................................................

        if cTB.vSettings["show_active"]:
            vBox.separator()

            vRow = vBox.row()

            vLbl = "Active Asset :  " + vName
            if len(cTB.vActiveObjects) and cTB.vActiveMode == "model":
                vLbl = "Active Object :  " + cTB.vActiveObjects[0].name
            elif cTB.vActiveMode == "mixer":
                vLbl = "Active Mix Material :  " + vName
                if cTB.vSettings["show_active"]:
                    vLbl = "Active Mix Material :"

            vOp = vRow.label(text=vLbl)

            vRow = vRow.row(align=1)

            vOp = vRow.operator(
                "poliigon.poliigon_asset_options",
                text="",
                icon="FILE_FOLDER",
                emboss=1,
            )
            vOp.vType = cTB.vActiveType
            vOp.vData = cTB.vActiveAsset + "@dir"
            vOp.vTooltip = "Open " + cTB.vActiveAsset + " Folder(s)"

            vOp = vRow.operator(
                "poliigon.poliigon_asset_options",
                text="",
                icon_value=cTB.vIcons["ICON_poliigon"].icon_id,
                emboss=1,
            )
            vOp.vType = cTB.vActiveType
            vOp.vData = cTB.vActiveAsset + "@link"
            vOp.vTooltip = "View " + cTB.vActiveAsset + " on Poliigon.com"

            vAData = cTB.vAssets["local"][cTB.vActiveType][cTB.vActiveAsset]

            vTypes = []
            for vT in cTB.vMaps:
                if any(
                    vF for vF in vAData["files"] if vT in f_FName(vF).split("_")
                ):
                    vTypes.append(vT)
            vTypes.sort()

            vVars = vAData["vars"]

            vSizes = vAData["sizes"]

            vScale = None

            # .....................................................................

            """if cTB.vActiveMode == "asset":
                vBox.separator()

                vMods = [
                    vF
                    for vF in vAData[
                        "files"
                    ]
                    if any(
                        vE
                        for vE in [".fbx", ".blend"]
                        if vF.lower().endswith(vE)
                    )
                ]

                vIBox = vBox.box()
                vIBox.scale_y = 0.9

                vOp = vIBox.operator(
                    "poliigon.poliigon_setting",
                    text="Asset Info",
                    icon="DISCLOSURE_TRI_DOWN"
                    if cTB.vSettings["show_asset_info"]
                    else "DISCLOSURE_TRI_RIGHT",
                    emboss=0,
                )
                vOp.vMode = "show_asset_info"
                if cTB.vSettings["show_asset_info"]:
                    vOp.vTooltip = "Hide Asset Info"
                else:
                    vOp.vTooltip = "Show Asset Info"

                if cTB.vSettings["show_asset_info"]:
                    # pRow = vIBox.row()
                    vRow = vIBox.split(factor=200.0 / cTB.vWidth, align=1)

                    vCol = vRow.column()

                    #if cTB.vActiveMat != None:
                    #    vCol.template_preview(bpy.data.materials[cTB.vActiveMat], show_buttons=0, preview_id="CUBE")
                    #else :
                    
                    vCol.template_icon(icon_value=cTB.vPreviews[cTB.vActiveAsset].icon_id,scale=7)

                    # .....................................................................

                    vCol = vRow.column(align=1)

                    vCol.label(text="Maps :")

                    vLbl = " "
                    for i in range(len(vTypes)):
                        if i not in [0, 3, 6, 9, 12]:
                            vLbl += "  "
                        vLbl += vTypes[i]
                        if i in [2, 5, 8, 11]:
                            vCol.label(text=vLbl)
                            vLbl = " "

                    # .....................................................................

                    if len(vVars):
                        vCol.label(text="Variations :")
                        vCol.label(text=" " + "  ".join(vVars))

                    # .....................................................................

                    vCol.label(text="Sizes :")
                    vCol.label(text=" " + "  ".join(vSizes))"""

            # .............................................................

            if cTB.vActiveAsset in cTB.vAssets["imported"]["Textures"].keys():
                vBox.separator()

                vMCol = vBox.column()

                vMCol.label(text="Materials :")

                if cTB.vActiveMode == "model":
                    for i in range(len(cTB.vActiveMats)):
                        vMat = cTB.vActiveMats[i]
                        if vMat == None:
                            continue

                        vAsset = None
                        for vA in cTB.vAssets["imported"]["Textures"].keys():
                            if vMat in cTB.vAssets["imported"]["Textures"][vA]:
                                vAsset = vA
                                break

                        vRow1 = vMCol.row(align=1)

                        if vAsset == None:
                            vRow1.label(text="Slot " + str(i) + " : " + vMat.name)
                        else:
                            vCol = vRow1.column()
                            vV = 1
                            vLbl = str(i) + " : "
                            if cTB.vWidth > 400:
                                vV = 1.5
                                vLbl = "Slot " + str(i) + " : "
                            vCol.ui_units_x = vV
                            vCol.label(text=vLbl)

                            if len(vSel) or len(vAllFaces):
                                vOp = vRow1.operator(
                                    "poliigon.poliigon_apply",
                                    text="",
                                    icon="TRACKING_REFINE_BACKWARDS"
                                )
                                vOp.vType = cTB.vActiveType
                                vOp.vAsset = vAsset
                                vOp.vMat = vMat.name
                                vOp.vTooltip = (
                                    "Apply " + vMat.name + " to Selected Objects"
                                )

                            vOp = vRow1.operator(
                                "poliigon.poliigon_active",
                                text=vMat.name,
                                icon="MATERIAL",
                            )
                            vOp.vType = cTB.vActiveType
                            vOp.vMode = "mat"
                            vOp.vData = vAsset + "@" + vMat.name
                            vOp.vTooltip = vMat.name

                            vOp = vRow1.operator(
                                "poliigon.poliigon_select",
                                text="",
                                icon="RESTRICT_SELECT_OFF"
                            )
                            vOp.vMode = "faces"
                            vOp.vData = str(i)
                            vOp.vTooltip = "Select " + vMat.name + " Faces"
                else:
                    vRow = vMCol.row()

                    for vM in cTB.vAssets["imported"]["Textures"][cTB.vActiveAsset]:
                        vRow1 = vRow.row(align=1)

                        vLbl = ""
                        if (
                            len(cTB.vAssets["imported"]["Textures"][cTB.vActiveAsset]) < 4
                            or vM.name == cTB.vActiveMat
                        ):
                            vLbl = vM.name

                        if len(vSel) or len(vAllFaces):
                            vOp = vRow1.operator(
                                "poliigon.poliigon_apply",
                                text="",
                                icon="TRACKING_REFINE_BACKWARDS",
                            )
                            vOp.vType = cTB.vActiveType
                            vOp.vAsset = cTB.vActiveAsset
                            vOp.vMat = vM.name
                            vOp.vTooltip = (
                                "Apply " + vM.name + " to Selected Objects"
                            )

                        vOp = vRow1.operator(
                            "poliigon.poliigon_active",
                            text=vLbl,
                            icon="MATERIAL",
                        )
                        vOp.vType = cTB.vActiveType
                        vOp.vMode = "mat"
                        vOp.vData = vM.name
                        vOp.vTooltip = vM.name

            # .............................................................

            if cTB.vActiveMat != None:
                vBox.separator()
                vBox.separator()

                vOBox = vBox.box()
                vOBox.scale_y = 0.9

                vSplit = vOBox.split(factor=1.0 - (45.0 / cTB.vWidth))

                # MATERIAL OPTIONS ........................................

                vOp = vSplit.operator(
                    "poliigon.poliigon_setting",
                    text="Material Options",
                    icon="DISCLOSURE_TRI_DOWN"
                    if cTB.vSettings["show_mat_ops"]
                    else "DISCLOSURE_TRI_RIGHT",
                    emboss=0,
                )
                vOp.vMode = "show_mat_ops"
                if cTB.vSettings["show_mat_ops"]:
                    vOp.vTooltip = "Hide Material Options"
                else:
                    vOp.vTooltip = "Show Material Options"

                if cTB.vSettings["show_mat_ops"]:
                    vSplit = vOBox.split(factor=50.0 / cTB.vWidth)

                    vSplit.label(text="Name:")

                    vRow = vSplit.row()

                    vRow.prop(bpy.context.scene, "vEditMatName", text="")
                    if bpy.context.scene.vEditMatName != cTB.vActiveMat:
                        vOp = vRow.operator(
                            "poliigon.poliigon_material",
                            text="",
                            icon="FILE_REFRESH",
                            emboss=1,
                        )
                        vOp.vType = cTB.vActiveType
                        vOp.vData = "rename"
                        vOp.vTooltip = "Rename Material."

                    vCol = vOBox.column()

                    vMat = bpy.data.materials[cTB.vActiveMat]

                    if not len(cTB.vActiveObjects) or cTB.vActiveMode == "asset":
                        vObjs = []
                        for vObj in bpy.data.objects:
                            if vObj.active_material == vMat:
                                vObjs.append(vObj.name)

                        if len(vObjs):
                            vObjs.sort()
                            vOp = vCol.operator(
                                "poliigon.poliigon_select",
                                text="Applied to " + str(len(vObjs)) + " objects.",
                                icon="RESTRICT_SELECT_OFF",
                            )
                            vOp.vMode = "mat_objs"
                            vOp.vData = cTB.vActiveMat
                            vOp.vTooltip = "\n".join(vObjs)

                vSize = []
                for vT in cTB.vActiveTextures.keys():
                    vFName = os.path.basename(
                        cTB.vActiveTextures[vT].image.filepath)
                    vSize += [vS for vS in vSizes if vS in vFName]
                vSize = list(set(vSize))

                # MATERIAL TEXTURES .......................................

                vTBox = vBox.box()
                vTBox.scale_y = 0.9

                vSplit = vTBox.split(factor=1.0 - (45.0 / cTB.vWidth))

                vOp = vSplit.operator(
                    "poliigon.poliigon_setting",
                    text="Material Textures",
                    icon="DISCLOSURE_TRI_DOWN"
                    if cTB.vSettings["show_mat_texs"]
                    else "DISCLOSURE_TRI_RIGHT",
                    emboss=0,
                )
                vOp.vMode = "show_mat_texs"
                if cTB.vSettings["show_mat_texs"]:
                    vOp.vTooltip = "Hide Material Textures"
                else:
                    vOp.vTooltip = "Show Material Textures"

                if not cTB.vSettings["show_mat_texs"]:
                    vSplit.label(text="", icon="BLANK1")

                else:
                    vLbl = vSize[0]
                    if len(vSize) > 1:
                        vLbl += "..."

                    if len(vSizes) > 1:
                        vOp = vSplit.operator(
                            "poliigon.poliigon_texture", text=vLbl
                        )
                        vOp.vType = cTB.vActiveType
                        vOp.vData = "size@" + "#".join(vSizes)
                        vOp.vTooltip = "Swap Texture Size"
                    else:
                        vSplit.label(text=vLbl)

                    vRow = vTBox.row()

                    for vT in sorted([vK for vK in cTB.vActiveTextures.keys()]):
                        vCol = vRow.column(align=1)
                        vCol.template_icon(
                            icon_value=cTB.vActiveTextures[
                                vT
                            ].image.preview.icon_id,
                            scale=3,
                        )
                        vOp = vCol.operator("poliigon.poliigon_texture", text=vT)
                        vOp.vType = cTB.vActiveType
                        vOp.vData = cTB.vActiveTextures[vT].image.name + "@" + vT
                        vOp.vTooltip = (
                            vT
                            + " Texture Options\n("
                            + cTB.vActiveTextures[vT].image.filepath
                            + ")"
                        )

                # MATERIAL PROPERTIES .....................................

                vMBox = vBox.box()
                vMBox.scale_y = 0.9

                vSplit = vMBox.split(factor=1.0 - (45.0 / cTB.vWidth))

                vOp = vSplit.operator(
                    "poliigon.poliigon_setting",
                    text="Material Properties",
                    icon="DISCLOSURE_TRI_DOWN"
                    if cTB.vSettings["show_mat_props"]
                    else "DISCLOSURE_TRI_RIGHT",
                    emboss=0,
                )
                vOp.vMode = "show_mat_props"
                if cTB.vSettings["show_mat_props"]:
                    vOp.vTooltip = "Hide Material Properties"
                else:
                    vOp.vTooltip = "Show Material Properties"

                if not cTB.vSettings["show_mat_props"]:
                    vSplit.label(text="", icon="BLANK1")
                else:
                    vOp = vSplit.operator(
                        "poliigon.poliigon_setting",
                        text="",
                        icon="SETTINGS",
                        emboss=cTB.vSettings["mat_props_edit"],
                        depress=cTB.vSettings["mat_props_edit"],
                    )
                    vOp.vMode = "mat_props_edit"
                    vOp.vTooltip = "Specify Which Properties to Show."

                    vDisp = 0
                    for vP in cTB.vActiveMatProps.keys():
                        if not cTB.vSettings["mat_props_edit"]:
                            if vP not in cTB.vSettings["mat_props"]:
                                continue
                            if "Displacement" in vP:
                                if not any(
                                    vT for vT in ["DISP", "DISP16"] if vT in vTypes
                                ):
                                    continue
                                vDisp = 1

                        vN = cTB.vActiveMatProps[vP]
                        vVal = vN.inputs[vP].default_value

                        vRow = vMBox.row()

                        if cTB.vSettings["mat_props_edit"]:
                            vOp = vRow.operator(
                                "poliigon.poliigon_setting",
                                text="",
                                icon="CHECKBOX_HLT"
                                if vP in cTB.vSettings["mat_props"]
                                else "CHECKBOX_DEHLT",
                            )
                            vOp.vMode = "prop@" + vP
                            vOp.vTooltip = "Show/Hide Property"

                        vRow1 = vRow.row(align=1)

                        vLbl = vP
                        if vN.type == "BUMP":
                            vLbl = "Bump " + vP

                        vRow1.prop(
                            text=vLbl + " : " + str(vVal),
                            data=vN.inputs[vP],
                            property="default_value",
                            expand=1,
                            slider=1,
                        )
                        vOp = vRow1.operator(
                            "poliigon.poliigon_preset",
                            text="",
                            icon="LOOP_BACK",
                        )
                        vOp.vData = vP
                        vOp.vTooltip = "(Reset Property to Default)"

                        vPSets = ["0.1", "0.5", "1.0", "2.0", "5.0", "10.0"]
                        if vP in cTB.vPresets.keys():
                            vPSets = cTB.vPresets[vP]
                        elif vP in ["Roughness Adj."]:
                            vPSets = [
                                "-1.0",
                                "-0.5",
                                "-0.1",
                                "0.1",
                                "0.5",
                                "1.0",
                            ]
                        elif vN.type == "BUMP" and vP == "Distance":
                            vPSets = ["0.05", "0.075", "0.1", "0.2", "0.5"]

                        if cTB.vSettings["mat_props_edit"]:
                            vOp = vRow.operator(
                                "poliigon.poliigon_setting",
                                text="",
                                icon="PRESET",
                                depress=(cTB.vEditPreset == vP),
                            )
                            vOp.vMode = (
                                "preset@"
                                + vP
                                + "@"
                                + ";".join([str(vV) for vV in vPSets])
                            )
                            if cTB.vEditPreset == vP:
                                vOp.vTooltip = "Save Presets"
                            else:
                                vOp.vTooltip = "Edit Presets"
                        else:
                            vOp = vRow.operator(
                                "poliigon.poliigon_preset",
                                text="",
                                icon="PRESET",
                            )
                            vOp.vData = (
                                vP + "@" + "@".join([str(vV) for vV in vPSets])
                            )
                            if vP == "Scale":
                                vOp.vData += "@Real World"
                            vOp.vTooltip = "(Set Property to ...)"

                        if cTB.vEditPreset == vP:
                            vRow = vMBox.row()
                            vRow.prop(
                                bpy.context.scene, "vEditText", text="Presets"
                            )

                        if vP == "Displacement Mid-Level":
                            vDObjs = [
                                vO
                                for vO in cTB.vActiveObjects
                                if "Subdivision" in vO.modifiers.keys()
                            ]

                            if len(vDObjs):
                                vPSets = [0.1, 0.5, 1.0, 5.0, 10.0]
                                if "Displacement Detail" in cTB.vPresets.keys():
                                    vPSets = cTB.vPresets["Displacement Detail"]

                                if cTB.vSettings["mat_props_edit"]:
                                    vRow = vMBox.row()

                                    if cTB.vSettings["mat_props_edit"]:
                                        vOp = vRow.operator(
                                            "poliigon.poliigon_setting",
                                            text="",
                                            icon="CHECKBOX_HLT"
                                            if "Displacement Detail"
                                            in cTB.vSettings["mat_props"]
                                            else "CHECKBOX_DEHLT",
                                        )
                                        vOp.vMode = "prop@Displacement Detail"
                                        vOp.vTooltip = "Show/Hide Property"

                                    vRow.label(text="Displacement Detail:")

                                    vOp = vRow.operator(
                                        "poliigon.poliigon_setting",
                                        text="",
                                        icon="PRESET",
                                        depress=(
                                            cTB.vEditPreset == "Displacement Detail"
                                        ),
                                    )
                                    vOp.vMode = (
                                        "preset@Displacement Detail@"
                                        + ";".join([str(vV) for vV in vPSets])
                                    )
                                    if cTB.vEditPreset == "Displacement Detail":
                                        vOp.vTooltip = "Save Presets"
                                    else:
                                        vOp.vTooltip = "Edit Presets"

                                    if cTB.vEditPreset == "Displacement Detail":
                                        vRow = vMBox.row()
                                        vRow.prop(
                                            bpy.context.scene,
                                            "vEditText",
                                            text="Presets",
                                        )
                                elif vDisp and len(vSel):
                                    vSlices = []
                                    for vO in vSel:
                                        try:
                                            vV = (
                                                float(
                                                    int(vO.cycles.dicing_rate * 100)
                                                )
                                                / 100.0
                                            )
                                            vSlices.append(vV)
                                        except:
                                            pass
                                    vSlices = list(set(vSlices))

                                    vMBox.label(text="Displacement Detail:")

                                    vRow = vMBox.row()
                                    for vV in vPSets:
                                        vCol = vRow.column()
                                        vCol.ui_units_x = 1.5
                                        vOp = vCol.operator(
                                            "poliigon.poliigon_preset",
                                            text=str(vV),
                                            depress=(vV in vSlices),
                                        )
                                        vOp.vData = "detail@" + str(vV)
                                        vOp.vTooltip = (
                                            "Set Displacement Detail to " + str(vV)
                                        )

            # .............................................................

            if not cTB.vSettings["hide_suggest"] and len(cTB.vSuggestions):
                vBox.separator()
                vBox.separator()

                vCol = vBox.column()

                vOp = vCol.operator(
                    "poliigon.poliigon_setting", text="You might also like..."
                )
                vOp.vMode = "view_suggested"
                vOp.vTooltip = "View Other Assets like " + cTB.vActiveAsset

                vRow = vCol.row(align=1)

                vNum = int(cTB.vWidth / 70.0)
                for n in range(len(cTB.vSuggestions)):
                    if n == vNum:
                        break
                    if cTB.vSuggestions[n] in cTB.vPreviews:
                        vIcon = cTB.vPreviews[cTB.vSuggestions[n]].icon_id
                    else:
                        cTB.f_GetPreview(cTB.vSuggestions[n])
                        vIcon = cTB.vIcons["GET_preview"].icon_id
                    vRow.template_icon(icon_value=vIcon, scale=3)

    cTB.vBase.separator()


# .............................................................................
# Draw popups
# .............................................................................


def show_quick_menu(cTB, asset_name, asset_id, asset_type, sizes=[]):
    """Generates the quick options menu next to an asset in the UI grid."""

    # Configuration
    if asset_name in cTB.vPurchased:
        title = "Choose Texture Size"  # If downloading and already purchased.
    else:
        title = asset_name

    downloaded = []  # Sizes already downloaded.
    in_scene = False

    if asset_type in cTB.vAssets["local"].keys():
        if asset_name in cTB.vAssets["local"][asset_type].keys():
            downloaded = cTB.vAssets["local"][asset_type][asset_name]["sizes"]

    if asset_type in cTB.vAssets["imported"].keys():
        if asset_name in cTB.vAssets["imported"][asset_type].keys():
            in_scene = True

    @reporting.handle_draw()
    def draw(self, context):
        layout = self.layout

        # List the different resolution sizes to provide.
        if asset_name in cTB.vPurchased:
            for size in sizes:
                if asset_type == "Textures":
                    draw_material_sizes(context, size, layout)
                elif asset_type == "Models":
                    draw_model_sizes(context, size, layout)
                elif asset_type == "Brushes":
                    draw_brush_sizes(context, size, layout)
                elif asset_type == "HDRIs":
                    draw_hdri_sizes(context, size, layout)
                else:
                    layout.label(text=f"{asset_type} not implemented yet")

            layout.separator()

        # Always show view online and high res previews.
        ops = layout.operator(
            "POLIIGON_OT_view_thumbnail",
            text="View larger thumbnail",
            icon="OUTLINER_OB_IMAGE")
        ops.tooltip = f"View larger thumbnail for {asset_name}"
        ops.asset = asset_name
        ops.thumbnail_index = 1

        ops = layout.operator(
            "poliigon.poliigon_link",
            text="View online",
            icon_value=cTB.vIcons["ICON_poliigon"].icon_id,
        )
        ops.vMode = str(asset_id)
        ops.vTooltip = "View on Poliigon.com"

        # If already local, support opening the folder location.
        if downloaded:
            ops = layout.operator(
                "poliigon.poliigon_folder",
                text="Open folder location",
                icon="FILE_FOLDER")
            ops.vAsset = asset_name

        return

    def draw_material_sizes(context, size, element):
        """Draw the menu row for a materials' single reoslution size."""
        row = element.row()
        imported = f"{asset_name}_{size}" in bpy.data.materials

        if imported or size in downloaded:
            # Action: Load and apply it
            if imported:
                label = f"{size} (apply material)"
                tip = f"Apply {size} Material\n{asset_name}"
            elif context.selected_objects:
                label = f"{size} (import + apply)"
                tip = f"Apply {size} Material\n{asset_name}"
            else:
                label = f"{size} (import)"
                tip = f"Import {size} Material\n{asset_name}"

            # If nothing is selected and this size is already importing,
            # then there's nothing to do.
            if imported and not context.selected_objects:
                row.enabled = False

            ops = row.operator(
                "poliigon.poliigon_material",
                text=label,
                icon="TRACKING_REFINE_BACKWARDS")
            ops.vAsset = asset_name
            ops.vSize = size
            ops.vType = asset_type
            ops.vTooltip = tip

        else:
            # Action: Download
            label = f"{size} (download)"
            ops = row.operator(
                "poliigon.poliigon_download",
                text=label,
                icon="IMPORT")
            ops.vAsset = asset_name
            ops.vSize = size
            ops.vType = asset_type
            ops.vMode = "download"
            ops.vTooltip = f"Download {size} Material\n{asset_name}"

    def draw_model_sizes(context, size, element):
        """Draw the menu row for a model's single reoslution size."""
        row = element.row()

        if size in downloaded:
            # Action: Load and apply it
            lod, label, tip = get_model_op_details(asset_name, asset_type, size)

            ops = row.operator(
                "poliigon.poliigon_model",
                text=label,
                icon="TRACKING_REFINE_BACKWARDS")
            ops.vAsset = asset_name
            ops.vSize = size
            ops.vType = asset_type
            ops.vTooltip = tip
            ops.vLod = lod

        else:
            # Action: Download
            ops = row.operator(
                "poliigon.poliigon_download",
                text=f"{size} (download)",
                icon="IMPORT")
            ops.vAsset = asset_name
            ops.vSize = size
            ops.vType = asset_type
            ops.vMode = "download"
            ops.vTooltip = f"Download {size} textures\n{asset_name}"

    def draw_hdri_sizes(context, size, element):
        """Draw the menu row for an HDRI's single reoslution size."""
        row = element.row()
        if in_scene or size in downloaded:
            # Action: Load and apply it
            if in_scene:
                label = f"{size} (apply HDRI)"
                tip = f"Apply {size} HDRI\n{asset_name}"
            else:
                label = f"{size} (import HDRI)"
                tip = f"Import {size} HDRI\n{asset_name}"

            ops = row.operator(
                "poliigon.poliigon_hdri",
                text=label,
                icon="TRACKING_REFINE_BACKWARDS")
            ops.vAsset = asset_name
            ops.vSize = size
            ops.vTooltip = tip

        else:
            # Action: Download
            label = f"{size} (download)"
            ops = row.operator(
                "poliigon.poliigon_download",
                text=label,
                icon="IMPORT")
            ops.vAsset = asset_name
            ops.vSize = size
            ops.vType = asset_type
            ops.vMode = "download"
            ops.vTooltip = f"Download {size}\n{asset_name}"

    def draw_brush_sizes(context, size, element):
        """Draw the menu row for a brush's single reoslution size."""
        row = element.row()
        if in_scene or size in downloaded:
            # Action: Load and apply it
            if in_scene:
                label = f"{size} (equip brush)"
                tip = f"Equip {size} brush\n{asset_name}"
            else:
                label = f"{size} (import brush)"
                tip = f"Equip {size} brush\n{asset_name}"

            ops = row.operator(
                "poliigon.poliigon_brush",
                text=label,
                icon="TRACKING_REFINE_BACKWARDS")
            ops.vAsset = asset_name
            ops.vSize = size
            ops.vTooltip = tip

        else:
            # Action: Download
            label = f"{size} (download)"
            ops = row.operator(
                "poliigon.poliigon_download",
                text=label,
                icon="IMPORT")
            ops.vAsset = asset_name
            ops.vSize = size
            ops.vType = asset_type
            ops.vMode = "download"
            ops.vTooltip = f"Download {size}\n{asset_name}"

    # Generate the popup menu.
    bpy.context.window_manager.popup_menu(draw, title=title, icon="QUESTION")


def show_categories_menu(cTB, categories, index):
    """Generates the popup menu to display category selection options."""

    @reporting.handle_draw()
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column(align=True)

        for i in range(len(categories)):
            if i > 0 and i % 15 == 0:
                col = row.column(align=True)

            button = categories[i]
            label = f" {button}"
            op = col.operator("poliigon.poliigon_setting", text=label)
            op.vMode = f"category_{index}_{button}"
            op.vTooltip = f"Select {button}"

            if i == 0:
                col.separator()

    bpy.context.window_manager.popup_menu(draw)


def f_Dropdown(cTB, **kwargs):
    # TODO: Refactor to have distinct dropdown classes for individual needs.
    dbg = 0

    cTB.print_separator(dbg, "f_Dropdown")
    if bpy.app.background:
        return  # Don't popup menus when running headless.

    cTB.check_dpi()

    vTitle = ""
    if "vTitle" in kwargs:
        vTitle = kwargs["vTitle"]

    @reporting.handle_draw()
    def draw(self, context):
        vBtns = []
        vIcons = []
        vTooltips = []
        vCmd = None
        vCmds = None
        vType = ""
        vAsset = ""
        vData = ""
        vMode = None

        if "vBtns" in kwargs:
            vBtns = kwargs["vBtns"]
        if "vIcons" in kwargs:
            vIcons = kwargs["vIcons"]
        if "vTooltips" in kwargs:
            vTooltips = kwargs["vTooltips"]
        if "vCmd" in kwargs:
            vCmd = kwargs["vCmd"]
        if "vCmds" in kwargs:
            vCmds = kwargs["vCmds"]
        if "vType" in kwargs:
            vType = kwargs["vType"]
        if "vAsset" in kwargs:
            vAsset = kwargs["vAsset"]
        if "vData" in kwargs:
            vData = kwargs["vData"]
        if "vMode" in kwargs:
            vMode = kwargs["vMode"]

        cTB.print_debug(dbg, "f_Dropdown", kwargs)

        vLayout = self.layout

        vRow = vLayout.row()

        vCol = vRow.column(align=1)

        if vCmd == "poliigon.poliigon_asset_options":
            vSizes = cTB.vAssets[cTB.vSettings["area"]][vType][vData]["sizes"]

            if len(vSizes):
                vSizes.sort()
                vCol.label(text=vData + "  (" + ",".join(vSizes) + ")")
            else:
                vCol.label(text=vData)

            vCol.separator()
        
        vDownloaded = []
        if vType in cTB.vAssets["local"].keys():
            if vAsset in cTB.vAssets["local"][vType].keys():
                vDownloaded = cTB.vAssets["local"][vType][vAsset]["sizes"]
                vDownloaded += cTB.vAssets["local"][vType][vAsset]["lods"]
        
        vInScene = []
        if vType in cTB.vAssets["imported"].keys():
            if vAsset in cTB.vAssets["imported"][vType].keys():
                vInScene += cTB.vAssets["imported"][vType][vAsset]
                vInScene += [cTB.f_GetSize(vObj.name) for vObj in cTB.vAssets["imported"][vType][vAsset]]
                for vObj in cTB.vAssets["imported"][vType][vAsset]:
                    if 'poliigon_lod' in dir(vObj):
                        vInScene.append(vObj.poliigon_lod)
        
        vIsSelection = len(bpy.context.selected_objects) > 0

        for i in range(len(vBtns)):
            if i > 0 and i % 30 == 0:
                vCol = vRow.column(align=1)

            vB = vBtns[i]
            cTB.print_debug(dbg, "f_Dropdown", vB)

            if vB == "-":
                vCol.separator()
                continue

            # ..............................................

            vBRow = vCol.row(align=1)

            if (
                vCmd == "poliigon.poliigon_preset"
                and vB == "Real World"
                and not vIsSelection
            ):
                continue

            # ..............................................

            vIcon = None
            if len(vIcons):
                vIcon = vIcons[i]

            elif vCmd == "poliigon.poliigon_asset_options":
                if vB == "Open Asset Folder(s)":
                    vIcon = "FILE_FOLDER"
                elif vB == "Find Asset on Poliigon.com":
                    vIcon = "URL"

            elif "Import" in vB:
                # vIcon = "IMPORT"
                vIcon = "TRACKING_REFINE_BACKWARDS"

            # ..............................................

            vBCmd = vCmd
            if vCmd == None and len(vCmds) :
                vBCmd = vCmds[i]

            vTtip = ""
            if len(vTooltips):
                vTtip = vTooltips[i]

            vLbl = f" {vB}"
            if vBCmd == "poliigon.poliigon_download":
                vLbl = f" {vB}  (download)"
                if vType in cTB.vAssets["local"].keys():
                    if vAsset in cTB.vAssets[cTB.vSettings["area"]][vType].keys():
                        if vType == "Textures" and vB == cTB.vSettings["res"]:
                            vLbl = f" {vB}  (download default)"
                        elif vType == "Models" and vB == cTB.vSettings["mres"]:
                            vLbl = f" {vB}  (download default)"
                        elif vType == "HDRIs" and vB == cTB.vSettings["hdri"]:
                            vLbl = f" {vB}  (download default)"

                vIcon = "IMPORT"

            # ..............................................

            if vIcon == None:
                vOp = vBRow.operator(vBCmd, text=vLbl)
            else:
                if vIcon == "URL":
                    vOp = vBRow.operator(
                        vBCmd,
                        text=vLbl,
                        icon_value=cTB.vIcons["ICON_poliigon"].icon_id,
                    )
                else:
                    vOp = vBRow.operator(vBCmd, text=vLbl, icon=vIcon)

            # ..............................................

            if vMode == "lods":
                vOp.vLod = vB

            elif vMode != None:
                vOp.vMode = vMode

            # ..............................................

            if vBCmd in ["poliigon.poliigon_download"]:
                vOp.vAsset = vAsset
                vOp.vType = vType
                vOp.vSize = vB.split(" ")[0]
                vOp.vMode = "download"

            elif vBCmd in [
                "poliigon.poliigon_apply",
                "poliigon.poliigon_texture",
            ]:
                vOp.vType = vType

            if vBCmd in [
                "poliigon.poliigon_mix",
                "poliigon.poliigon_select",
                "poliigon.poliigon_preset",
                "poliigon.poliigon_texture",
            ]:
                vOp.vData = vData + "@" + vB

            elif vBCmd in ["poliigon.poliigon_apply"]:
                vOp.vAsset = vData
                vOp.vMat = vB

            elif vBCmd == "poliigon.poliigon_setting":
                if vMode == "area":
                    vOp.vMode = vB.replace(" ", "_").lower()
                else:
                    vOp.vMode = vData + "_" + vB

            elif vBCmd in [
                "poliigon.poliigon_mapping",
                "poliigon.poliigon_sorting",
            ]:
                vOp.vData = vB

            elif vBCmd in ["poliigon.poliigon_mix_tex"]:
                if vData == "":
                    vOp.vMode = vB
                else:
                    vOp.vMode = vData + "@" + vB

            elif vBCmd == "poliigon.poliigon_asset_options":
                if vB == "Open Asset Folder(s)":
                    vOp.vData = vData + "@dir"

                elif vB == "Find Asset on Poliigon.com":
                    vOp.vData = vData + "@link"

            if vTtip != None:
                vOp.vTooltip = vTtip

    bpy.context.window_manager.popup_menu(draw, title=vTitle, icon="QUESTION")


def f_Popup(cTB, vTitle="", vMsg="", vBtns=["OK"], vCmds=[None], vMode=None):
    dbg = 0
    cTB.print_separator(dbg, "f_Popup")

    @reporting.handle_draw()
    def draw(self, context):
        vLayout = self.layout

        vCol = vLayout.column(align=1)

        vIcon = "INFO"
        if vMode == "question":
            vIcon = "QUESTION"
        elif vMode == "error":
            vIcon = "ERROR"

        vCol.label(text=vTitle, icon=vIcon)

        vCol.separator()

        vCol.label(text=vMsg)

        vCol.separator()
        vCol.separator()

        vRow = vCol.row()
        for i in range(len(vBtns)):
            if vCmds[i] in [None, "cancel"]:
                vOp = vRow.operator("poliigon.poliigon_setting", text=vBtns[i])
                vOp.vMode = "none"

            elif vCmds[i] == "credits":
                vOp = vRow.operator(
                    "poliigon.poliigon_link", text="Add Credits", depress=1
                )
                vOp.vMode = "credits"

    bpy.context.window_manager.popover(draw)


def f_AssetInfo(cTB, vAsset):
    """Dynamic menu popup call populated based on info on this asset."""
    dbg = 0
    cTB.print_separator(dbg, "f_AssetInfo")

    @reporting.handle_draw()
    def asset_info_draw(self, context):
        """Called as part of the popup in operators for info mode."""
        vAssetType = cTB.vSettings["category"][cTB.vSettings["area"]][0]

        if cTB.vSettings["area"] == "poliigon":
            vAData = cTB.vAssets["poliigon"][vAssetType][vAsset]
            vPrevs = cTB.vPreviews

        else:
            vAData = cTB.vAssets[vAssetType][vAsset]
            vPrevs = cTB.vPreviews

        vLayout = self.layout
        vLayout.alignment = "CENTER"

        # .................................................................

        vCol = vLayout.column(align=1)

        vCol.template_icon(icon_value=vPrevs[vAsset].icon_id, scale=10)

        # .................................................................

        vRow = vCol.row(align=0)

        vRow.label(text=vAsset)

        vOp = vRow.operator(
            "poliigon.poliigon_asset_options", text="", icon="FILE_FOLDER"
        )
        vOp.vType = cTB.vActiveType
        vOp.vData = vAsset + "@dir"
        vOp.vTooltip = "Open " + vAsset + " Folder(s)"

        vOp = vRow.operator(
            "poliigon.poliigon_link",
            text="",
            icon_value=cTB.vIcons["ICON_poliigon"].icon_id,
        )
        vOp.vMode = str(vAData["id"])
        vOp.vTooltip = "View on Poliigon.com"

        vCol.separator()

        # .................................................................

        if vAssetType == "Models":
            vCol.label(text="Models :")

            vCol.separator()

        # .................................................................

        vCol.label(text="Maps :")

        vGrid = vCol.box().grid_flow(
            row_major=1, columns=4, even_columns=0, even_rows=0, align=0
        )

        for vM in vAData["maps"]:
            vGrid.label(text=vM)

        vCol.separator()

        # .................................................................

        vCol.label(text="Map Sizes :")

        vCol.box().label(text="   ".join(vAData["sizes"]))

        # vGrid = vCol.box().grid_flow(row_major=1, columns=7, even_columns=1, even_rows=1, align=0)
        #
        # for vS in vAData['sizes'] :
        #   vGrid.label(text=vS)

        vCol.separator()

    bpy.context.window_manager.popover(asset_info_draw, ui_units_x=15)


@reporting.handle_draw()
def f_NotificationBanner(notifications, layout):
    """General purpose notification banner UI draw element."""

    def build_mode(url, action, notification_id):
        return "notify@{}@{}@{}".format(url, action, notification_id)

    if not notifications:
        return

    box = layout.box()
    row = box.row(align=True)
    main_col = row.column(align=True)

    for i, notice in enumerate(notifications):
        first_row = main_col.row(align=False)
        x_row = first_row  # x_row is the row to add the x button to, if there.

        if notice.action == Notification.ActionType.OPEN_URL:
            panel_width = cTB.vWidth / cTB.get_ui_scale()

            # Empirical for width for "Beta addon: [Take survey]" specifically.
            single_row_width = 250
            if panel_width > single_row_width:
                # Single row with text + button.
                # TODO: generalize this for notification message and length,
                # and if dismiss is included.
                first_row.alert = True
                first_row.label(text=notice.title)
                first_row.alert = False
                ops = first_row.operator(
                    "poliigon.poliigon_link",
                    icon=notice.icon or "NONE",
                    text=notice.ac_open_url_label,
                )
                if notice.tooltip:
                    ops.vTooltip = notice.tooltip
                ops.vMode = build_mode(
                    notice.ac_open_url_address,
                    notice.ac_open_url_label,
                    notice.notification_id)

            else:
                # Two rows (or more, if text wrapping).
                col = first_row.column(align=True)
                col.alert = True
                # Empirically found squaring below worked best for 1 & 2x displays,
                # which accounts for the box+panel padding and the 'x' button.
                if notice.allow_dismiss:
                    padding_width = 32 * cTB.get_ui_scale()
                else:
                    padding_width = 17 * cTB.get_ui_scale()
                cTB.f_Label(cTB.vWidth - padding_width, notice.title, col)
                col.alert = False

                second_row = main_col.row(align=True)
                second_row.scale_y = 1.0
                ops = second_row.operator(
                    "poliigon.poliigon_link",
                    icon=notice.icon or "NONE",
                    text=notice.ac_open_url_label,
                )
                if notice.tooltip:
                    ops.vTooltip = notice.tooltip
                ops.vMode = build_mode(
                    notice.ac_open_url_address,
                    notice.ac_open_url_label,
                    notice.notification_id)

        elif notice.action == Notification.ActionType.UPDATE_READY:
            panel_width = cTB.vWidth / cTB.get_ui_scale()

            # Empirical for width for "Update ready: Download | logs".
            single_row_width = 300
            if panel_width > single_row_width:
                # Single row with text + button.
                first_row.alert = True
                first_row.label(text=notice.title)
                first_row.alert = False
                splitrow = first_row.split(factor=0.7, align=True)
                splitcol = splitrow.split(align=True)

                ops = splitcol.operator(
                    "poliigon.poliigon_link",
                    icon=notice.icon or "NONE",
                    text=str(notice.ac_update_ready_download_label),
                )
                if notice.tooltip:
                    ops.vTooltip = notice.tooltip
                ops.vMode = build_mode(
                    notice.ac_update_ready_download_url,
                    notice.ac_update_ready_download_label,
                    notice.notification_id)

                splitcol = splitrow.split(align=True)
                ops = splitcol.operator(
                    "poliigon.poliigon_link",
                    text=str(notice.ac_update_ready_logs_label),
                )
                if notice.tooltip:
                    ops.vTooltip = "See changes in this version"
                ops.vMode = build_mode(
                    notice.ac_update_ready_logs_url,
                    notice.ac_update_ready_logs_label,
                    notice.notification_id)
            else:
                # Two rows (or more, if text wrapping).
                col = first_row.column(align=True)
                col.alert = True
                if notice.allow_dismiss:
                    padding_width = 32 * cTB.get_ui_scale()
                else:
                    padding_width = 17 * cTB.get_ui_scale()
                cTB.f_Label(cTB.vWidth - padding_width, notice.title, col)
                col.alert = False

                second_row = main_col.row(align=True)
                splitrow = second_row.split(factor=0.7, align=True)
                splitcol = splitrow.split(align=True)
                ops = splitcol.operator(
                    "poliigon.poliigon_link",
                    icon=notice.icon or "NONE",
                    text=str(notice.ac_update_ready_download_label),
                )
                if notice.tooltip:
                    ops.vTooltip = notice.tooltip
                ops.vMode = build_mode(
                    notice.ac_update_ready_download_url,
                    notice.ac_update_ready_download_label,
                    notice.notification_id)
                splitcol = splitrow.split(align=True)
                ops = splitcol.operator(
                    "poliigon.poliigon_link",
                    text=str(notice.ac_update_ready_logs_label),
                )
                if notice.tooltip:
                    ops.vTooltip = notice.tooltip
                ops.vMode = build_mode(
                    notice.ac_update_ready_logs_url,
                    notice.ac_update_ready_logs_label,
                    notice.notification_id)

        elif notice.action == Notification.ActionType.POPUP_MESSAGE:
            panel_width = cTB.vWidth / cTB.get_ui_scale()

            single_row_width = 250
            if panel_width > single_row_width:
                # Single row with text + button.
                first_row.alert = True
                first_row.label(text=notice.title)
                first_row.alert = False
                ops = first_row.operator(
                    "poliigon.popup_message",
                    icon=notice.icon or "NONE",
                    text="View"
                )
                if notice.tooltip:
                    ops.vTooltip = notice.tooltip
                ops.message_body = notice.ac_popup_message_body
                if notice.ac_popup_message_url:
                    ops.message_url = notice.ac_popup_message_url

            else:
                # Two rows (or more, if text wrapping).
                col = first_row.column(align=True)
                col.alert = True
                # Empirically found squaring below worked best for 1 & 2x displays,
                # which accounts for the box+panel padding and the 'x' button.
                if notice.allow_dismiss:
                    padding_width = 32 * cTB.get_ui_scale()
                else:
                    padding_width = 17 * cTB.get_ui_scale()
                cTB.f_Label(cTB.vWidth - padding_width, notice.title, col)
                col.alert = False

                second_row = main_col.row(align=True)
                second_row.scale_y = 1.0
                ops = second_row.operator(
                    "poliigon.popup_message",
                    icon=notice.icon or "NONE",
                    text="View",
                )
                if notice.tooltip:
                    ops.vTooltip = notice.tooltip
                ops.message_body = notice.ac_popup_message_body
                if notice.ac_popup_message_url:
                    ops.message_url = notice.ac_popup_message_url

        else:
            main_col.label(text=notice.title)
            print("Invalid notifcation type")

        if notice.allow_dismiss:
            right_col = x_row.column(align=True)
            ops = right_col.operator(
                "poliigon.close_notification", icon="X", text="", emboss=False)
            ops.notification_index = i

    layout.separator()


# .............................................................................
# Draw panel
# .............................................................................


class POLIIGON_PT_toolbox(Panel):
    bl_idname = "POLIIGON_PT_toolbox"
    bl_label = "Poliigon"
    bl_category = "Poliigon"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    @reporting.handle_draw()
    def draw(self, context):
        f_BuildUI(self, context)


# .............................................................................
# Utilities
# .............................................................................


def get_model_op_details(asset_name, asset_type, size):
    """Get details to use in the ui for a given model and size."""
    default_lod = cTB.vSettings["lod"]
    asset_data = cTB.vAssets["local"][asset_type][asset_name]
    downloaded = asset_data["sizes"]

    if len(asset_data["lods"]):
        lod = cTB.f_GetClosestLod(asset_data["lods"], default_lod)
    else:
        lod = ""

    coll_name = construct_model_name(asset_name, size, lod)

    coll = bpy.data.collections.get(coll_name)
    if coll:
        in_scene = True
    else:
        in_scene = False

    label = ""
    tip = ""
    if size in downloaded:
        if in_scene:
            if lod:
                label = f"{size} {lod} (import again)"
                tip = f"Import {size} {lod} again\n{asset_name}"
            else:                   
                label = f"{size} (import again)"
                tip = f"Import {size} again\n{asset_name}"
        else:
            if lod:
                label = f"{size} {lod} (import)"
                tip = f"Import {size} {lod}\n{asset_name}"
            else:
                label = f"{size} (import)"
                tip = f"Import {size}\n{asset_name}"

    return lod, label, tip


# .............................................................................
# Registration
# .............................................................................

def register():
    bpy.utils.register_class(POLIIGON_PT_toolbox)


def unregister():
    bpy.utils.unregister_class(POLIIGON_PT_toolbox)
