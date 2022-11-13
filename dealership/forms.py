from django import forms

from category.models import Category
from dealership.models import Dealership


class DealershipForm(forms.ModelForm):
    category = forms.ModelMultipleChoiceField(queryset=Category.objects.all())

    class Meta:
        model = Dealership
        fields = '__all__'

    def __init__(self, show_fields=None, *args, **kwargs):
        super(DealershipForm, self).__init__(*args, **kwargs)

        for meta_field in list(self.fields):
            if meta_field not in show_fields:
                self.fields.pop(meta_field)
