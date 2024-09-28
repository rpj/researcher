## researcher

Do some research via [gpt-researcher](https://github.com/assafelovic/gpt-researcher)

### prereqs

By default, expects an [OpenAI API key](https://platform.openai.com) in the `OPENAI_API_KEY` environment variable and a [Tavily API key](https://app.tavily.com/) in `TAVILY_API_KEY`.

Also expects an [R2 bucket](https://developers.cloudflare.com/r2/) set up and keys as `AWS_*` environment variables.

### irc bot

```
$ git clone https://github.com/rpj/researcher.git
$ cd researcher
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
$ python bot.py --nickname ... --server ... --channel ...
```

Prompt format: `research! query ... ...`

### cli utility

```
$ python lib/research.py --help
```