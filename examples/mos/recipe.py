#!/usr/bin/env python
from pathlib import Path

from kowhowse.sweet import *


# IMPORTANT! Make sure to name the main function survey_definition
def survey_definition():
    RESDIR = Path(__file__).parent/'res'
    SMPDIR = Path(__file__).parents[1]/'media'

    # Create survey with a welcome message
    survey = Survey(
        description='Survey with MOS questions',
        instruction=RESDIR/'welcome.html'
    )

    # Create systems to compare
    systems = [System(c) for c in 'AB']

    # Part 1 with instruction
    section = Section(
        description='Part 1',
        instruction=RESDIR/'instruction1.html'
    )

    # Create MOS scale
    scale = MosScale(
        'Naturalness',
        [
            MosLevel(desc, value)
            for value, desc in enumerate('Poor Okay Good'.split())
        ]
    )

    # Create MOS question for each sentence
    for sentence in ['KingDonkeyEars_011_001', 'PussInBoots_002_002']:
        question = MosQuestion(sentence, None, [scale])
        for system, directory in (
            (systems[0], SMPDIR/'a'),
            (systems[1], SMPDIR/'b')
        ):
            audio = Audio(
                f'{system}:{sentence}',
                system,
                (directory/sentence).with_suffix('.wav')
            )
            question.samples.append(audio)
        section.questions.append(question)
    survey.sections.append(section)

    # In Part 2, we create MOS questions with multiple scales
    section = Section(
        description='Part 2',
        instruction=RESDIR/'instruction2.html'
    )
    
    scales = [
        scale, # Naturalness scale from Part 1
        MosScale(
            'Quality',
            [
                MosLevel(desc, value)
                for desc, value in {
                    'Terrible': -3.5,
                    'Bad': -2,
                    'Okay': 0,
                    'Good': 1,
                    'Excellent': 2
                }.items()
            ]
        ),
    ]

    for sentence in ['KnightsAndCastles_006_003', 'LittleRedRidingHood_003_003']:
        question = MosQuestion(sentence, None, scales)
        for system, directory in (
            (systems[0], SMPDIR/'a'),
            (systems[1], SMPDIR/'b')
        ):
            audio = Audio(
                f'{system}:{sentence}',
                system,
                (directory/sentence).with_suffix('.wav')
            )
            question.samples.append(audio)
        section.questions.append(question)
    survey.sections.append(section)

    # Dummy Section for concluding thank you message
    thanks = Section(
        description='Thanks',
        instruction=RESDIR/'thanks.html'
    )
    survey.sections.append(thanks)

    return survey
