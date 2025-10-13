"""
CRZ64I AST and IR Dataclasses

Defines dataclasses for representing the Abstract Syntax Tree (AST) and Intermediate Representation (IR) of CRZ64I code.
"""

import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple, Union, Dict, Any


def to_json_dict(obj):
    d = asdict(obj)
    def remove_meta(o):
        if isinstance(o, dict):
            return {k: remove_meta(v) for k, v in o.items() if k != 'meta'}
        elif isinstance(o, list):
            return [remove_meta(item) for item in o]
        else:
            return o
    return remove_meta(d)


@dataclass
class Attribute:
    """Represents an attribute like #[fusion] or #[power="low"]."""

    name: str
    value: Optional[str] = None
    meta: Optional[Dict[str, int]] = None

    def to_json(self) -> dict:
        return to_json_dict(self)


@dataclass
class Instr:
    """Represents an instruction with mnemonic, operands, attributes, and raw text."""

    mnemonic: str
    operands: List[str]
    attrs: List[Attribute]
    raw: str
    meta: Optional[Dict[str, int]] = None

    @property
    def op(self):
        return self.mnemonic

    def to_json(self) -> dict:
        return to_json_dict(self)


@dataclass
class Label:
    """Represents a label like _loop:."""

    name: str
    meta: Optional[Dict[str, int]] = None

    def to_json(self) -> dict:
        return to_json_dict(self)


@dataclass
class LocalDecl:
    """Represents a local declaration like let x: i32 = 5;."""

    name: str
    type_: Optional[str]
    expr: str
    meta: Optional[Dict[str, int]] = None

    def to_json(self) -> dict:
        return to_json_dict(self)


@dataclass
class Assign:
    """Represents an assignment like x = y + 1;."""

    target: str
    expr: str
    meta: Optional[Dict[str, int]] = None

    def to_json(self) -> dict:
        return to_json_dict(self)


@dataclass
class Return:
    """Represents a return statement like return x;."""

    expr: Optional[str]
    meta: Optional[Dict[str, int]] = None

    def to_json(self) -> dict:
        return to_json_dict(self)


@dataclass
class If:
    """Represents an if statement."""

    condition: str
    then_block: List['Statement']
    else_block: Optional[List['Statement']]
    attrs: List[Attribute] = None
    meta: Optional[Dict[str, int]] = None

    def __post_init__(self):
        if self.attrs is None:
            self.attrs = []

    def to_json(self) -> dict:
        return to_json_dict(self)


@dataclass
class Loop:
    """Represents a for loop."""

    var: str
    start: str
    end: str
    body: List['Statement']
    attrs: List[Attribute] = None
    meta: Optional[Dict[str, int]] = None

    def __post_init__(self):
        if self.attrs is None:
            self.attrs = []

    def to_json(self) -> dict:
        return to_json_dict(self)


# Define Statement as Union for body in Function
Statement = Union[Instr, LocalDecl, Assign, Return, Label, If, Loop]


@dataclass
class Function:
    """Represents a function declaration."""

    name: str
    params: List[Tuple[str, Optional[str]]]  # (name, type)
    return_type: Optional[str]
    body: List[Statement]
    attrs: List[Attribute] = None
    meta: Optional[Dict[str, int]] = None

    def __post_init__(self):
        if self.attrs is None:
            self.attrs = []

    def to_json(self) -> dict:
        return to_json_dict(self)


@dataclass
class Program:
    """Represents the entire program."""

    declarations: List[Union[Function, Instr, Label]]
    meta: Optional[Dict[str, int]] = None

    def to_json(self) -> dict:
        functions = [d for d in self.declarations if isinstance(d, Function)]
        attrs = []
        for d in self.declarations:
            if hasattr(d, 'attrs'):
                attrs.extend(d.attrs)
        return {"functions": [f.to_json() for f in functions], "attrs": [a.to_json() for a in attrs]}
