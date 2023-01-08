from proxyrr import proxy_error

class TestProxyError():

    def test_create_base_error(self):
        base_error = proxy_error.ProxyError(500, 'BaseError', 'Test message')
        assert 500 == base_error.code
        assert 'BaseError' == base_error.type
        assert 'Test message' == base_error.message