"""
Syntax sugar for bitter.py that hides away relational DB shenanigans so
the developer can create surveys with just basic Python.
"""
from os import path


class Describable:
    def __init__(self, description):
        self.description = description

    def __str__(self):
        return self.description


class Instructable:
    def __init__(self, instruction):
        self.instruction = instruction


class Survey(Describable, Instructable):
    def __init__(self, description, instruction):
        Describable.__init__(self, description)
        Instructable.__init__(self, instruction)
        self.sections = []

    @property
    def systems(self):
        return {sample.system for sample in self.samples}

    @property
    def samples(self):
        return {sample
                for section in self
                for question in section
                for sample in question}

    def __iter__(self):
        return iter(self.sections)


class System(Describable):
    def __init__(self, description):
        Describable.__init__(self, description)

    def __hash__(self):
        return hash(self.description)

    def __eq__(self, other):
        return isinstance(other, System) and \
               self.description == other.description

    def __ne__(self, other):
        return not(self == other)


class Audio(Describable):
    REFERENCE = 'R'
    ANCHOR = 'A'
    STIMULUS = 'S'

    def __init__(self, description, system, data, role=STIMULUS):
        Describable.__init__(self, description)
        self.system = system
        self.data = data
        self.role = role

    def __hash__(self):
        return hash((self.description, self.system, self.data, self.role))

    def __eq__(self, other):
        return isinstance(other, Audio) and \
               (self.description, self.system, self.data, self.role) == \
               (other.description, other.system, other.data, self.role)

    def __ne__(self, other):
        return not(self == other)


class Section(Describable, Instructable):
    def __init__(self, description, instruction):
        Describable.__init__(self, description)
        Instructable.__init__(self, instruction)
        self.questions = []

    def __iter__(self):
        return iter(self.questions)


class End(Section):
    pass


class Question(Describable, Instructable):
    def __init__(self, description, instruction):
        Describable.__init__(self, description)
        Instructable.__init__(self, instruction)
        self.samples = []

    def __iter__(self):
        return iter(self.samples)


class AbQuestion(Question):
    def __init__(self, description, instruction):
        Question.__init__(self, description, instruction)


class AbxQuestion(Question):
    def __init__(self, description, instruction):
        Question.__init__(self, description, instruction)


class MushraQuestion(Question):
    def __init__(self, description, instruction, num_anchors=None, num_stimuli=None):
        Question.__init__(self, description, instruction)
        self.num_anchors = num_anchors
        self.num_stimuli = num_stimuli


class MosLevel(Describable):
    def __init__(self, description, value):
        Describable.__init__(self, description)
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def __lt__(self, other):
        return self.value < other.value

    def __gt__(self, other):
        return self.value > other.value

    def __le__(self, other):
        return not (self > other)

    def __ge__(self, other):
        return not (self < other)

    def __eq__(self, other):
        return self >= other and self <= other

    def __ne__(self, other):
        return not(self == other)


class MosQuestion(Question):
    def __init__(self, description, instruction, levels):
        Question.__init__(self, description, instruction)
        self.levels = levels
