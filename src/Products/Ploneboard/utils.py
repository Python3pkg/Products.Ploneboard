from AccessControl import ClassSecurityInfo, ModuleSecurityInfo
from AccessControl.class_init import InitializeClass
from Acquisition import Implicit, aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName
from ZODB.PersistentMapping import PersistentMapping
from zope.i18nmessageid import MessageFactory

from . import config


def importModuleFromName(module_name):
    """ import and return a module by its name """
    __traceback_info__ = (module_name, )
    m = __import__(module_name)
    try:
        for sub in module_name.split('.')[1:]:
            m = getattr(m, sub)
    except AttributeError as e:
        raise ImportError(str(e))
    return m

def changeOwnershipOf(object, userid, recursive=0):
    """Changes the ownership of an object. Stolen from Plone and CMFCore, but
    be less restrictive about where the owner is found.
    """
    user = None
    uf = object.acl_users
    while uf is not None:
        user = uf.getUserById(userid)
        if user is not None:
            break
        container = aq_parent(aq_inner(uf))
        parent = aq_parent(aq_inner(container))
        uf = getattr(parent, 'acl_users', None)

    if user is None:
        raise KeyError("User %s cannot be found." % userid)

    object.changeOwnership(user, recursive)

    def fixOwnerRole(object, user_id):
        # Get rid of all other owners
        owners = object.users_with_local_role('Owner')
        for o in owners:
            roles = list(object.get_local_roles_for_userid(o))
            roles.remove('Owner')
            if roles:
                object.manage_setLocalRoles(o, roles)
            else:
                object.manage_delLocalRoles([o])
        # Fix for 1750
        roles = list(object.get_local_roles_for_userid(user_id))
        roles.append('Owner')
        object.manage_setLocalRoles(user_id, roles)

    fixOwnerRole(object, user.getId())
    catalog_tool = getToolByName(object, 'portal_catalog')
    catalog_tool.reindexObject(object)

    if recursive:
        purl = getToolByName(object, 'portal_url')
        _path = purl.getRelativeContentURL(object)
        subobjects = [b.getObject() for b in \
                     catalog_tool(path={'query':_path,'level':1})]
        for obj in subobjects:
            fixOwnerRole(obj, user.getId())
            catalog_tool.reindexObject(obj)

class TransformDataProvider(Implicit):
    """ Base class for data providers """
    security = ClassSecurityInfo()
    security.declareObjectPublic()

    def __init__(self):
        self.config = PersistentMapping()
        self.config_metadata = PersistentMapping()

        self.config.update({'inputs' : {} })
        self.config_metadata.update({
            'inputs' : {
                'key_label' : '',
                'value_label' : '',
                'description' : ''}
            })

    security.declarePublic('setElement')
    def setElement(self, inputs):
        """ inputs - dictionary, but may be extended to new data types"""
        self.config['inputs'].update(inputs)

    def delElement(self, el):
        """ el - dictionary key"""
        del self.config['inputs'][el]

    security.declarePublic('getElements')
    def getElements(self):
        """ Returns mapping """
        return self.config['inputs']

    security.declarePublic('getConfigMetadata')
    def getConfigMetadata(self):
        """ Returns config metadata """
        return self.config_metadata['inputs']

InitializeClass(TransformDataProvider)


def finalizeSchema(schema):
    # Categorization
    if 'subject' in schema:
        schema.changeSchemataForField('subject', 'categorization')
    if 'relatedItems' in schema:
        schema.changeSchemataForField('relatedItems', 'categorization')
    if 'location' in schema:
        schema.changeSchemataForField('location', 'categorization')
    if 'language' in schema:
        schema.changeSchemataForField('language', 'categorization')

    # Dates
    if 'effectiveDate' in schema:
        schema.changeSchemataForField('effectiveDate', 'dates')
    if 'expirationDate' in schema:
        schema.changeSchemataForField('expirationDate', 'dates')
    if 'creation_date' in schema:
        schema.changeSchemataForField('creation_date', 'dates')
    if 'modification_date' in schema:
        schema.changeSchemataForField('modification_date', 'dates')

    # Ownership
    if 'creators' in schema:
        schema.changeSchemataForField('creators', 'ownership')
    if 'contributors' in schema:
        schema.changeSchemataForField('contributors', 'ownership')
    if 'rights' in schema:
        schema.changeSchemataForField('rights', 'ownership')

    # Settings
    if 'allowDiscussion' in schema:
        schema.changeSchemataForField('allowDiscussion', 'settings')
    if 'excludeFromNav' in schema:
        schema.changeSchemataForField('excludeFromNav', 'settings')
    if 'nextPreviousEnabled' in schema:
        schema.changeSchemataForField('nextPreviousEnabled', 'settings')

# Use PloneboardMessageFactory for translations in Python
PloneboardMessageFactory = MessageFactory(config.I18N_DOMAIN)
ModuleSecurityInfo('Products.Ploneboard.utils').declarePublic('PloneboardMessageFactory')