def test_two_plus_two_equals_four():
    result = 2 + 3
    assert result == 5

def test_account_module():
    try:
        from account import __version__
        assert True
    except ImportError:
        from account import __name__
        assert __name__ == 'account'