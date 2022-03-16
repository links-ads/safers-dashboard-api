import pytest
import factory
import os

from faker import Faker
from functools import partial
from itertools import combinations
from random import shuffle

from django.core.files.storage import get_storage_class
from django.core.files.uploadedfile import SimpleUploadedFile

fake = Faker()

##############
# useful fns #
##############


def shuffle_string(string):
    """
    Mixes up a string.
    Useful for generating invalid ids, etc.
    """
    string_list = list(string)
    shuffle(string_list)
    return "".join(string_list)


#############
# factories #
#############


def optional_declaration(declaration, chance=50, default=None):
    """
    Used in DjangoModelFactories.  Only sets a field value to
    "declaration" some of the time, otherwise sets it to "default".
    Useful for optional fields.
    """
    decider = factory.LazyFunction(
        partial(fake.boolean, chance_of_getting_true=chance)
    )
    return factory.Maybe(
        decider,
        yes_declaration=declaration,
        no_declaration=default,
    )


###########
# markers #
###########


def get_list_combinations(lst):
    """
    Returns all possible list combination of lst.
    >> get_list_combinations(["a", "b", "c"])
    >> [[], ["a"], ["b"], ["c"], ["a", "b"], ["a", "c"], ["b", "c"], ["a", "b", "c"]]
    useful w/ `@pytest.mark.parametrize`
    """
    n_items = len(lst) + 1
    lists = []
    for i in range(0, n_items):
        temp = [list(c) for c in combinations(lst, i)]
        if len(temp):
            lists.extend(temp)
    return lists


#####################
# fixtures  & mocks #
#####################


@pytest.fixture
def mock_storage(monkeypatch):
    """
    Mocks the backend storage system by not actually accessing media
    """

    clean_name = lambda name: os.path.splitext(os.path.basename(name))[0]

    def _mock_open(instance, name, mode="rb"):
        return SimpleUploadedFile(name=name, content=b"mock")

    def _mock_save(instance, name, content):
        setattr(instance, f"mock_{clean_name(name)}_exists", True)
        return str(name).replace("\\", "/")

    def _mock_delete(instance, name):
        setattr(instance, f"mock_{clean_name(name)}_exists", False)

    def _mock_exists(instance, name):
        return getattr(instance, f"mock_{clean_name(name)}_exists", False)

    # TODO: APPLY MOCK TO DefaultStorage AS WELL
    storage_class = get_storage_class()

    monkeypatch.setattr(storage_class, "_open", _mock_open)
    monkeypatch.setattr(storage_class, "_save", _mock_save)
    monkeypatch.setattr(storage_class, "delete", _mock_delete)
    monkeypatch.setattr(storage_class, "exists", _mock_exists)
