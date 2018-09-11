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
    def __init__(self, description, system, data):
        Describable.__init__(self, description)
        self.system = system
        self.data = data

    def __hash__(self):
        return hash((self.description, self.system, self.data))

    def __eq__(self, other):
        return isinstance(other, Audio) and \
               (self.description, self.system, self.data) == \
               (other.description, other.system, other.data)

    def __ne__(self, other):
        return not(self == other)


class Section(Describable, Instructable):
    def __init__(self, description, instruction):
        Describable.__init__(self, description)
        Instructable.__init__(self, instruction)
        self.questions = []

    def __iter__(self):
        return iter(self.questions)


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
    def __init__(self, description, instruction, num_choices):
        Question.__init__(self, description, instruction)
        self.num_choices = num_choices


class MosQuestion(Question):
    def __init__(self, description, instruction, num_levels):
        Question.__init__(self, description, instruction)
        self.num_levels = num_levels
