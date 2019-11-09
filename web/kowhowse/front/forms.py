from django import forms
from ..bitter import *


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['description']
