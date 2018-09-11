from django.contrib import admin

from .models import *

for m in [Survey, Question, AbQuestion, AbxQuestion, MushraQuestion, MosQuestion, Audio, Subject, Page]:
    admin.site.register(m)
