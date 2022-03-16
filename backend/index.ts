import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";

const websiteBucket = new gcp.storage.Bucket("lebergarrett", {
    cors: [{
        maxAgeSeconds: 3600,
        methods: [
            "GET",
            "HEAD",
            "PUT",
            "POST",
            "DELETE",
        ],
        origins: ["*"],
        responseHeaders: ["*"],
    }],
    forceDestroy: true,
    location: "US",
    uniformBucketLevelAccess: false,
    website: {
        mainPageSuffix: "index.html",
    },
});

const publicRule = new gcp.storage.BucketAccessControl("lebergarrett", {
    bucket: websiteBucket.name,
    role: "READER",
    entity: "allUsers",
});

// Export the DNS name of the bucket
export const bucketName = websiteBucket.url;
