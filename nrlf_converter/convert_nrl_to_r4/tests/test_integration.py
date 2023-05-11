import json
from datetime import datetime as dt
from http import HTTPStatus
from pathlib import Path
from types import FunctionType
from uuid import uuid4

import pytest

from nrlf_converter import nrl_to_r4

PATH_TO_HERE = Path(__file__).parent
PATH_TO_DATA = PATH_TO_HERE.parent.parent / "nrl" / "tests" / "data"
PATHS_TO_TEST_DATA = list(PATH_TO_DATA.iterdir())
SANDBOX_URL = "https://sandbox.api.service.nhs.uk/record-locator/producer/FHIR/R4/DocumentReference"

NHS_NUMBER = "3964056618"
ODS_CODE = "Y05868"
DOC_TYPE = "736253002"
SUPERSEDE_ERROR_MSG = "At least one document pointer cannot be deleted because it belongs to another organisation"


def _hack_permissions(document_reference: dict, uuid: str):
    old_ods_code = document_reference["custodian"]["identifier"]["value"]
    document_reference["custodian"]["identifier"]["value"] = ODS_CODE
    document_reference["id"] = (
        document_reference["id"].replace(old_ods_code, ODS_CODE) + uuid
    )
    document_reference["type"]["coding"][0]["code"] = DOC_TYPE
    return document_reference


def _create_headers(uuid: str):
    return {
        "Accept": "application/fhir+json;version=1",
        "NHSD-End-User-Organisation-ODS": ODS_CODE,
        "X-Request-ID": uuid,
        "X-Correlation-Id": uuid,
        "Content-Type": "application/fhir+json;version=1",
    }


def _test_end_to_end(path_to_data: Path, requests_post: FunctionType):
    uuid = f"nhsd--nrl_to_r4--{dt.now().isoformat()}--{uuid4()}"

    with open(path_to_data) as f:
        document_reference = nrl_to_r4(
            document_pointer=json.load(f), nhs_number=NHS_NUMBER
        )

    document_reference = _hack_permissions(
        document_reference=document_reference, uuid=uuid
    )
    headers = _create_headers(uuid=uuid)

    print("Making POST request with headers", headers)  # noqa: T201
    print("and body")  # noqa: T201
    print(document_reference)  # noqa: T201
    return requests_post(data=document_reference, headers=headers)


@pytest.mark.parametrize("path_to_data", PATHS_TO_TEST_DATA)
def test_that_nrl_test_data_conforms_to_contract(path_to_data):
    import json

    def requests_post(data: dict, headers: dict):
        json.dumps(data)

    _test_end_to_end(path_to_data=path_to_data, requests_post=requests_post)


@pytest.mark.integration
@pytest.mark.parametrize("path_to_data", PATHS_TO_TEST_DATA)
def test_validate_against_nrlf(path_to_data):
    import requests

    def requests_post(data: dict, headers: dict):
        r = requests.post(url=SANDBOX_URL, json=data, headers=headers)
        return HTTPStatus(r.status_code), r.json()

    status_code, message = _test_end_to_end(
        path_to_data=path_to_data, requests_post=requests_post
    )

    if status_code is HTTPStatus.BAD_REQUEST:
        assert message["issue"][0]["diagnostics"] == SUPERSEDE_ERROR_MSG, message
    else:
        assert status_code is HTTPStatus.CREATED, message
