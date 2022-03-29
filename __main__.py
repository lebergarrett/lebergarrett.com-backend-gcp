import time
import os
import pulumi
import pulumi_gcp as gcp

site_domain = "lebergarrett.com"
site_name = "lebergarrett"


website_bucket = gcp.storage.Bucket(site_name, 
    cors=[gcp.storage.BucketCorArgs(
        max_age_seconds=3600,
        methods=[
            "GET",
        ],
        origins=[f"https://{site_domain}", f"https://www.{site_domain}"],
        response_headers=["*"],
    )],
    force_destroy=True,
    location="US",
    uniform_bucket_level_access=False,
    website=gcp.storage.BucketWebsiteArgs(
        main_page_suffix="index.html",
    ))

bucket_reader = gcp.storage.DefaultObjectAccessControl(site_name,
    bucket=website_bucket.name,
    role="READER",
    entity="allUsers",
)

website_backend = gcp.compute.BackendBucket(site_name,
    description="Backend for static website",
    bucket_name=website_bucket.name
)

website_ssl_certificate = gcp.compute.ManagedSslCertificate(site_name,
    managed=gcp.compute.ManagedSslCertificateManagedArgs(
        domains=[f"{site_domain}.", f"www.{site_domain}."]
    )
)

website_url_map = gcp.compute.URLMap(site_name,
    description="URLmap for static website",
    default_service=website_backend.id,
    host_rules=[
        gcp.compute.URLMapHostRuleArgs(
            hosts=[site_domain],
            path_matcher="all-paths",
        )
    ],
    path_matchers=[
        gcp.compute.URLMapPathMatcherArgs(
            name="all-paths",
            default_service=website_backend.id,
            path_rules=[
                gcp.compute.URLMapPathMatcherPathRuleArgs(
                    paths=["/*"],
                    service=website_backend.id
                )
            ]
        )
    ]
)

http_to_https_url_map = gcp.compute.URLMap(f"{site_name}-http-to-https",
    description="HTTP to HTTPS redirect for static website",
    default_url_redirect=gcp.compute.URLMapDefaultUrlRedirectArgs(
        strip_query=False,
        https_redirect=True,
    )
)

website_target_https_proxy = gcp.compute.TargetHttpsProxy(site_name,
    url_map=website_url_map.id,
    ssl_certificates=[website_ssl_certificate.id]
)

http_to_https_proxy = gcp.compute.TargetHttpProxy(f"{site_name}-http-to-https",
    url_map=http_to_https_url_map.id,
)

website_global_address = gcp.compute.GlobalAddress(site_name)

website_global_forwarding_rule = gcp.compute.GlobalForwardingRule(site_name,
    ip_protocol="TCP",
    load_balancing_scheme="EXTERNAL",
    port_range="443",
    target=website_target_https_proxy.self_link,
    ip_address=website_global_address.id,
)

http_to_https_forwarding_rule = gcp.compute.GlobalForwardingRule(f"{site_name}-http-to-https",
    ip_protocol="TCP",
    load_balancing_scheme="EXTERNAL",
    port_range="80",
    target=http_to_https_proxy.self_link,
    ip_address=website_global_address.id,
)

website_dns_zone = gcp.dns.ManagedZone(site_name,
    description=f"{site_domain} DNS zone",
    dns_name=f"{site_domain}.",
)

website_dns_record = gcp.dns.RecordSet(site_name,
    name=website_dns_zone.dns_name,
    type="A",
    ttl=300,
    managed_zone=website_dns_zone.name,
    rrdatas=[website_global_address.address],
)

website_cname = gcp.dns.RecordSet(f"{site_name}-cname",
    name=website_dns_zone.dns_name.apply(lambda dns_name: f"www.{dns_name}"),
    managed_zone=website_dns_zone.name,
    type="CNAME",
    ttl=300,
    rrdatas=[f"{site_domain}."]
)

# ----- Visitors Application -----

# File path to where the Cloud Function's source code is located.
PATH_TO_SOURCE_CODE = "./function"

# We will store the source code to the Cloud Function in a Google Cloud Storage bucket.
function_bucket = gcp.storage.Bucket(f"{site_name}-cloudfunction",
    location="US",
)

# The Cloud Function source code itself needs to be zipped up into an
# archive, which we create using the pulumi.AssetArchive primitive.
assets = {}
for file in os.listdir(PATH_TO_SOURCE_CODE):
    location = os.path.join(PATH_TO_SOURCE_CODE, file)
    asset = pulumi.FileAsset(path=location)
    assets[file] = asset

archive = pulumi.AssetArchive(assets=assets)

# Create the single Cloud Storage object, which contains all of the function's
# source code. ("main.py" and "requirements.txt".)
function_object = gcp.storage.BucketObject(f"{site_name}-cloudfunction",
    name="main.py-%f" % time.time(),
    bucket=function_bucket.name,
    source=archive)

# Create the Cloud Function, deploying the source we just uploaded to Google
# Cloud Storage.
visitor_function = gcp.cloudfunctions.Function(f"{site_name}-cloudfunction",
    available_memory_mb=128,
    entry_point="visitor_count",
    region="us-central1",
    runtime="python37",
    source_archive_bucket=function_bucket.name,
    source_archive_object=function_object.name,
    trigger_http=True)

function_iam = gcp.cloudfunctions.FunctionIamMember(f"{site_name}-cloudfunction",
    project=visitor_function.project,
    region=visitor_function.region,
    cloud_function=visitor_function.name,
    role="roles/cloudfunctions.invoker",
    member="allUsers",
)

# Export the cloud function URL.
pulumi.export("function_url", visitor_function.https_trigger_url)
