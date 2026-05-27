from lib.cairn.stubs import stub_method

_STUB_MESSAGE = "RedisCacheBackend requires `poetry install --with redis`"


class RedisCacheBackend:
    get = stub_method(_STUB_MESSAGE)
    set = stub_method(_STUB_MESSAGE)
    delete = stub_method(_STUB_MESSAGE)
    exists = stub_method(_STUB_MESSAGE)
