from dataclasses import dataclass
import pytest

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from safers.core.managers import TransientModelQuerySet, CachedTransientModelManager


@dataclass
class TestModel:
    __test__ = False  # prevent pytest auto-discovery

    id: int


class TestModelQuerySet(TransientModelQuerySet):
    __test__ = False  # prevent pytest auto-discovery

    pass


class TestModelManager(CachedTransientModelManager):
    __test__ = False  # prevent pytest auto-discovery

    queryset_class = TestModelQuerySet

    model_class = TestModel

    cache_key = "test"

    def get_transient_queryset_data(self):
        test_models_data = [{"id": 1}, {"id": 2}, {"id": 3}]
        return test_models_data


class TestTransientModelQuerySet:
    def test_get(self):

        test_models = map(TestModel, [1, 2, 3])
        test_queryset = TestModelQuerySet(test_models)

        test_model = test_queryset.get(id=1)
        assert test_model.id == 1

    def test_get_missing(self):

        test_models = map(TestModel, [1, 2, 3])
        test_queryset = TestModelQuerySet(test_models)

        with pytest.raises(ObjectDoesNotExist):
            test_queryset.get(id=4)

    def test_get_multiple(self):

        test_models = map(TestModel, [1, 2, 2])
        test_queryset = TestModelQuerySet(test_models)

        with pytest.raises(MultipleObjectsReturned):
            test_queryset.get(id=2)

    def test_first(self):
        test_models = map(TestModel, [1, 2, 3])
        test_queryset = TestModelQuerySet(test_models)

        test_model = test_queryset.first()
        assert test_model.id == 1

    def test_first_missing(self):
        test_queryset = TestModelQuerySet([])

        test_model = test_queryset.first()
        assert test_model is None

    def test_last(self):
        test_models = map(TestModel, [1, 2, 3])
        test_queryset = TestModelQuerySet(test_models)

        test_model = test_queryset.last()
        assert test_model.id == 3

    def test_last_missing(self):
        test_queryset = TestModelQuerySet([])

        test_model = test_queryset.last()
        assert test_model is None

    def test_filter(self):
        test_models = map(TestModel, [1, 2, 3])
        test_queryset = TestModelQuerySet(test_models)

        filtered_queryset = test_queryset.filter(id=1)
        assert len(filtered_queryset) == 1
        assert filtered_queryset.first().id == 1

    def test_exclude(self):
        test_models = map(TestModel, [1, 2, 3])
        test_queryset = TestModelQuerySet(test_models)

        excluded_queryset = test_queryset.exclude(id=1)
        assert len(excluded_queryset) == 2
        assert excluded_queryset.first().id != 1
        assert excluded_queryset.last() != 1


@pytest.mark.django_db
class TestCachedTransientModelManager:
    def test_get_queryset(self):
        test_manager = TestModelManager.from_queryset(TestModelQuerySet)(
            model_class=TestModel
        )
        test_queryset = test_manager.get_queryset()
        assert isinstance(test_queryset, TestModelQuerySet)

    def test_cache_queryset_(self):
        test_manager = TestModelManager.from_queryset(TestModelQuerySet)(
            model_class=TestModel
        )
        assert test_manager.cache.get(test_manager.cache_key) is None
        test_manager.get_queryset()
        assert test_manager.cache.get(test_manager.cache_key) is not None