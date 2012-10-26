from haystack import indexes
from cfda.models import Program


class ProgramIndex(indexes.SearchIndex, indexes.Indexable):
    type = 'cfda'
    program_number = indexes.CharField(model_attr='program_number') 
    program_title = indexes.CharField(model_attr='program_title')
    text = indexes.CharField(document=True)
    
    def get_model(self):
        return Program

    def prepare_text(self, object):
        tmpl = u"{obj.program_number} {obj.program_title}"
        return tmpl.format(obj=object
                          ).replace('_', ' '
                          ).encode('utf-8')

    def prepare_program_title(self, object):
        return object.program_title.replace('_', ' ').encode('utf-8')
                 
    def get_queryset(self):
        "Used when the entire index for model is updated."
        
        return Program.objects.filter(types_of_assistance__financial=True ).distinct()

