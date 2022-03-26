import pulumi
import pulumi_gcp

siteDomain = "lebergarrett.com"
siteName = "lebergarrett"


websiteBucket = storage.Bucket(siteName, 
    cors=[
        max_age_seconds=3600,
        methods=[
            "GET",
        ],
        origins=[`https://${siteDomain}`, `https://www.${siteDomain}`],
        response_headers=["*"],
    ],
    forceDestroy=True,
    location="US",
    uniformBucketLevelAccess=False,
    website=gcp.storeage.BucketWebsiteArgs(
        main_page_suffix: "index.html",
    ))

# Export the DNS name of the bucket
#pulumi.export('bucket_name', bucket.url)
