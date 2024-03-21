def _priv_method() -> None:
    print('Hello from priv')


def pub_method() -> None:
    _priv_method()
