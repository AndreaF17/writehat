from .base import *

class Component(BaseComponent):

    default_name = 'Table of Contents'
    htmlTemplate = 'componentTemplates/TableOfContents.html'
    iconType = 'fas fa-list'
    iconColor = 'var(--blue)'


    def preprocess(self, context):

        toc_components = self.buildToc(context['report'].components, 0)
        context['toc_components'] = toc_components
        return context


    @classmethod
    def buildToc(cls, components, level=0):
        '''
        Build a list of components
        '''

        toc_components = []
        for c in components:
            if c.includeInToc and c.showTitle:
                component = { 
                    "name": c.name,
                    "id": c._id,
                    "level": level,
                    "index": c.index
                }
                toc_components.append(component)

            if c.includeInToc and hasattr(c, 'toc_entries'):
                for entry in c.toc_entries() or []:
                    toc_components.append({
                        "name": entry.get("name", ""),
                        "id": entry.get("id", ""),
                        "level": entry.get("level", level),
                        "index": entry.get("index", ""),
                    })

            if c.includeInToc and c.showTitle and len(c.children):
                toc_components += cls.buildToc(c.children, level + 1)

        return toc_components
