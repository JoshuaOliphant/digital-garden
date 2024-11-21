---
title: "Route53 to Fly Subdomain"
status: "Evergreen"
created: "2023-11-21"
updated: "2024-11-21"
tags: [aws, route53, fly, subdomain]
---
I created this face shape identifier tool that helps people identify their face shapes and get
personalized hairstyle recommendations, after looking up haircuts and how to choose the right one for my face shape.
I deployed it to [fly.io](fly.io) and wanted to create a subdomain for my main domain, [anoliphantneverforgets.com](anoliphantneverforgets.com),
and point it to the Fly app. They have documentation about how to do this [here](https://fly.io/docs/networking/custom-domain/#teaching-your-app-about-custom-domains).

Here are the steps I took to create the subdomain:

1. Decide on the subdomain name. I chose `faceshapeidentifier.anoliphantneverforgets.com`.
2. Run the fly command to add a cert:
```bash
fly certs add faceshapeidentifier.anoliphantneverforgets.com

You are creating a certificate for faceshapeidentifier.anoliphantneverforgets.com
We are using Let's Encrypt for this certificate.

You can configure your DNS for faceshapeidentifier.anoliphantneverforgets.com by:

1: Adding an CNAME record to your DNS service which reads:

    CNAME faceshapeidentifier. face-shaper.fly.dev
```
3. I went to Route53 in the AWS console and created a new CNAME record for the subdomain.
  - Route53 -> Hosted zones -> anoliphantneverforgets.com -> Create record
  - Record name: `faceshapeidentifier`
  - Record type: `CNAME`
  - Value: `face-shaper.fly.dev`
4. Waited for the DNS changes to propagate.
5. Done!
