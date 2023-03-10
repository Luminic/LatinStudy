import logging
from typing import TypeAlias
from enum import Enum, IntEnum


class PCol(Enum):
    CNONE = ''

    CEND      = '\33[0m'
    CBOLD     = '\33[1m'
    CITALIC   = '\33[3m'
    CURL      = '\33[4m'
    CBLINK    = '\33[5m'
    CBLINK2   = '\33[6m'
    CSELECTED = '\33[7m'

    CBLACK  = '\33[30m'
    CRED    = '\33[31m'
    CGREEN  = '\33[32m'
    CYELLOW = '\33[33m'
    CBLUE   = '\33[34m'
    CVIOLET = '\33[35m'
    CBEIGE  = '\33[36m'
    CWHITE  = '\33[37m'
    CGREY   = '\33[90m'

    CBLACKBG  = '\33[40m'
    CREDBG    = '\33[41m'
    CGREENBG  = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG   = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG  = '\33[46m'
    CWHITEBG  = '\33[47m'


a_macron = 'ā'
e_macron = 'ē'
i_macron = 'ī'
o_macron = 'ō'
u_macron = 'ū'
vowels = "aeiou"
long_vowels = a_macron + e_macron + i_macron + o_macron + u_macron

def make_short(org_str:str):
    new_str = org_str
    for i in range(len(vowels)):
        new_str = new_str.replace(long_vowels[i], vowels[i])
    return new_str

def make_long(org_str:str):
    new_str = org_str
    for i in range(len(vowels)):
        new_str = new_str.replace(vowels[i], long_vowels[i])
    return new_str


class Gender(IntEnum):
    Masc = 0
    Fem = 1
    Neut = 2


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


class DescBlockType(Enum):
    Text = PCol.CNONE.value
    VocabType = PCol.CVIOLET.value
    Latin = PCol.CRED.value
    Definition = PCol.CBLUE.value
    Gender = PCol.CYELLOW.value
    DebugInfo = PCol.CGREY.value



