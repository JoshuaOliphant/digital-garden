---
title: "OpenAPI to Click App"
status: "Budding"
created: "2024-10-31"
updated: "2024-10-31"
tags: [python, openapi, click, claude, ai]
---
About 3 weeks ago, I had an idea to create an app that would take an OpenAPI spec and generate a Click app. I've been working on it in my free time and I've got a basic version working. Its the sort of project I never would have attempted in the past, but I had the help of Claude so it was pretty easy.

I use a Python OpenAPI client generator called `openapi-python-client` to generate the client code. Then I use Jinja templates for the Click app, which wraps the client code. The app has a command for each endpoint in the OpenAPI spec. The commands take the parameters defined in the spec and call the corresponding client method.

I think it could be really useful for people who want to create a Click app to interact with an API but don't want to write all the boilerplate code.

Feel free to try it out: [openapi-to-click-app](https://github.com/JoshuaOliphant/openapi_to_click)
