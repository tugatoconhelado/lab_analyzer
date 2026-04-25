from dataclasses import dataclass

@dataclass
class Parent:
    a: int = 10
    b: int = 20

@dataclass
class Child(Parent):
    a: int = 100  # Overriding the default value
    c: int = 30   # Adding a new field

# Usage
obj = Child()
print(obj) 