class Vocab:
    def __init__(self):
        self.description = ""
        self.loaded = False
    
    def __hash__(self):
        return hash(self.description)
    
    def load(self):
        self.loaded = True
    
    def get_extended_description(self):
        return ""

    def get_parsed_description(self) -> list[tuple[str, DescBlockType]]:
        parsed_desc = []

        for desc in self.description.split(PCol.CEND.value):
            desc_block_type = DescBlockType.Text
            cutpoint = 0
            for dbt in DescBlockType:
                if dbt == DescBlockType.Text:
                    continue
                if (cutpoint := desc.find(dbt.value)) != -1:
                    desc = desc.replace(dbt.value, "")
                    desc_block_type = dbt
                    break

            if cutpoint != 0:
                parsed_desc.append((desc[:cutpoint], DescBlockType.Text,))
                desc = desc[cutpoint:]
        
            parsed_desc.append((desc, desc_block_type,))
        
        return parsed_desc

    def get_clean_description(self):
        clean_desc = ""
        for desc, desc_type in self.get_parsed_description():
            if desc_type != DescBlockType.DebugInfo:
                clean_desc += desc
        return clean_desc


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
    def _replace_ending(somestr:str, old:str, new:str):
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

    def get_extended_description(self):
        all_conjugations = []
        all_conjugations += self.conjugations[Mood.Indicative]
        all_conjugations += self.conjugations[Mood.Imperative]
        all_conjugations.append(self.conjugations[Mood.Infinitive])
        return ", ".join(all_conjugations)
    
    def _perfect_active_conjugation(self):
        perf_stem:str = self.principal_parts[2][:-1]
        if len(self.principal_parts[2]) == 0 or self.principal_parts[2][-1] != 'ī':
            logging.warning(f"Cannot conjugate {self.description} in the perfect active system")
            return

        perf_suffixes = (
            "ī",    "imus",
            "istī", "istis",
            "it",   "ērunt",
        )

        pluperf_suffixes = (
            "eram", "erāmus",
            "erās", "erātis",
            "erat", "erant",
        )

        futperf_suffixes = (
            "erō",  "erimus",
            "eris", "eritis",
            "erit", "erint",
        )

        for pers in Person:
            for num in Number:
                for time in Time:
                    suffix = None
                    if time == Time.Present:
                        suffix = perf_suffixes[pers+num]
                    elif time == Time.Past:
                        suffix = pluperf_suffixes[pers+num]
                    elif time == Time.Future:
                        suffix = futperf_suffixes[pers+num]
                    
                    conj = perf_stem + suffix
                    self.conjugations[Mood.Indicative][Aspect.Perfective + time + pers + num] = conj
    
    def _first_and_second_conjugation(self):
        prog_stem:str = self.conjugations[Mood.Infinitive][:-2]

        self.conjugations[Mood.Indicative] = [""] * len(Number) * len(Person) * len(Tense)
        prog_suffixes = (
            "ō", "mus",
            "s", "tis",
            "t", "nt",
        )
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
                    conj = self._replace_ending(conj, "āō", "ō")
                    conj = self._replace_ending(conj, "āt", "at")
                    conj = self._replace_ending(conj, "ānt", "ant")

                    # Second conj
                    conj = self._replace_ending(conj, "ēō", "eō")
                    conj = self._replace_ending(conj, "ēt", "et")
                    conj = self._replace_ending(conj, "ēnt", "ent")

                    self.conjugations[Mood.Indicative][Aspect.Progressive + time + pers + num] = conj
        
        self._perfect_active_conjugation()

        self.conjugations[Mood.Imperative] = [prog_stem, prog_stem + "te"]

    def _third_and_fourth_conjugation(self):
        prog_stem:str = self.conjugations[Mood.Infinitive][:-2]

        self.conjugations[Mood.Indicative] = [""] * len(Number) * len(Person) * len(Tense)

        pres_suffixes = (
            "ō", "mus",
            "s", "tis",
            "t", "unt",
        )

        imperf_suffixes = (
            "ēbam", "ēbāmus",
            "ēbās", "ēbātis",
            "ēbat", "ēbant",
        )

        fut_suffixes = (
            "am", "ēmus",
            "ēs", "ētis",
            "et", "ent",
        )

        for pers in Person:
            for num in Number:
                for time in Time:
                    suffix = None

                    if time == Time.Present:
                        suffix = pres_suffixes[pers+num]

                    elif time == Time.Past:
                        suffix = imperf_suffixes[pers+num]

                    elif time == Time.Future:
                        suffix = fut_suffixes[pers+num]
                    
                    modified_stem = ""

                    if self.conjugation == 3:
                        modified_stem = prog_stem[:-1]
                        
                        if self.principal_parts[0].endswith("iō"):
                            modified_stem += 'i'

                        elif time == Time.Present and not (
                                (pers == Person.First and num == Number.Singular)
                                or (pers == Person.Third and num == Number.Plural)):
                            modified_stem += 'i'
                        
                    elif self.conjugation == 4:
                        assert prog_stem[-1] == 'ī'
                        if suffix[0] in (vowels + long_vowels) or suffix[-1] == 't':
                            modified_stem = self._replace_ending(prog_stem, 'ī', 'i')
                        else:
                            modified_stem = prog_stem

                    conj = modified_stem + suffix
                    self.conjugations[Mood.Indicative][Aspect.Progressive + time + pers + num] = conj

        self._perfect_active_conjugation()
        
        self.conjugations[Mood.Imperative] = [prog_stem, prog_stem + "te"]
        self._replace_ending(self.conjugations[Mood.Imperative][Number.Plural], "ete", "ite")
    
    def conjugate(self):
        self.conjugations[Mood.Infinitive] = self.principal_parts[1]

        conjugation_funcs = [
            self._first_and_second_conjugation,
            self._first_and_second_conjugation,
            self._third_and_fourth_conjugation,
            self._third_and_fourth_conjugation
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
            logging.warning(f"Cannot yet conjugate {self.conjugation}-th conjugation verbs: {self.description}")
    
    def load(self):
        super().load()

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
        

class Case(IntEnum):
    Nominative = 0 * len(Number)
    Genitive   = 1 * len(Number)
    Dative     = 2 * len(Number)
    Accusative = 3 * len(Number)
    Ablative   = 4 * len(Number)
    Vocative   = 5 * len(Number)


class Declinable(Vocab):
    def __init__(self):
        super().__init__()
        self.declension = 0

    def decline(self, nom_sg:str, base:str, gender:Gender) -> list[str]:
        endings = None

        cases = [""] * len(Case) * len(Number)

        if self.declension == 1:
            endings = [
                "a",  "ae",
                "ae", "ārum",
                "ae", "īs",
                "am", "ās",
                "ā",  "īs",
                "",   "",
            ]

        elif self.declension == 2:
            endings = [
                "",   "ī",
                "ī",  "ōrum",
                "ō",  "īs",
                "um", "ōs",
                "ō",  "īs",
                "",   "",
            ]
            if gender == Gender.Neut:
                endings[Case.Nominative + Number.Plural] = "a"
                endings[Case.Accusative + Number.Plural] = "a"

        elif self.declension == 3:
            endings = [
                "",   "ēs",
                "is", "um",
                "ī",  "ibus",
                "em", "ēs",
                "e",  "ibus",
                "",   "",
            ]
            if gender == Gender.Neut:
                endings[Case.Nominative + Number.Plural] = "a"
                endings[Case.Accusative + Number.Plural] = "a"
                endings[Case.Accusative + Number.Singular] = None

        else:
            logging.warning(f"Cannot yet decline {self.declension}-th declension words: {self.description}")
            return cases
        
        for case in Case:
            for number in Number:
                if case == Case.Nominative and number == Number.Singular:
                    cases[case + number] = nom_sg
                
                elif gender == Gender.Neut and self.declension == 3 and case == Case.Accusative:
                    cases[case + number] = cases[Case.Nominative + number]
                
                elif case == Case.Vocative:
                    if number == Number.Singular and endings[Case.Nominative + number].endswith("us"):
                        cases[case + number] = base + "e"
                    else:
                        cases[case + number] = cases[Case.Nominative + number]

                elif endings[case + number] != "":
                    cases[case + number] = base + endings[case + number]
        
        return cases


class Noun(Declinable):
    def __init__(self, nom_sg: str, gen_sg: str, gender: Gender, english: list[str]):
        super().__init__()

        self.nom_sg = nom_sg
        self.gen_sg = gen_sg
        self.gender = gender
        self.english = english

        self.cases: list[str] = [""] * len(Case) * len(Number)
        self.base: str|None = None
        self.plural_only: bool = False
    
    def get_extended_description(self):
        return ", ".join(self.cases)
    
    def load(self):
        super().load()

        if self.nom_sg.endswith("a") and self.gen_sg.endswith("ae"):
            self.declension = 1
            self.base = self.gen_sg[:-2]

        elif self.nom_sg.endswith("ae") and self.gen_sg.endswith("ārum"):
            self.declension = 1
            self.plural_only = True
            self.base = self.gen_sg[:-4]

        elif (self.nom_sg.endswith("er") or self.nom_sg.endswith("us") or self.nom_sg.endswith("um")) \
                and self.gen_sg.endswith("ī"):
            self.declension = 2
            self.base = self.gen_sg[:-1]

        elif (self.nom_sg.endswith("ī") or self.nom_sg.endswith("a")) \
                and self.gen_sg.endswith("ōrum"):
            self.declension = 2
            self.plural_only = True
            self.base = self.gen_sg[:-4]

        elif self.gen_sg.endswith("is"):
            self.declension = 3
            self.base = self.gen_sg[:-2]

        self.cases = self.decline(self.nom_sg, self.base, self.gender)


class Adjective(Declinable):
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