---
title: "Setting Up a Custom Subdomain with Route53 and Fly.io"
status: "Evergreen"
created: "2023-11-21"
updated: "2024-11-21"
tags: [aws, route53, fly, subdomain, dns-configuration, custom-domain, web-hosting]
---

I built this face shape identifier tool that helps people get personalized hairstyle recommendations based on their face shape, after looking up information on how to choose the right hairstyle for my own face shape. After deploying it to [fly.io](https://fly.io), I wanted to make it accessible through a subdomain of my main website [anoliphantneverforgets.com](https://anoliphantneverforgets.com).

![alt text](<../../static/images/Setting Up a Custom Subdomain with Route53 and Fly-1.io - visual selection.png>)

Here's how I set it up:

## Prerequisites

Before starting, you'll need:

- A domain managed by AWS Route53
- A deployed application on Fly.io
- The Fly CLI installed

## Step-by-Step Configuration

### 1. Plan Your Subdomain

I chose `faceshapeidentifier.anoliphantneverforgets.com` for my tool.

### 2. Generate SSL Certificate

Run this command to add a certificate:

```bash
fly certs add faceshapeidentifier.anoliphantneverforgets.com
```

Fly.io will give you the CNAME record details you need for the next step.

### 3. Configure Route53

1. Go to Route53 in the AWS console
2. Navigate to Hosted zones → your domain
3. Click "Create record" and set up:
   - Record name: `faceshapeidentifier`
   - Record type: `CNAME`
   - Value: `face-shaper.fly.dev`
   - TTL: 300 seconds

### 4. Verify Everything Works

The DNS changes usually take 5-30 minutes to propagate. You can check the status with:

```bash
dig faceshapeidentifier.anoliphantneverforgets.com CNAME
```

If things aren't working:

1. Check the certificate status:

```bash
fly certs show faceshapeidentifier.anoliphantneverforgets.com
```

2. Make sure your app is running:

```bash
fly status
```

Want to learn more? Check out the [Fly.io custom domain docs](https://fly.io/docs/networking/custom-domain/) or the [AWS Route53 guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring.html).
