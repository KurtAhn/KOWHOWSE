import sys, os
from pathlib import Path
from importlib import import_module
from importlib.util import spec_from_file_location, module_from_spec
from argparse import FileType

from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.conf import settings

from kowhowse import bitter as B, sweet as S


class Command(BaseCommand):
    help = 'Create survey'

    def add_arguments(self, parser):
        parser.add_argument('script')

    def create_survey(self, script):
        spec = spec_from_file_location('recipe', Path(script).resolve())
        recipe = module_from_spec(spec)
        spec.loader.exec_module(recipe)

        _survey = recipe.survey_definition()
        survey = B.Survey(
            description=_survey.description,
            public=_survey.public
        )
        if _survey.instruction:
            with open(_survey.instruction) as f:
                survey.instruction.save(
                    Path(_survey.instruction).name,
                    File(f)
                )
        survey.save()
        return _survey, survey

    def handle(self, *args, **kwargs):
        _survey, survey = self.create_survey(kwargs['script'])

        systems = {}
        samples = {}
        for _section in _survey:
            if _section.__class__ == S.Section:
                section = B.Section(
                    survey=survey,
                    description=_section.description
                )
            else:
                section = B.End(
                    survey=survey,
                    description=_section.description
                )
            section.save()

            if _section.instruction:
                with open(_section.instruction) as f:
                    section.instruction.save(
                        Path(_section.instruction).name,
                        File(f)
                    )
            section.save()

            for _question in _section:
                question = getattr(B, _question.__class__.__name__)(
                    section=section, description=_question.description
                )

                if _question.instruction:
                    with open(_question.instruction) as f:
                        question.instruction.save(
                            Path(_question.instruction).name,
                            File(f)
                        )

                if isinstance(question, B.MosQuestion):
                    question.num_scales = len(_question.scales)
                    question.save()

                    for _scale in _question.scales:
                        try:
                            question.scales.add(
                                B.MosScale.objects.get(
                                    description=_scale.description
                                )
                            )
                        except (
                            B.MosScale.DoesNotExist,
                            B.MosScale.MultipleObjectsReturned
                        ):
                            scale = B.MosScale(
                                description=_scale.description
                            )
                            scale.save()
                            question.scales.add(scale)

                            for _level in _scale.levels:
                                level = B.MosLevel(
                                    scale=scale,
                                    description=_level.description,
                                    value=_level.value
                                )
                                level.save()

                    # question.num_levels = len(_question.levels)
                    # question.save()
                    # for _level in _question.levels:
                    #     try:
                    #         question.levels.add(B.MosLevel.objects.get(
                    #             description=_level.description,
                    #             value=_level.value))
                    #     except (B.MosLevel.DoesNotExist,
                    #             B.MosLevel.MultipleObjectsReturned):
                    #         level = B.MosLevel(
                    #             description=_level.description,
                    #             value=_level.value)
                    #         level.save()
                    #         question.levels.add(level)
                else:
                    question.save()

                for _sample in _question:
                    system = systems.get(_sample.system, None)
                    if system is None:
                        systems[_sample.system] = B.System(description=_sample.system.description)
                        system = systems[_sample.system]
                        system.save()

                    sample = samples.get(_sample, None)
                    if sample is None:
                        samples[_sample] = B.Audio(
                            description=_sample.description,
                            system=system,
                            role=_sample.role
                        )
                        sample = samples[_sample]
                        with open(_sample.data, 'rb') as f:
                            sample.data.save(
                                Path(system.description)/Path(_sample.data).name,
                                File(f)
                            )
                        sample.save()
                    question.samples.add(sample)
                question.save()
            section.save()
        survey.save()
