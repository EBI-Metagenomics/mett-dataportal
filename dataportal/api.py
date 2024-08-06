import operator
from enum import Enum
from functools import reduce
from typing import Optional, List

from django.db.models import Q
from django.db.models.functions import Lower
from django.shortcuts import get_object_or_404
from django.urls import reverse
from ninja import ModelSchema, NinjaAPI, Field
from ninja.pagination import RouterPaginated
from pydantic import AnyHttpUrl



api = NinjaAPI(
    title="DataPortal Data Portal API",
    description="The API to browse [DataPortal](https://www.dataportal.eu) samples and metadata, "
    "and navigate to datasets stored in public archives. \n\n #### Useful links: \n"
    "- [Documentation](https://ebi-metagenomics.github.io/dataportal-database/)\n"
    "- [DataPortal Data Portal home](/)\n"
    "- [DataPortal Project Website](https://www.dataportal.eu)\n"
    "- [Helpdesk](https://www.ebi.ac.uk/contact)\n"
    "- [TSV Export endpoints](/export/docs)",
    urls_namespace="api",
    default_router=RouterPaginated(),
    csrf=True,
)
