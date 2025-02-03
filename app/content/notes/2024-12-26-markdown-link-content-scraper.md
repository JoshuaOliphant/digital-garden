---
title: "Markdown Link Content Scraper"
status: "Evergreen"
created: "2024-12-26"
updated: "2024-12-26"
tags: [web-scraping, notebookllm, fastapi, claude, ai]
---
I've been using NotebookLLM for a few months now, which I quite enjoy. Sometimes
I have a main source that is a website, and then I also want to add all of the linked
sources. This is obviously very tedious, so today I created a quick little web
interface that does the hard work for me, which you can try out [here](https://link-content-scraper.fly.dev/).

The website takes in a link, and then scrapes all of the content from the link sources
(and the original source) as Markdown using [Jina API](https://jina.ai/reader/).
All of this Markdown is downloadable as a zip with all of the content in individual files.
Then I can simply grab all of these files and upload them to NotebookLLM.

This is part of my effort to build small, personalized projects with the help of
AI. I tend to use Claude the most. I took [Simon Willison's idea](https://simonwillison.net/2024/Dec/19/one-shot-python-tools/)
and created a Claude Project with project instructions that tell Claude how I
want one-shot projects to be built. Plus, [AI makes coding projects easy and fun](https://www.geoffreylitt.com/2024/12/22/making-programming-more-fun-with-an-ai-generated-debugger.html).

For a list of all my projects, visit my [projects page](https://anoliphantneverforgets.com/projects).