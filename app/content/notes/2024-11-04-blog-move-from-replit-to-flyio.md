---
title: "Blog Move from Replit to Fly.io"
status: "Budding"
created: "2024-11-03"
updated: "2024-11-03"
tags: [TIL, fly, docker, replit]
---

Yesterday, I moved my blog from Replit to [fly.io](fly.io). Replit was nice because it allowed me to quickly and easily get my blog out into the world. I had been wanting to create my own blog from scratch for a while, and I have been enjoying tweaking it however I like. Unfortunately, Replit doesn't have an API or any facility to create CI/CD pipelines. I listen to the [Changelog podcast](https://changelog.com) regularly, and they are always advertising that they use fly.io, so I looked into it and found that it was super easy to get going. This will be my notes on the process.

To get started, at least on a Mac, I followed the [quickstart](https://changelog.com):

```bash
brew install flyctl
# or login if you have an account already
fly auth signup  
# configures and tries to launch your app
fly launch
```

The problem that I immediately ran into was that it misidentified my application as NodeJS because I have a `node_modules` directory. The tech stack for my blog is Python, FastAPI, HTMX, and Tailspin. The workaround for this problem was to create my own Dockerfile. I'm using `uv`, and they had [instructions for creating a Dockerfile](https://docs.astral.sh/uv/guides/integration/docker/#installing-uv), so I used that. Then it was just a matter of pointing the launch command at the Dockerfile:

```bash
fly deploy --dockerfile Dockerfile
```