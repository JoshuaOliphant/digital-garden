---
title: Today I created my first Claude Agent skill
status: Budding
created: '2025-10-19'
updated: '2025-10-19'
tags:
- ai
- claude
- claude code
- anthropic
- agent skills
growth_stage: budding
---

Earlier this week Anthropic released [Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills). I've been reading about them all week, and today I finally built one myself. I've been using a tool called Mochi for spaced repetition, but not as much as I'd like to because it's a bit tedious to create cards, and I've been intending to create some AI tool or process to make it easier. So I created an agent skill for it, and even created my own plugin marketplace to store it. I'm sure I'll create more plugins.

Here's the process I went through to create the agent skill.

## Meta Skill-Creator

Anthropic created a skills repository in GitHub, which acts as a [plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces), including a meta [skill-creator](https://github.com/anthropics/skills/tree/main/skill-creator). I used Claude Code to build my Mochi skill, and from the README.md you can see that you simply add it with:

`/plugin marketplace add anthropics/skills`

Then either browse the available skills with the slash command `/plugins` or specifically add it with:

`/plugin install skill-creator@anthropic-agent-skills`

## Creating the Mochi creator skill

Once you have skills installed, the skill metadata from the `SKILL.md` frontmatter is loaded into the Claude Code context when you first fire it up. Then all you need to say is something like "Help me create a new skill for xyz...". In my case, I created my skill over two separate conversations with Claude Code. The first prompt I used was:

```
I want your help to create a new mochi-creator skill that uses the Mochi API to create new Mochi cards and collections. Here is the link to their API documentation that you should familiarize yourself with before creating this new skill https://mochi.cards/docs/api/
```

Claude Code created a simple skill that worked by implementing the Mochi API. I put it in a [Github repository](https://github.com/JoshuaOliphant/claude-plugins), and gave it the documentation for setting up a [plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces), which it easily accomplished. I was able to install the marketplace and plugin with the skill with these commands:

```
# Add this marketplace
/plugin marketplace add joshuaoliphant/claude-plugins

# Install the plugin
/plugin install mochi-creator@oliphant-plugins
```

I tested it out and it worked fine, but...

## Improving the Skill

I realized the Mochi skill lacked the knowledge to create really good flashcards, and then I remembered that I had read an article by Andy Matuschak titled [How to write good prompts: using spaced repetition to create understanding](https://andymatuschak.org/prompts/) a few months ago. I fired up a new instance of Claude Code and gave it this prompt:

```
I want you to help me update the mochi-creator plugin in @plugins/mochi-creator/skills/mochi-creator/ . Here are the steps you should take:
- Read this blog post on spaced repetition, this is the basis for improving the mochi 
creator skill https://andymatuschak.org/prompts/
- Read this documentation on what claude agent skills are 
https://docs.claude.com/en/docs/claude-code/skills
- Tell me how you plan to improve this skill 
```

I tried it out on Andy Matuschak's article with a fresh instance of Claude Code; it created 39 flashcards of various types, and tagged them for me.

You can try out the Mochi Creator skill from my [plugin marketplace repository](https://github.com/JoshuaOliphant/claude-plugins).
