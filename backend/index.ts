import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";

const siteDomain = "lebergarrett.com";
const siteName = "lebergarrett";

const websiteBucket = new gcp.storage.Bucket(siteName, {
    cors: [{
        maxAgeSeconds: 3600,
        methods: [
            "GET",
        ],
        origins: [`https://${siteDomain}`, `https://www.${siteDomain}`],
        responseHeaders: ["*"],
    }],
    forceDestroy: true,
    location: "US",
    uniformBucketLevelAccess: false,
    website: {
        mainPageSuffix: "index.html",
    },
});

const bucketReader = new gcp.storage.DefaultObjectAccessControl(siteName, {
    bucket: websiteBucket.name,
    role: "READER",
    entity: "allUsers",
});

const websiteBackend = new gcp.compute.BackendBucket(siteName, {
    description: "Backend for static website",
    bucketName: websiteBucket.name,
    enableCdn: true,
});

const websiteSslCertificate = new gcp.compute.ManagedSslCertificate(siteName, {
    managed: {
        domains: [`${siteDomain}.`, `www.${siteDomain}.`],
    }
});

const websiteUrlmap = new gcp.compute.URLMap(siteName, {
    description: "URLmap for static website",
    defaultService: websiteBackend.id,
    hostRules: [
        {
            hosts: [siteDomain],
            pathMatcher: "all-paths",
        },
    ],
    pathMatchers: [
        {
            name: "all-paths",
            defaultService: websiteBackend.id,
            pathRules: [
                {
                    paths: ["/*"],
                    service: websiteBackend.id,
                }
            ]
        },
    ],
    // tests: [{
    //     service: staticBackendBucket.id,
    //     host: "hi.com",
    //     path: "/home",
    // }],
});

const httpToHttpsUrlMap = new gcp.compute.URLMap(`${siteName}-http-to-https`, {
    description: "HTTP to HTTPS redirect for static website",
    defaultUrlRedirect: {
        stripQuery: false,
        httpsRedirect: true,
    }
});

const websiteTargetHttpsProxy = new gcp.compute.TargetHttpsProxy(siteName, {
    urlMap: websiteUrlmap.id,
    sslCertificates: [websiteSslCertificate.id],
});

const httpToHttpsProxy = new gcp.compute.TargetHttpProxy(`${siteName}-http-to-https`, {
    urlMap: httpToHttpsUrlMap.id,
});


const websiteGlobalAddress = new gcp.compute.GlobalAddress(siteName, {});

const websiteGlobalForwardingRule = new gcp.compute.GlobalForwardingRule(siteName, {
    ipProtocol: "TCP",
    loadBalancingScheme: "EXTERNAL",
    portRange: "443",
    target: websiteTargetHttpsProxy.selfLink,
    ipAddress: websiteGlobalAddress.id,
});

const httpToHttpsForwardingRule = new gcp.compute.GlobalForwardingRule(`${siteName}-http-to-https`, {
    ipProtocol: "TCP",
    loadBalancingScheme: "EXTERNAL",
    portRange: "80",
    target: httpToHttpsProxy.selfLink,
    ipAddress: websiteGlobalAddress.id,
});

const websiteDnsZone = new gcp.dns.ManagedZone(siteName, {
    description: "lebergarrett.com DNS zone",
    dnsName: `${siteDomain}.`,
});

const websiteDnsRecord = new gcp.dns.RecordSet(siteName, {
    name: pulumi.interpolate`${websiteDnsZone.dnsName}`,
    type: "A",
    ttl: 300,
    managedZone: websiteDnsZone.name,
    rrdatas: [websiteGlobalAddress.address],
});

const websiteCname = new gcp.dns.RecordSet(`${siteName}-cname`, {
    name: pulumi.interpolate`www.${websiteDnsZone.dnsName}`,
    managedZone: websiteDnsZone.name,
    type: "CNAME",
    ttl: 300,
    rrdatas: [`${siteDomain}.`],
});

// ----- Visitors Application -----

// have Cloud Function create the firestore document instead of Pulumi

const visitorFunction = new gcp.cloudfunctions.HttpCallbackFunction(siteName, {
    runtime: "python3.9",
    callback: (req, res) => {
        // function here
    },
})


// Export the DNS name of the bucket
//export const bucketName = websiteBucket.url;
