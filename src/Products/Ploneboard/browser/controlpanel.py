from zope.schema import Tuple, Bool
from zope.schema import Choice
from zope.interface import implements
from zope.interface import Interface
from zope.formlib.form import FormFields
from zope.component import adapts
from plone.app.controlpanel.form import ControlPanelForm
from plone.app.controlpanel.widgets import MultiCheckBoxVocabularyWidget
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Ploneboard.utils import PloneboardMessageFactory as _


class ITransformSchema(Interface):
    enabled_transforms = Tuple(
            title=_("label_transforms",
                default="Transforms"),
            description=_("help_transforms",
                default="Select the text transformations that should be "
                        "used for comments posted in Ploneboard "
                        "conversations. Text transformations alter the "
                        "text entered by the user, either to remove "
                        "potentially malicious HTML tags, or to add "
                        "additional functionality, such as making links "
                        "clickable."),
            required=True,
            missing_value=set(),
            value_type=Choice(
                vocabulary="Products.Ploneboard.AvailableTransforms"))

    enable_anon_name = Bool(
            title=_("label_anon_nick",
                default="Anonymous name"),
            description=_("help_anon_nick",
                default="If selected, anonymous users can insert a name in their comments."),
            required=False)


class ControlPanelAdapter(SchemaAdapterBase):
    adapts(IPloneSiteRoot)
    implements(ITransformSchema)

    def __init__(self, context):
        super(ControlPanelAdapter, self).__init__(context)
        self.tool = getToolByName(self.context, "portal_ploneboard")

    def get_enabled_transforms(self):
        return self.tool.getEnabledTransforms()

    def set_enabled_transforms(self, value):
        for t in self.tool.getTransforms():
            self.tool.enableTransform(t, t in value)

    def get_enable_anon_name(self):
        return self.tool.getEnableAnonName()

    def set_enable_anon_name(self, value):
        self.tool.setEnableAnonName(value)

    enabled_transforms = property(get_enabled_transforms, set_enabled_transforms)
    enable_anon_name = property(get_enable_anon_name, set_enable_anon_name)


class ControlPanel(ControlPanelForm):
    form_fields = FormFields(ITransformSchema)
    form_fields["enabled_transforms"].custom_widget = MultiCheckBoxVocabularyWidget

    label = _("ploneboard_configuration",
            default="Ploneboard configuration")
    description = _("description_ploneboard_config",
            default="Here you can configure site settings for Ploneboard.")

    form_name = _("ploneboard_transform_panel",
            default="Text transformations")
