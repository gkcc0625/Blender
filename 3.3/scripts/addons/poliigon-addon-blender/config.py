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

import os
from . import reporting

try:
    import ConfigParser
except:
    import configparser as ConfigParser


class PoliigonEnvironment():
    """Poliigon environment used for assisting in program control flow."""

    api_url: str = ""
    env: str = ""
    host: str = ""

    required_attrs = ["api_url", "env"]

    def __init__(self):
        base = os.path.dirname(__file__)
        self._update_files(base)
        self._load_env(base)

    def _load_env(self, path):
        env_file = os.path.join(path, "env.ini")
        if os.path.exists(env_file):
            try:
                # Read .ini here and set values
                # https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.optionxform
                config = ConfigParser.ConfigParser()
                config.optionxform = str
                config.read(env_file)

                self.api_url = config.get("DEFAULT", "api_url")
                self.env = config.get("DEFAULT", "env_name")
                self.host = config.get("DEFAULT", "host")

                for k, v in vars(self).items():
                    if k in self.required_attrs and v in [None, ""]:
                        raise ValueError(f"Attribute '{k}' not set!")
            except ValueError as e:
                print("Could not load environment for the Poliigon Addon for Blender!")
                raise
        else:
            # Assume production environment and set fallback values
            self.api_url = "https://api.poliigon.com/api/v1"
            self.env = "prod"
            self.host = ""

    def _update_files(self, path):
        """Updates files in the specified path within the addon."""
        update_key = "_update"
        search_key = "env" + update_key
        files_to_update = [f for f in os.listdir(path)
                           if os.path.isfile(os.path.join(path, f))
                           and os.path.splitext(f)[0].endswith(search_key)]

        for f in files_to_update:
            f_split = os.path.splitext(f)
            tgt_file = f_split[0][:-len(update_key)] + f_split[1]

            try:
                os.replace(os.path.join(path, f), os.path.join(path, tgt_file))
                print(f"Updated {tgt_file}")
            except PermissionError as e:
                reporting.capture_message("file_permission_error", e, "error")
            except OSError as e:
                reporting.capture_message("os_error", e, "error")


environ = PoliigonEnvironment()
