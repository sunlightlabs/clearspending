import datetime
from haystack import indexes
from haystack.sites import site
from cfda.models import Program


class ProgramIndex(indexes.SearchIndex):
    
    type = 'cfda'
    text = indexes.CharField(document=True)
    
   
    def prepare_text(self, object):
        
        text = getattr(object, 'objectives')
        text += getattr(object, 'program_title')

        return text
         
    def get_queryset(self):
        "Used when the entire index for model is updated."
        
        # limit cfda indexing to programs that are included in a sector
        return Program.objects.all()
    

site.register(Program, ProgramIndex)
