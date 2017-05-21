"""Migrate from 0.1b1 to 1.0b.
"""
# Zope imports
from ZODB.PersistentMapping import PersistentMapping
from Acquisition import aq_base

# CMF imports
from Products.CMFCore.utils import getToolByName

# Product imports


class Migration(object):
    """Migrate from 0.1b1 to 1.0b.
    """

    def __init__(self, site, out):
        self.site = site
        self.out = out
        self.catalog = getToolByName(self.site, 'portal_catalog')

    def migrate(self):
        """Run migration on site object passed to __init__.
        """
        print("Migrating Ploneboard 0.1b1 -> 1.0b", file=self.out)
        self.findAndCatalogAndClean()

    def findAndCatalogAndClean(self):
        """Manually find all the ploneboard types, recatalog them, and remove
        their old index objects that are just ZODB turds now.
        """
        # Ploneboard instances themselves should still be cataloged...
        pb_brains = self.catalog(portal_type='Ploneboard')
        forum_count = 0
        conv_count = 0
        comm_count = 0
        for pb in [brain.getObject() for brain in pb_brains]:
            if pb.hasObject('ploneboard_catalog'):
                pb._delObject('ploneboard_catalog')
                msg = "Removed stale 'ploneboard_catalog' from Ploneboard at %s."
                print(msg % '/'.join(pb.getPhysicalPath()), file=self.out)
            else:
                msg = "Checked for stale 'ploneboard_catalog' object on %s, but not present."
                print(msg % '/'.join(pb.getPhysicalPath()), file=self.out)
            # Directly access the stored forums.  The Ploneboard API won't work here
            for forum in pb.objectValues('PloneboardForum'):
                forum.reindexObject()
                self._cleanIndex(forum)
                forum_count += 1
                for conv in forum.objectValues('PloneboardConversation'):
                    conv.reindexObject()
                    self._cleanIndex(conv)
                    conv_count += 1
                    for comm in conv.objectValues('PloneboardComment'):
                        comm.reindexObject()
                        comm_count += 1
        msg = "Indexed and cleaned %s forums, %s conversations, and %s comments."
        print(msg % (forum_count, conv_count, comm_count), file=self.out)

    def _cleanIndex(self, ob):
        if getattr(aq_base(ob), '_index', None) is not None:
            delattr(ob, '_index')
            msg = "Removed stale '_index' from %s at %s."
            print(msg % (ob.meta_type, '/'.join(ob.getPhysicalPath())), file=self.out)
        else:
            msg = "Checked for stale '_index' attribute on '%s' at %s, but not present."
            print(msg % (ob.meta_type, '/'.join(ob.getPhysicalPath())), file=self.out)

