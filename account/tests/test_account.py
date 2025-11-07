def test_two_plus_two_equals_four():
    result = 2 + 2
    assert result == 4

def test_account_module():
    try:
        from account import __version__
        assert __version__ is not None
    except ImportError:
        from account import __name__
        assert __name__ == 'account'