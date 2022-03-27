from faker import Faker

fake = Faker()


def generate_password(**kwargs):
    """
    generates a password
    """
    password_kwargs = {
        "length": 20,
        "special_chars": True,
        "digits": True,
        "upper_case": True,
        "lower_case": True,
    }
    password_kwargs.update(kwargs)
    assert password_kwargs["length"
                          ] >= 4  # faker will break if the pwd is _too_ short
    return fake.password(**password_kwargs)