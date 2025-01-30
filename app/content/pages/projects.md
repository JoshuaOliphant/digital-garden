---
title: "projects"
created: "2024-11-21"
updated: "2024-11-21"
status: "Budding"
---
## Face Shape Identifier

An AI-powered tool that helps identify face shapes from uploaded photos.
I was looking up haircuts and how to choose the right one for my face shape, and I thought it would be fun to build a tool that could help people identify their face shapes and get personalized hairstyle recommendations.

- [Try it out](https://faceshapeidentifier.anoliphantneverforgets.com)
- [Github repo](https://github.com/JoshuaOliphant/face_shaper)

## Markdown Link Content Scraper

This project is a web application that scrapes content from a given URL and all its linked pages, converting the content to Markdown format using the Jina API. The application shows real-time and allows users to download all scraped content as a ZIP file. The project uses FastAPI for the backend, a simple HTML/JavaScript frontend, and is containerized using uv for efficient Python dependency management.

The idea came from my use of Notebook LLM, because often I want to add a source and the sources that are linked from it. But I don't want to click through each link and get the content because it can get very tedious, particularly when there are lots of links. Now I can get all of the content as Markdown and upload it all at once to NotebookLLM.

- [Try it out](https://link-content-scraper.anoliphantneverforgets.com)
- [Github repo](https://github.com/JoshuaOliphant/Link-Content-Scraper)

## Entiendo

My wife gave me this idea, which is to build a tool to help interpret complicated documents. Her idea more specifically was an AI app to scan contracts and go through each paragraph and explain it in Layman's terms. I thought it could be a more general-purpose tool, so I decided to go ahead and build it.

It uses the new citations API that Anthropic recently added. Plus, while I was digging around in their documentation I found that they also handle PDFs, so I am using Anthropic for that as well.

- [Try it out](https://entiendo.anoliphantneverforgets.com)
- [Github repo](https://github.com/JoshuaOliphant/entiendo)
