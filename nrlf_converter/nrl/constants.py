import re

NHS_NUMBER_SYSTEM_URL = "https://fhir.nhs.uk/Id/nhs-number"
UPDATE_DATE_FORMAT = r"%a, %d %b %Y %H:%M:%S GMT"
REPLACES = "replaces"
DEFAULT_SYSTEM = "http://snomed.info/sct"
ODS_SYSTEM = "https://fhir.nhs.uk/Id/ods-organization-code"
CUSTODIAN_ODS_REGEX = re.compile(
    "^https://directory.spineservices.nhs.uk/STU3/Organization/(?P<ods_code>\w+)$"
)
RELATES_TO_REPLACES_REGEX = re.compile(
    "^https://psis-sync.national.ncrs.nhs.uk/DocumentReference/(?P<logical_id>.*)$"
)
