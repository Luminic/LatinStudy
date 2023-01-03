import logging
from typing import TypeAlias
from enum import Enum, IntEnum

a_macron = 'ā'
e_macron = 'ē'
i_macron = 'ī'
o_macron = 'ō'
u_macron = 'ū'


class Gender(Enum):
    Unknown = 0
    Masc = 1
    Fem = 2
    Neut = 3


class VocabType(Enum):
    """
    Values are not to be changed
    """

    Verb = 0
    Adverb = 1
    Noun = 2
    Adjective = 3
    Pronoun = 4
    Preposition = 5
    Conjunction = 6
    Interjection = 7


class Vocab:
    def __init__(self):
        self.description = ""
    
    def __hash__(self):
        return hash(self.description)


PrincipalParts: TypeAlias = tuple[str,str,str,str]

class Number(IntEnum):
    Singular = 0
    Plural   = 1

class Person(IntEnum):
    First  = 0 * len(Number)
    Second = 1 * len(Number)
    Third  = 2 * len(Number)

class Time(IntEnum):
    Present = 0 * len(Number) * len(Person)
    Past    = 1 * len(Number) * len(Person)
    Future  = 2 * len(Number) * len(Person)

class Aspect(IntEnum):
    Progressive = 0 * len(Number) * len(Person) * len(Time)
    Perfective  = 1 * len(Number) * len(Person) * len(Time)

class Tense(IntEnum):
    Present       = Time.Present + Aspect.Progressive
    Imperfect     = Time.Past    + Aspect.Progressive
    Future        = Time.Future  + Aspect.Progressive
    Perfect       = Time.Present + Aspect.Perfective
    Pluperfect    = Time.Past    + Aspect.Perfective
    FuturePerfect = Time.Future  + Aspect.Perfective

class Mood(IntEnum):
    Indicative  = 0
    Imperative  = 1
    Infinitive  = 2
    Subjunctive = 3

# def parsing_from_index(index:int, enum_type):
#     return int(len(enum_type))


