import re

NHS_NUMBER_SYSTEM_URL = "https://fhir.nhs.uk/Id/nhs-number"
ASID_SYSTEM_URL = "https://fhir.nhs.uk/Id/nhsSpineASID"
UPDATE_DATE_FORMAT = r"%a, %d %b %Y %H:%M:%S GMT"
REPLACES = "replaces"
DEFAULT_SYSTEM = "http://snomed.info/sct"
ODS_SYSTEM = "https://fhir.nhs.uk/Id/ods-organization-code"
CUSTODIAN_ODS_REGEX = re.compile(
    "^https://directory.spineservices.nhs.uk/STU3/Organization/(?P<ods_code>\w+)$"
)
RELATES_TO_REPLACES_REFERENCE_REGEXES = [
    re.compile(
        "^https://psis-sync.national.ncrs.nhs.uk/DocumentReference/(?P<logical_id>.*)$"
    ),
    re.compile(
        "^https://clinicals.spineservices.nhs.uk/DocumentReference/(?P<logical_id>.*)$"
    ),
]

RELATES_TO_REPLACES_IDENTIFIER_REGEXES = [
    re.compile("^urn:uuid:(?P<logical_id>.*)$"),
]
