from django import forms
from django.forms import ModelForm
from ..bitter import *


class SubjectForm(ModelForm):
    class Meta:
        model = Subject
        fields = ['description']
