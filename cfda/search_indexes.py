import datetime
from haystack import indexes
from haystack.sites import site
from cfda.models import Program


class ProgramIndex(indexes.SearchIndex):
    
    type = 'cfda'
    text = indexes.CharField(document=True)
    
   
    def prepare_text(self, object):
        
#       text = getattr(object, 'objectives')
#limit to just program title. Objectives produces a lot of noise
        text = getattr(object, 'program_title')

        return text
         
    def get_queryset(self):
        "Used when the entire index for model is updated."
        
        return Program.objects.filter(types_of_assistance__financial=True ).distinct()
        #return Program.objects.all()
    

site.register(Program, ProgramIndex)
