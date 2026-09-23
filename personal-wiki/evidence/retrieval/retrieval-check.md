# Retrieval check (no model)

Method: **bm25**, top 6 passages, over 70 indexed passages. Run with `wiki eval --retrieval-only`. This isolates the retrieval tool from Gemma.

## test-1: What exploration rate did I use when training the Ms. Pac-Man agent?

**PASS: expected passage(s) retrieved**. Expected ranks: `{'My hyperparameters': 3}`

| Rank | Location | Section | Score |
|---:|---|---|---:|
| 1 | `raw/ms-pacman-README.md:1-7` | Ms. Pac-Man DQN | 18.3493 |
| 2 | `raw/ms-pacman-README.md:225-237` | How the agent learns | 11.9951 |
| 3 | `raw/ms-pacman-README.md:47-61` | My hyperparameters | 10.099 |
| 4 | `raw/ms-pacman-README.md:204-220` | What I observed | 9.6124 |
| 5 | `raw/ms-pacman-README.md:79-92` | Results > Training budget | 6.5309 |

## test-2: How does my contacts app stop one user from seeing someone else's people?

**PASS: expected passage(s) retrieved**. Expected ranks: `{'Authentication and ownership > The ownership rule': 1}`

| Rank | Location | Section | Score |
|---:|---|---|---:|
| 1 | `raw/networking-tracker-README.md:178-207` | Authentication and ownership > The ownership rule | 14.437 |
| 2 | `raw/networking-tracker-README.md:1-9` | Networking Tracker | 13.7017 |
| 3 | `raw/networking-tracker-README.md:96-124` | Architecture | 11.3799 |
| 4 | `raw/networking-tracker-README.md:126-139` | Architecture > Request flow: adding a contact | 9.3314 |

## test-3: Which of my projects trained on a GPU and which trained only on a CPU?

**PASS: expected passage(s) retrieved**. Expected ranks: `{'Results > Training budget': 1, 'My Custom LLM: a tiny nanoGPT trained from scratch || 3. My choices, prediction, and run details': 3}`

| Rank | Location | Section | Score |
|---:|---|---|---:|
| 1 | `raw/ms-pacman-README.md:79-92` | Results > Training budget | 6.4923 |
| 2 | `raw/ms-pacman-README.md:20-45` | Run it yourself | 6.1995 |
| 3 | `raw/custom-llm-README.md:1-13` | My Custom LLM: a tiny nanoGPT trained from scratch | 5.627 |
| 4 | `raw/custom-llm-README.md:131-141` | 3. My choices, prediction, and run details | 5.4974 |
| 5 | `raw/networking-tracker-README.md:232-239` | Local setup > 1. Create the Neon project | 4.5596 |
| 6 | `raw/ms-pacman-README.md:259-270` | Repository layout | 4.0829 |

## test-4: What grade did I receive on the Ms. Pac-Man assignment?

**n/a: no passage should answer this; check that nothing retrieved states the answer**. Expected ranks: `{}`

| Rank | Location | Section | Score |
|---:|---|---|---:|
| 1 | `raw/ms-pacman-README.md:1-7` | Ms. Pac-Man DQN | 20.4342 |
| 2 | `raw/ms-pacman-README.md:225-237` | How the agent learns | 7.7821 |
| 3 | `raw/ms-pacman-README.md:204-220` | What I observed | 6.8168 |
| 4 | `raw/ms-pacman-README.md:20-45` | Run it yourself | 3.3125 |
| 5 | `raw/custom-llm-README.md:1-13` | My Custom LLM: a tiny nanoGPT trained from scratch | 2.6535 |
