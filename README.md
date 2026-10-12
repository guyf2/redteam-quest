# RedTeam Quest

A hands-on game that teaches you to attack and defend AI systems: image classifiers, chatbots, vision-language
models, training pipelines and agents. You play in your browser. For most levels you don't type code: you write a
spec, a coding agent builds it, and a grader attacks a real model with your result. Others are live: you try to get
a real local chatbot to leak a secret, and a Guide and Co-pilot help you think it through.

Everything runs on your own computer. Nothing is sent anywhere except what your own Claude account does.

## What you need

| | |
|---|---|
| OS | Linux (tested on Ubuntu). macOS may work, Windows is untested. |
| GPU | NVIDIA with about 12 GB of VRAM recommended. CPU-only works but the model-based levels are very slow. |
| Disk | About 15 GB free (PyTorch, two language models, datasets). |
| Python | 3.10 or newer (3.12 recommended). |
| [Ollama](https://ollama.com/download) | The local models the live levels attack. |
| [Claude Code](https://docs.claude.com/en/docs/claude-code/setup) | Powers the Build agent, Guide and Co-pilot. **You sign in with your own account**; the game uses whatever account is logged in on your computer, so nobody else's tokens are involved. |

## Setup (once)

```bash
git clone <this repo> redteam-quest && cd redteam-quest
./setup.sh
```

The script creates a Python environment, installs dependencies, pulls the two Ollama models (`llama3.2:3b`,
`qwen2.5vl:7b`), prepares the small MNIST target, and tells you if anything is missing (Ollama, Claude Code, GPU).
It is safe to re-run. Options: `--skip-models`, `--skip-warmup`, `--full-warmup` (also pre-download CIFAR-10 + CLIP, about 0.7 GB; otherwise they download the first time you open a multimodal level), `--no-launcher`.

Before your first game, run `claude` once in a terminal and sign in.

## Play

```bash
./start-game.sh        # starts the game and opens http://127.0.0.1:8765
```

(`./play.sh` does the same from a terminal. Setup also adds a "RedTeam Quest" entry to your app menu.)

The game saves your progress in `game/state.json` and your agent chats in `game/chat.json`, both local to you.

## How it works

Levels come in worlds (vision, LLM, multimodal, training, agents, defense, red-team craft), each ending in a boss.
Read the mission, tell the agent what to build, review and run the grader, then take the quiz for bonus XP.
Hints cost XP. The Guide explains the lesson without giving answers; on live-target levels the Co-pilot reads
your attempts and suggests what to try next, but never sends anything for you.

## Troubleshooting

- **Agent / Guide says `claude` not found or not signed in:** install Claude Code and run `claude` once.
- **Chatbot levels fail to respond:** make sure Ollama is running (`ollama list`) and the models are pulled.
- **Everything is slow:** check `nvidia-smi`. If it says "Driver/library version mismatch", reboot.
- **Port 8765 in use:** another copy of the game is running.

## Safety

All targets are local models running on your machine. Use what you learn on systems you own or are authorised to test.
