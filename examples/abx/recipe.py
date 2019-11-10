#!/usr/bin/env python
from pathlib import Path

from kowhowse.sweet import *


# IMPORTANT! Make sure to name the main function survey_definition
def survey_definition():
    RESDIR = Path(__file__).parent/'res'
    SMPDIR = Path(__file__).parents[1]/'media'

    # Create survey with a welcome message
    survey = Survey(
        description='Survey with AB and ABX questions',
        instruction=RESDIR/'welcome.html'
    )

    # Create systems to compare and map them to directories containing
    # audio files produced by respective systems.
    sysdirs = {
        System('A'): SMPDIR/'a',
        System('B'): SMPDIR/'b'
    }

    # Section 1 (AB)
    survey.sections.append(
        section_definition(
            'Part 1',
            RESDIR/'instruction1.html',
            'AB',
            sysdirs,
            ['KingDonkeyEars_011_001', 'PussInBoots_002_002']
        )
    )

    # Section 2 (ABX)
    survey.sections.append(
        section_definition(
            'Part 2',
            RESDIR/'instruction2.html',
            'ABX',
            sysdirs,
            ['KingDonkeyEars_011_001', 'PussInBoots_002_002']
        )
    )

    # Ending
    thanks = End('fin', RESDIR/'thanks.html')
    survey.sections.append(thanks)

    # That's all!
    return survey


def section_definition(description, instruction_file, question_type, systems, sentences):
    if question_type not in 'AB ABN ABX ABXN'.split():
        raise ValueError('Invalid question type')
    create_question = (
        AbQuestion
        if question_type == 'AB' else
        AbxQuestion
    )

    # Create section header with instruction
    section = Section(
        description=description,
        instruction=instruction_file
    )
    for sentence in sentences:
        question = create_question(description=sentence, instruction=None)
        for system, directory in systems.items():
            audio = Audio(
                f'{system}:{sentence}',
                system,
                Path(directory)/f'{sentence}.wav'
            )
            question.samples.append(audio)
        section.questions.append(question)
    return section