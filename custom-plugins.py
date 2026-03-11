import re

from detect_secrets.plugins.base import RegexBasedDetector


class MongoDBConnectionStringDetector(RegexBasedDetector):
    secret_type = "MongoDB Connection String"  # pragma: allowlist secret

    denylist = [
        re.compile(r"mongodb\+srv://[a-zA-Z0-9]+:\S+@.+"),
    ]


class ApplicationInsightsConnectionStringDetector(RegexBasedDetector):
    secret_type = "Application Insights Connection String"  # pragma: allowlist secret

    denylist = [
        re.compile(
            r"InstrumentationKey=[a-f0-9\-]{36};IngestionEndpoint=https://[a-zA-Z0-9\.-]+/;LiveEndpoint=https://[a-zA-Z0-9\.-]+/;ApplicationId=[a-f0-9\-]{36}"
        ),
    ]


class AzureStorageConnectionStringDetector(RegexBasedDetector):
    secret_type = "Azure Storage Connection String"  # pragma: allowlist secret

    denylist = [
        re.compile(
            r"DefaultEndpointsProtocol=https;AccountName=[a-zA-Z0-9]+;AccountKey=[a-zA-Z0-9\/\+\=]{88};EndpointSuffix=core\.windows\.net"
        ),
    ]
