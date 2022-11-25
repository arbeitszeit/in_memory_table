from mypyc.build import mypycify
from setuptools import setup

setup(
    ext_modules=mypycify(
        [
            "in_memory_relations/table.py",
            "in_memory_relations/column_index.py",
            "in_memory_relations/sorted_collection.py",
        ]
    ),
)
