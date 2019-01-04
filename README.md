A rudimentary parser for StepMania `.sm` files
and some tools for working with them.

Contents of the repository:
- [`pysm/__init__.py`](pysm/__init__.py)

    Rudimentary parser for `.sm` files

- [`check-couples.py`](check-couples.py)

    Checks couples charts for potentially nasty patterns.
    Tries to find places where one player might still be standing on an
    arrow when the other player steps on it.

- [`generator.py`](generator.py)

    Proof-of-concept step pattern generator

- [`notes-to-short-rolls.py`](notes-to-short-rolls.py)

    Converts all normal notes in a file to short roll notes.
