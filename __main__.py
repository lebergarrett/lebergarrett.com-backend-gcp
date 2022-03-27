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

# Visitors Application

# visitor_function = gcp.cloudfunctions.Function(site_name,
#     description="Visitors app function",
#     runtime="python3.9",
#     available_memory_mb=128,
#     source_archive_bucket="", #TODO
#     source_archive_object="", #TODO
#     trigger_http=True,
#     entry_point="visitor_count"
# )
# Export the DNS name of the bucket
#pulumi.export('bucket_name', bucket.url)
