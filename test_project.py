from project import is_int_between, is_valid_search


def test_is_int_between():
    assert is_int_between(1, 10, "3") == True
    assert is_int_between(2, 5, "10") == False


def test_is_valid_search():
    assert is_valid_search(" ") == False
    assert is_valid_search("             ") == False
    assert is_valid_search("a") == False
    assert is_valid_search("abc") == True
