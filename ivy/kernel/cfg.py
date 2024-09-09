import typing
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class Config:
    text_base: int
    nr_cpus: int
