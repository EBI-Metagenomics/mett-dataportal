import operator
import shlex
from functools import reduce

import django_filters
from django.db.models import (
    Q,
    CharField,
    TextField,
    QuerySet,
    F,
    Subquery,
    OuterRef,
    Func,
)
from django.utils.safestring import mark_safe
