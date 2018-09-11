from django.core.management.base import BaseCommand, CommandError
from survey.models import *
import sys, os
from os import path
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
from django.conf import settings
from argparse import FileType

class Command(BaseCommand):
    help = 'Create survey'

    def add_arguments(self, parser):
        parser.add_argument('script')

    def handle(self, *args, **kwargs):
        script = kwargs['script']
        spec = spec_from_file_location("recipe", path.realpath(script))
        recipe = module_from_spec(spec)
        spec.loader.exec_module(recipe)

        _survey = recipe.survey_definition()

        survey = Survey(description=_survey.description)
        if _survey.instruction:
            with open(_survey.instruction) as f:
                survey.instruction.save(path.basename(_survey.instruction), File(f))
        survey.save()

        systems = {}
        samples = {}
        for _section in _survey:
            section = survey.sections.create(description=_section.description)
            if _section.instruction:
                with open(_section.instruction) as f:
                    section.instruction.save(path.basename(_section.instruction), File(f))
            section.save()

            for _question in _section:
                question = {
                    'AbQuestion': AbQuestion,
                    'AbxQuestion': AbxQuestion,
                    'MushraQuestion': MushraQuestion,
                    'MosQuestion': MosQuestion
                }[_question.__class__.__name__](
                    section=section,
                    description=_question.description)

                if _question.instruction:
                    with open(_question.instruction) as f:
                        question.instruction.save(path.basename(_question.instruction), File(f))
                question.save()

                for _sample in _question:
                    system = systems.get(_sample.system, None)
                    if system is None:
                        systems[_sample.system] = System(description=_sample.system.description)
                        system = systems[_sample.system]
                        system.save()

                    sample = samples.get(_sample, None)
                    if sample is None:
                        samples[_sample] = Audio(
                            description=_sample.description,
                            system=system
                        )
                        sample = samples[_sample]
                        with open(_sample.data, 'rb') as f:
                            sample.data.save(path.join(system.description, path.basename(_sample.data)), File(f))
                        sample.save()
                    question.samples.add(sample)
                question.save()
            section.save()
        survey.save()

    # def handle(self, *args, **kwargs):
    #     RESDIR = path.join(path.dirname(settings.BASE_DIR), 'res')
    #
    #     # Create survey
    #     survey = Survey(title='Demo survey')
    #     with open(path.join(RESDIR, 'welcome.html')) as f:
    #         survey.text.save('survey1.html', File(f))
    #     survey.save()
    #
    #     # Create systems to evaluate
    #     for name in ['A', 'B']:
    #         System(name=name).save()
    #
    #     sentences = ['KingDonkeyEars_011_001', 'PussInBoots_002_002']
    #
    #     # Add samples
    #     SYNDIR = path.join(os.sep, 'home', 'kurt', 'Documents', 'ed', 'thesis', 'thesis', 'data', 'syn')
    #     for sentence in sentences:
    #         for system, directory in {'A': path.join('D', '34', 'test_0.0_0.0'),
    #                                   'B': path.join('D_D', '34_31', 'test_0.0_0.0')}.items():
    #             audio = Audio(system=System.objects.get(name=system))
    #             with open(path.join(SYNDIR, directory, sentence+'.wav'), 'rb') as f:
    #                 audio.data.save('{}/{}.wav'.format(system, sentence), File(f))
    #             audio.save()
    #
    #
    #     # Add sections
    #     for n in range(1):
    #         section = survey.sections.create()
    #         with open(path.join(RESDIR, 'instruction1.html')) as f:
    #             section.text.save('section1.html', File(f))
    #         section.save()
    #
    #         # Add questions
    #         for sentence in sentences:
    #             question = section.abxquestions.create()
    #             question.save()
    #             # Add samples
    #             question.samples.add(Audio.objects.get(data=path.join('audio', 'A', sentence+'.wav')))
    #             question.samples.add(Audio.objects.get(data=path.join('audio', 'B', sentence+'.wav')))
    #             question.save()
    #         section.save()
    #     survey.save()