class Verb(Vocab):
    @staticmethod
    def replace_ending(somestr:str, old:str, new:str):
        if somestr[-len(old):] == old:
            return somestr[:-len(old)] + new
        return somestr

    def __init__(self, principal_parts: PrincipalParts, english: list[str]):
        super().__init__()

        self.principal_parts = principal_parts
        self.english = english

        self.special_cases:dict[tuple[tuple[str, str], ...],str] = {}
        """
        Dictionary from the parsing of a case to an irregular conjugation for that parsing

        example keys
        `(("Mood", "Imperative"), ("Number", "Singular"))`
        or
        `(("Mood", "Indicative"), ("Number", "Singular"), ("Person", "First"), ("Tense", "Pluperfect"))`

        Mood must come first. The order of the others doesn't matter
        """

        self.conjugation:int = -1

        self.conjugations:list[list[str]|str|None] = [None] * 4
        """
        Access each conjugation the following way:

        `self.conjugations[Mood.Indicative][Number + Person + Tense]` or `self.conjugations[Mood.Indicative][Number + Person + Aspect + Time]` (since `Tense = Aspect + Time`)

        `self.conjugations[Mood.Imperative][Number]`

        `self.conjugations[Mood.Infinitive]`

        The subjunctive mood and passive tense are currently unimplemented
        """
    
    def __str__(self):
        return ", ".join(self.principal_parts) + ": " + self.english
    
    def first_and_second_conjugation(self):
        prog_stem:str = self.conjugations[Mood.Infinitive][:-2]
        prog_suffixes = (
            "ō", "mus",
            "s", "tis",
            "t", "nt",
        )
        self.conjugations[Mood.Indicative] = [""] * len(Number) * len(Person) * len(Tense)

        for pers in Person:
            for num in Number:
                for time in Time:
                    suffix = prog_suffixes[pers+num]
                    infix = ""

                    if time == Time.Past:
                        if pers == Person.First and num == Number.Singular:
                            infix = "ba"
                            suffix = "m"
                        else:
                            infix = "bā"

                    elif time == Time.Future:
                        if pers == Person.First and num == Number.Singular:
                            infix = "b"
                        elif pers == Person.Third and num == Number.Plural:
                            infix = "bu"
                        else:
                            infix = "bi"

                    conj = prog_stem + infix + suffix

                    # First conj
                    conj = self.replace_ending(conj, "āō", "ō")
                    conj = self.replace_ending(conj, "āt", "at")
                    conj = self.replace_ending(conj, "ānt", "ant")

                    # Second conj
                    conj = self.replace_ending(conj, "ēō", "eō")
                    conj = self.replace_ending(conj, "ēt", "et")
                    conj = self.replace_ending(conj, "ēnt", "ent")

                    self.conjugations[Mood.Indicative][Aspect.Progressive + time + pers + num] = conj

        self.conjugations[Mood.Imperative] = [prog_stem, prog_stem + "te"]

    def third_conjugation(self):
        raise NotImplementedError

    def fourth_conjugation(self):
        raise NotImplementedError
    
    def conjugate(self):
        self.conjugations[Mood.Infinitive] = self.principal_parts[1]

        conjugation_funcs = [
            self.first_and_second_conjugation,
            self.first_and_second_conjugation,
            self.third_conjugation,
            self.fourth_conjugation
        ]
        try:
            conjugation_funcs[self.conjugation-1]()

            mood = None
            total_parsing = None
            for parsing, conjugation in self.special_cases.items():
                for i, (parse_type, parse,) in enumerate(parsing):
                    if i == 0:
                        assert parse_type == Mood.__name__
                        mood = Mood[parse]
                    else:
                        if total_parsing == None: total_parsing = 0

                        potential_types = (Number, Person, Time, Aspect, Tense,)
                        potential_types = {pt.__name__ : pt for pt in potential_types}
                        total_parsing += potential_types[parse_type][parse].value
                
                if total_parsing is None:
                    self.conjugations[mood] = conjugation
                else:
                    self.conjugations[mood][total_parsing] = conjugation

        except NotImplementedError:
            logging.warning(f"Cannot yet conjugate {self.conjugation}-th conjugation verbs")
    
    def load(self):
        self.conjugation = self.determine_conjugation()
        self.conjugate()

    def determine_conjugation(self) -> int:
        assert len(self.principal_parts) in (3,4,) and len(self.principal_parts[1]) >= 3
        if self.principal_parts[1][-3:] == "āre":
            return 1
        elif self.principal_parts[1][-3:] == "ēre":
            return 2
        elif self.principal_parts[1][-3:] == "ere":
            return 3
        elif self.principal_parts[1][-3:] == "īre":
            return 4
        return -1


class Adverb(Vocab):
    pass


class Declinable(Vocab):
    def __init__(self, declension: int):
        super().__init__()

        self.declension = declension


class Noun(Declinable):
    @staticmethod
    def determine_declension(nom_sg: str, gen_sg: str) -> int:
        raise NotImplementedError()

    def __init__(self, nom_sg: str, gen_sg: str, gender: Gender, english: list[str]):
        super().__init__(Noun.determine_declension(nom_sg, gen_sg))

        self.nom_sg = nom_sg
        self.gen_sg = gen_sg
        self.gender = gender
        self.english = english
        

class Adjective(Declinable):
    @staticmethod
    def determine_declension() -> int:
        return 1
    
    def __init__(self, masc: str, fem: str, neut: str, english: list[str]):
        self.masc = masc
        self.fem = fem
        self.neut = neut
        self.english = english


class Pronoun(Vocab):
    pass

class Preoposition(Vocab):
    pass

class Conjunction(Vocab):
    pass

class Interjection(Vocab):
    pass

class Unknown(Vocab):
    pass