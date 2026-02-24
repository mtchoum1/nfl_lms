#!/usr/bin/env python3
# Test the User class

import sys
from pathlib import Path

# Ensure project root is on path so "user" can be imported from any cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from user import User

# test user_init, get_id, get_name
def test_user_init():
    user = User(1, "John Doe")
    assert user.get_id() == 1
    assert user.get_name() == "John Doe"

#test user repr
def test_user_repr():
    user = User(42, "Jane")
    assert repr(user) == "User(id=42, name=Jane)"

# test user str
def test_user_str():
    user = User(42, "Jane")
    assert str(user) == "User(id=42, name=Jane)"

# test user equality with same id and name
def test_user_equality_same_id_and_name():
    a = User(1, "Alice")
    b = User(1, "Alice")
    assert a == b  
    assert (a != b) is False

# test user equality with different id and name
def test_user_equality_different_id_and_name():
    a = User(1, "Alice")
    b = User(2, "Bob")
    assert a != b
    assert (a == b) is False

# test user equality with different id but same name
def test_user_equality_different_id_but_same_name():
    a = User(1, "Alice")
    b = User(2, "Alice")
    assert a != b
    assert (a == b) is False

# test user equality with different name but same id
def test_user_equality_different_name_but_same_id():
    a = User(1, "Alice")
    b = User(1, "Bob")
    assert a != b
    assert (a == b) is False

# test user hash with same id and name
def test_user_hash_same_id_and_name():
    a = User(1, "Alice")
    b = User(1, "Alice")
    assert hash(a) == hash(b)

# test user hash with different id and name
def test_user_hash_different_id_and_name():
    a = User(1, "Alice")
    b = User(2, "Bob")
    assert hash(a) != hash(b)

# test user hash with different id but same name
def test_user_hash_different_id_but_same_name():
    a = User(1, "Alice")
    b = User(2, "Alice")
    assert hash(a) != hash(b)

# test user hash with different name but same id
def test_user_hash_different_name_but_same_id():
    a = User(1, "Alice")
    b = User(1, "Bob")
    assert hash(a) != hash(b)