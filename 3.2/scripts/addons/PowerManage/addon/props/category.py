import bpy


class Category(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Name',
        description='The name of the category',
    )

    expand: bpy.props.BoolProperty(
        name='Expand',
        default=True,
    )

    def icon(self) -> str:
        return 'DISCLOSURE_TRI_DOWN' if self.expand else 'DISCLOSURE_TRI_RIGHT'
