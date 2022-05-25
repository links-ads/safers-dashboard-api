import pytest
from copy import deepcopy

from django.db import transaction
from django.db.utils import IntegrityError

from safers.core.tests.factories import *

from .factories import *


@pytest.mark.django_db
class TestDataType:
    def test_constraints(self):

        data_type_1 = DataTypeFactory(
            datatype_id="test", subgroup="test", group="test"
        )
        data_type_2 = DataTypeFactory(
            datatype_id=None, subgroup="test", group=None
        )
        data_type_3 = DataTypeFactory(
            datatype_id=None, subgroup=None, group="test"
        )

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                # all null fields
                data_type_4 = DataTypeFactory(
                    datatype_id=None, subgroup=None, group=None
                )

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                # duplicate fields
                data_type_5 = DataTypeFactory(
                    datatype_id="test", subgroup="test", group="test"
                )

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                # subgroup AND group
                data_type_6 = DataTypeFactory(
                    datatype_id=None, subgroup="test2", group="test2"
                )

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                # datatype w/out subgroup AND group
                data_type_7 = DataTypeFactory(
                    datatype_id="test", subgroup="test3", group=None
                )

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                # duplicate subgroup
                data_type_8 = DataTypeFactory(
                    datatype_id=None, subgroup="test", group=None
                )

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                # duplicate group
                data_type_9 = DataTypeFactory(
                    datatype_id=None, subgroup=None, group="test"
                )

        # new subgrup
        data_type_10 = DataTypeFactory(
            datatype_id="test2", subgroup="test2", group="test"
        )

        # new group
        data_type_11 = DataTypeFactory(
            datatype_id="test3", subgroup="test", group="test2"
        )

        with transaction.atomic():
            with pytest.raises(IntegrityError):
                # duplicate datatype_id
                data_type_12 = DataTypeFactory(
                    datatype_id="test", subgroup="test3", group="test3"
                )

        # all new fields
        data_type_13 = DataTypeFactory(
            datatype_id="test4", subgroup="test4", group="test4"
        )

    def test_filters(self):

        data_type_1 = DataTypeFactory(
            datatype_id="test", subgroup="test", group="test"
        )
        data_type_2 = DataTypeFactory(
            datatype_id=None, subgroup="test", group=None
        )
        data_type_3 = DataTypeFactory(
            datatype_id=None, subgroup=None, group="test"
        )

        assert DataType.objects.get_empty_subgroup("test") == data_type_2
        assert DataType.objects.get_empty_group("test") == data_type_3
        assert DataType.objects.get_empty_subgroup("invalid") is None
        assert DataType.objects.get_empty_group("invalid") is None
