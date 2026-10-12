<div align="center">

# 🎯 RedTeam Quest

### Learn to break AI systems, so you can defend them.

A hands-on game that teaches AI red-teaming through play: fool image classifiers, make chatbots leak secrets,
poison training data, hijack agents, then harden everything you broke. **41 levels, 7 worlds, 7 bosses.**
All of it runs on your own computer, against local models.

![Platform](https://img.shields.io/badge/platform-Linux-informational?logo=linux&logoColor=white)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![Runs locally](https://img.shields.io/badge/runs-100%25%20locally-success)
![Models](https://img.shields.io/badge/models-Ollama-black)
![Levels](https://img.shields.io/badge/levels-41-orange)
![License](https://img.shields.io/badge/license-MIT-green)

<img src="docs/screenshots/map.png" alt="The RedTeam Quest world map: seven worlds, each ending in a boss" width="90%">

<sub>The world map: seven worlds, each ending in a boss. Progress and XP are saved as you go.</sub>

</div>

---

## ✨ What makes it different

- 🧑‍✈️ **You are the manager, not the typist.** You rarely write code. You write a *spec*, a coding agent builds it, and you review what it made. That is how this work is done now, so it is what you practise.
- 🎲 **Real models, real attacks.** Graders attack a real neural network or a live local chatbot. Nothing is simulated, so a defense that only works on paper fails.
- 📊 **See it, don't just read it.** Interactive labs let you drag a slider and watch a real attack flip a real prediction.
- 🧭 **Three helpers, on your side.** A **Build agent** writes and tests your code, a **Guide** explains the lesson without giving answers, and on live levels a **Co-pilot** reads your attempts and suggests what to try next.
- 🏆 **Bosses that test mastery.** Each world ends with a realistic problem and fresh hidden test cases every run, so you cannot memorise your way through.
- 🔒 **Everything is local.** Models run on your machine and your progress never leaves it.

## 🗺️ The seven worlds

| | World | You will... | Levels |
|---|---|---|:---:|
| 🖼️ | **Vision attacks** | Fool image classifiers with gradients, transfer, black-box queries and printable patches, then break a "robust" model | 7 |
| 💬 | **LLM attacks** | Extract secrets from live chatbots, hijack an email assistant, poison an agent's memory and a RAG knowledge base | 8 |
| 👁️ | **Multimodal** | Beat vision-language models with a single word written on a photo, adversarial images and hidden instructions | 4 |
| 🧪 | **Training & privacy** | Plant a backdoor, tell who was in a model's training data, steal a model through its API | 4 |
| 🤖 | **Agents & tools** | Audit file, shell and URL-fetching tools; decide which agent messages to trust | 6 |
| 🛡️ | **Defense & forensics** | Train robust models, certify them, catch bad evaluations, hunt backdoors, evade a safety classifier | 7 |
| 📝 | **Red-team craft** | Threat-model a system, triage findings, write the report an engineer will act on | 5 |

## 🎮 How a level works

1. 📖 **Read the mission.** A short briefing, plus interactive visualisations of the idea.
2. ✍️ **Write your spec.** Tell the Build agent what to build: the threat model, the budget, how success is measured.
3. 🔍 **Review and test.** The agent can run your level's grader as a private dry run and report timing and crashes before you grade it for real.
4. ✅ **Run the grader.** It attacks a real model with your code. Pass and you earn XP.
5. 🧠 **Take the quiz** for bonus XP and move up the ranks, from *Script Kiddie* to *Grandmaster*.

<table>
<tr>
<td width="50%" valign="top">
<b>🧩 Delegate, review, learn</b><br>
Every level mixes a briefing, a live visualisation and an agent that builds your idea.<br><br>
<img src="docs/screenshots/level.png" alt="A level: mission, the idea, an interactive lab, and your Build agent">
</td>
<td width="50%" valign="top">
<b>🎯 Real grading, real feedback</b><br>
Graders attack a real model with your code and show exactly what happened.<br><br>
<img src="docs/screenshots/grader.png" alt="The grader showing accuracy dropping from 98% to 2% under attack">
<br><br>
<b>💥 Attack live chatbots</b><br>
Talk a real local model into revealing a secret, rung by rung.<br><br>
<img src="docs/screenshots/live.png" alt="A live-target level: a five-rung ladder of increasingly defended chatbots">
</td>
</tr>
</table>

## 🧰 What you need

| | |
|---|---|
| 🐧 **OS** | Linux (tested on Ubuntu). macOS may work; Windows is untested. |
| 🎮 **GPU** | NVIDIA with about 12 GB of VRAM recommended. CPU-only works, but the model-based levels are very slow. |
| 💾 **Disk** | About 15 GB free (PyTorch, two language models, datasets). |
| 🐍 **Python** | 3.10 or newer (3.12 recommended). |
| 🦙 **[Ollama](https://ollama.com/download)** | Runs the local models the live levels attack. |
| 🤖 **[Claude Code](https://docs.claude.com/en/docs/claude-code/setup)** | Powers the Build agent, Guide and Co-pilot. **You sign in with your own account.** The game uses whatever account is logged in on your computer, so nobody else's tokens are involved. |

## 🚀 Quick start

```bash
git clone https://github.com/guyf2/redteam-quest && cd redteam-quest
./setup.sh          # one time: Python env, dependencies, models, checks
claude              # one time: sign in with your own account, then exit
./start-game.sh     # play! opens http://127.0.0.1:8765
```

`./setup.sh` is safe to re-run, and tells you plainly if anything is missing (Ollama, Claude Code, GPU).

| Option | What it does |
|---|---|
| `--skip-models` | Don't pull the Ollama models (`llama3.2:3b`, `qwen2.5vl:7b`) |
| `--skip-warmup` | Don't prepare the small MNIST target up front |
| `--full-warmup` | Also pre-download CIFAR-10 and CLIP (about 0.7 GB; otherwise fetched the first time you open a multimodal level) |
| `--no-launcher` | Don't add a "RedTeam Quest" entry to your app menu |

Your progress is saved to `game/state.json` and your agent chats to `game/chat.json`, both local to you.

## 🩺 Troubleshooting

| Problem | Fix |
|---|---|
| Agent or Guide says `claude` is not found or not signed in | Install Claude Code, run `claude` once and sign in |
| Chatbot levels do not respond | Check Ollama is running (`ollama list`) and the models are pulled |
| Everything is slow | Run `nvidia-smi`. If it says "Driver/library version mismatch", reboot |
| Port 8765 is in use | Another copy of the game is already running |
| First multimodal level pauses | It is downloading CIFAR-10 and CLIP once; run `./setup.sh --full-warmup` to do it ahead of time |

## 🛡️ Safety

Every target is a local model running on your own machine, and nothing here touches anyone else's systems.
Use what you learn only on systems you own or are explicitly authorised to test.

## 📄 License

[MIT](LICENSE). Free to use, modify and share.

<div align="center">

<sub>Built for people who want to defend AI systems by learning to break them first.</sub>

</div>
