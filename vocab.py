from typing import TypeAlias
from enum import Enum


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
        pass


PrincipalParts: TypeAlias = tuple[str,str,str,str]

class Verb(Vocab):
    @staticmethod
    def determine_conjugation(principal_parts: PrincipalParts) -> int:
        raise NotImplementedError()

    def __init__(self, principal_parts: PrincipalParts, english: list[str]):
        super().__init__()

        self.principal_parts = principal_parts
        self.english = english
        self.conjugation = 0


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