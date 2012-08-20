from django.views.generic import DetailView
from models import YawdElfinderTestModel

class IndexView(DetailView):
    template_name = 'index.html'
    
    def get_object(self):
        return YawdElfinderTestModel.objects.get(pk=1)
