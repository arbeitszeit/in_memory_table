from mypyc.build import mypycify
from setuptools import setup

setup(
    ext_modules=mypycify(
        [
            "in_memory_table/table.py",
            "in_memory_table/column_index.py",
            "in_memory_table/sorted_collection.py",
        ]
    ),
)
