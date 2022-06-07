from . import utils
from . import props
from . import ops
from . import ui

modules = (
    utils,
    props,
    ops,
    ui,
)


def register():
    for module in modules:
        module.register()

    utils.meta.update_panel_category()


def unregister():
    for module in reversed(modules):
        module.unregister()
