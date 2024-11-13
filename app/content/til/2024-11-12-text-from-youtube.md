---
title: "How to get text from YouTube videos"
status: "Budding"
created: "2023-11-12"
updated: "2024-11-12"
tags: [ai]
---
Yesterday, I was reading a blog post about writing for a tech audience, which is [here](https://rmoff.net/2023/07/19/blog-writing-for-developers/?utm_source=changelog-news) if you're curious. It linked out to a YouTube video that is quite long (I haven't actually watched it yet) but I wanted to get the text from it.

I remembered that Simon Willison created a command line tool for interacting with LLMs called [llm](https://github.com/simonw/llm?tab=readme-ov-file). It has a plugin system, and he also made a little [plugin for Whisper](https://github.com/simonw/llm-whisper-api). I had the `llm` tool installed already, so I followed the instructions for adding the Whisper plugin.

This whole idea entered my brain from the first blog post I referenced above because it mentions a tool called [yt-dlp](https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#output-template), which he suggests using to download the audio version of the YouTube video if readers would rather listen to it. I've been using Google's NotebookLM quite a lot, and I wanted to get the text so I could add it to a notebook about writing. So, I installed this tool as well. My first attempt looked like this:

```bash
yt-dlp --extract-audio --audio-format mp3 https://youtu.be/vtIzMaLkCaM\?si\=0JT8gUmso781EdGc -o "%(title)s.%(ext)s" && \
llm whisper-api "$(ls -t *.mp3 | head -1)" > transcription.txt
[youtube] Extracting URL: https://youtu.be/vtIzMaLkCaM?si=0JT8gUmso781EdGc
[youtube] vtIzMaLkCaM: Downloading webpage
[youtube] vtIzMaLkCaM: Downloading ios player API JSON
[youtube] vtIzMaLkCaM: Downloading mweb player API JSON
[youtube] vtIzMaLkCaM: Downloading m3u8 information
[info] vtIzMaLkCaM: Downloading 1 format(s): 251
[download] Destination: LEADERSHIP LAB： The Craft of Writing Effectively.webm
[download] 100% of   64.27MiB in 00:00:02 at 27.03MiB/s
[ExtractAudio] Destination: LEADERSHIP LAB： The Craft of Writing Effectively.mp3
Deleting original file LEADERSHIP LAB： The Craft of Writing Effectively.webm (pass -k to keep)
Error: Client error '413 Payload Too Large' for url 'https://api.openai.com/v1/audio/transcriptions'
For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/413
```

I had never used `yt-dlp` before, so I got Claude's help constructing the command. I found in the [Whisper documentation](https://platform.openai.com/docs/guides/speech-to-text) that it can only process payloads up to 25 MB. Otherwise, you have to start chunking it, which I didn't feel like doing. I asked Claude how to compress the data to less than 25 MB. It said I use this tool:

```bash
brew install ffmpeg
```

I didn't think to tell Claude how large the file size was, so it didn't get below 25 MB the first time. Then I told it the file size was 57 MB, and interestingly, it guessed that it was a lecture:

```
Since 56k bitrate still gives us a 33MB file, we need to be more aggressive with the compression to get under 25 MB. Let's try an even lower bitrate and convert to mono (single channel) since this appears to be a speech recording where stereo isn't crucial:

```bash
ffmpeg -i "LEADERSHIP LAB： The Craft of Writing Effectively.mp3" -ac 1 -b:a 40k output.mp3
```

This command:
- `-ac 1` converts to mono (single audio channel)
- `-b:a 40k` sets an even lower bitrate of 40kbps

After running this, check the size:
```bash
ls -lh output.mp3
```

If it's still too large, you could try:
```bash
ffmpeg -i "LEADERSHIP LAB： The Craft of Writing Effectively.mp3" -ac 1 -b:a 32k output.mp3
```

Since this appears to be a lecture or speech recording, you can go lower with the bitrate without severely impacting speech intelligibility. Speech requires less bitrate than music to remain comprehensible. The mono conversion alone should reduce the file size significantly, and combined with the lower bitrate, this should get you under 25MB while maintaining acceptable speech quality.
```

The first command from Claude's instructions worked to get the file size down to 19 MB. Unfortunately, it was still too large for the Whisper plugin in the LLM tool.

```bash
llm whisper-api output.mp3 > transcription.txt
Error: The read operation timed out
```

So, in the end, I just pulled the `curl` command straight out of the OpenAI Whisper documentation I shared earlier, which looks like this:

```bash
curl --request POST \
  --url https://api.openai.com/v1/audio/transcriptions \
  --header "Authorization: Bearer $OPENAI_API_KEY" \
  --header 'Content-Type: multipart/form-data' \
  --form file=@output.mp3 \
  --form model=whisper-1
```

It finally worked, and I got my text. I may look at the `llm` Whisper plugin to see if I can update it to work with larger file sizes. If I do, I'll add an update here.
