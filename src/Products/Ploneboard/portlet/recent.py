from zope.interface import implements
from zope import schema
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.formlib.form import Fields
from plone.memoize.view import memoize
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.i18n.normalizer.interfaces import IIDNormalizer

from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from Products.Ploneboard.utils import PloneboardMessageFactory as _


class IRecentConversationsPortlet(IPortletDataProvider):
    """A portlet which shows recent Ploneboard conversations.
    """

    title = schema.TextLine(title=_("title_title",
                                default="Portlet title"),
                        required=True,
                        default="Recent messages")

    count = schema.Int(title=_("title_count",
                                default="Number of items to display"),
                       description=_("help_count",
                                default="How many items to list."),
                       required=True,
                       default=5)


    forum = schema.Choice(title=_("title_forum",
                                 default = "Limit to specific board or forum"),
                          description=_("help_forum", default="Limit recent conversations to a specific forum"),
                          vocabulary="ploneboard.BoardsAndForumVocabulary",
                          required=False,
                          default="")                    


class Assignment(base.Assignment):
    implements(IRecentConversationsPortlet)

    title = "Recent messages"
    count = 5
    forum = ""

    def __init__(self, title=None, count=None, forum=None):
        if title is not None:
            self.title=title
        if count is not None:
            self.count=count
        if forum is not None:
            self.forum=forum


class Renderer(base.Renderer):
    def __init__(self, context, request, view, manager, data):
        base.Renderer.__init__(self, context, request, view, manager, data)

    @memoize
    def results(self):
        ct=getToolByName(self.context, "portal_catalog")
        normalize=getUtility(IIDNormalizer).normalize
        icons=getMultiAdapter((self.context, self.request),
                                name="plone").icons_visible()
        
        query = dict(object_provides="Products.Ploneboard.interfaces.IConversation",
                        sort_on="modified",
                        sort_order="reverse",
                        sort_limit=self.data.count)
        
        if self.data.forum !="":
        
            result = ct(UID=self.data.forum)
            if len(result)==1:
                #limit to specific forum
                query["path"] = result[0].getPath()

        brains=ct(query)[:self.data.count]

        def morph(brain):
            obj=brain.getObject()
            forum=obj.getForum()

            return dict(
                    title = brain.Title,
                    description = brain.Description,
                    url = brain.getURL()+"/view",
                    icon = icons and obj.getIconURL() or None,
                    forum_url = forum.absolute_url(),
                    forum_title = forum.title_or_id(),
                    review_state = normalize(brain.review_state),
                    portal_type = normalize(brain.portal_type),
                    date = brain.modified)

        return [morph(brain) for brain in brains]

    @property
    def available(self):
        return len(self.results())>0

    def update(self):
        self.conversations=self.results()

    @property
    def title(self):
        return self.data.title

    @property
    def next_url(self):

        if self.data.forum !="":
            ct=getToolByName(self.context, "portal_catalog")
            result = ct(UID=self.data.forum)
            if len(result)==1:
                #limit to specific forum
                return result[0].getURL()

        state=getMultiAdapter((self.context, self.request),
                                name="plone_portal_state")
        return state.portal_url()+"/ploneboard_recent"

    render = ViewPageTemplateFile("recent.pt")


class AddForm(base.AddForm):
    form_fields = Fields(IRecentConversationsPortlet)
    label = _("label_add_portlet",
                default="Add recent conversations portlet.")
    description = _("help_add_portlet",
            default="This portlet shows conversations with recent comments.")

    def create(self, data):
        return Assignment(title=data.get("title"), count=data.get("count"))


class EditForm(base.EditForm):
    form_fields = Fields(IRecentConversationsPortlet)
    label = _("label_add_portlet",
                default="Add recent conversations portlet.")
    description = _("help_add_portlet",
            default="This portlet shows conversations with recent comments.")

def BoardsAndForumVocabularyFactory(context):
    """Vocabulary factory for supplying a vocabulary of users in the site for the injected responsible person field"""
    tool = getToolByName(context, 'uid_catalog')
    items = [SimpleTerm(r.UID, r.UID, r.Title.decode('utf-8')) for r in tool(portal_type=["PloneboardForum","Ploneboard"])]
    return SimpleVocabulary(items)
