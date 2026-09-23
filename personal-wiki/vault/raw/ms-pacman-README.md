# Ms. Pac-Man DQN

A Deep Q-Network trained to play Ms. Pac-Man (`ALE/MsPacman-v5`) for Class 3, Assignment 2.
It uses the supplied classroom notebook from [pepealonso95/pacman-dqn](https://github.com/pepealonso95/pacman-dqn)
(commit `d1b9e9d`). Only the three hyperparameter choices in section 1 were changed.

**[Open the executed notebook](pacman_dqn.ipynb)** — every cell output from the final training and evaluation run is saved in it.

## Contents

- [Run it yourself](#run-it-yourself)
- [My hyperparameters](#my-hyperparameters)
- [What I expected](#what-i-expected)
- [Results](#results)
- [What I observed](#what-i-observed)
- [How the agent learns](#how-the-agent-learns)
- [Limitation and next experiment](#limitation-and-next-experiment)
- [Repository layout](#repository-layout)

## Run it yourself

**Google Colab:** [open the notebook in Colab](https://colab.research.google.com/github/bongo-drums/ms-pacman/blob/main/pacman_dqn.ipynb).
Select **Runtime → Change runtime type → T4 GPU**, then **Runtime → Run all**. The first code cell installs every package.

**Locally (Windows, what I used):** Python 3.11–3.13 is required. On Windows, install the CUDA build of PyTorch
*before* the notebook runs; otherwise its install cell pulls the CPU-only build.

```powershell
py install 3.13
py -V:3.13 -m venv $HOME\.venvs\ms-pacman
$py = "$HOME\.venvs\ms-pacman\Scripts\python.exe"
& $py -m pip install torch --index-url https://download.pytorch.org/whl/cu128
& $py -m pip install -r requirements.txt nbclient ipykernel
& $py -m ipykernel install --user --name py313
```

Then either open `pacman_dqn.ipynb` in VS Code or Jupyter with the `py313` kernel and choose **Run All**, or run it headless:

```powershell
& $py run.py        # executes the notebook in place and saves every output
& $py collect.py    # copies the newest run into results/ and regenerates the Results section below
& $py analyze.py    # replays the saved agents on the evaluation seeds -> results/evaluation_breakdown.md
```

`run.py --max-minutes N` stops training once after *N* minutes, just like pressing Interrupt, and still runs the evaluation.

## My hyperparameters

| Setting | Value | Why |
|---|---|---|
| Exploration | **0.10** | Half the notebook's 0.20 and closer to the 5% used at evaluation, so the agent trains in conditions like the ones it is scored in. Fewer random moves also mean fewer random deaths, so games last longer and the agent sees more of the maze. 10% still leaves room to try new moves. |
| Episodes | **1,000** | A 2-minute setup check ran at ~373 decisions per second, so 1,000 games (roughly 0.6–1.0 million decisions) fits in under an hour on this laptop. That is about 15–20× the setup check's budget, which was clearly too small to learn anything. |
| Learning rate | **0.0001** | The standard Adam learning rate for DQN, and the notebook's reference value. The setup check showed stable, finite loss at this rate. A larger step risks unstable Q-values over a long run; a smaller one would learn too slowly for this budget. |

All other settings are the notebook's defaults, including replay memory (5,000), batch size, target sync, and the
evaluation settings (seeds 101–505, 5% exploration, 3,000-decision limit).

**Setup check (not the submitted run).** Before choosing, I ran the notebook at its defaults (0.20 exploration,
learning rate 0.0001) with training stopped after 2 minutes: 77 games, 44,816 decisions, 10,954 learning updates.
The untrained network averaged 492 and the briefly trained one 190. That measured the hardware speed and showed that
a few minutes of training is not enough.

## What I expected

*Written before the final training run started.*

I expected the trained agent to beat the untrained baseline (mean 492), probably landing somewhere around 600–1,000.
Games 1–1,000 give roughly 15–20× the setup check's experience, and lower exploration should let games run longer.
I expected the first few hundred games to stay near the baseline while the network learns basic move values,
then a gradual rise in the training scores. I also expected two sources of noise:

- **Small sample.** Five evaluation games is small; one untrained game alone scored 800.
- **Forgetting.** The replay memory holds only 5,000 decisions (about eight games), so the agent could forget earlier
  lessons, and scores might rise and then fall.

<!-- evidence:start -->
## Results

### Training budget

| | |
|---|---|
| Exploration | 0.1 |
| Learning rate | 0.0001 |
| Episodes requested / completed | 1000 / 1000 |
| Decisions | 622,643 |
| Learning updates | 155,411 |
| Elapsed training time | 31.3 min (includes periodic demos) |
| Status | completed |
| Hardware | 13th Gen Intel(R) Core(TM) i9-13900H + NVIDIA GeForce RTX 4060 Laptop GPU (CUDA) |
| Software | Python 3.13.15, PyTorch 2.11.0+cu128, Gymnasium 1.3.0, ALE 0.11.2 |
| Run folder | `20260915_103037_357579` |

### Evaluation: untrained vs. trained

Same five seeds, 5% exploration, and a 3,000-decision limit for both. The baseline is the untrained network.

| Game | Seed | Untrained | Trained |
|---:|---:|---:|---:|
| 1 | 101 | 350 | 590 |
| 2 | 202 | 500 | 230 |
| 3 | 303 | 320 | 2380 |
| 4 | 404 | 800 | 350 |
| 5 | 505 | 490 | 490 |
| **Mean** | | **492.0** | **808.0** |

Change in mean score: **+316.0**. Time-limited games before / after: 0 / 0. Source: [comparison.json](results/comparison.json)

### Training dashboard

![Training dashboard](results/training_dashboard.png)

### Gameplay

Each GIF is the first 20 seconds of a game at 4× speed.

| Untrained | Best trained game |
|---|---|
| ![Untrained](results/gifs/episode_0000.gif) | ![Best trained](results/gifs/final_best.gif) |
| seed 101, score 350 | best of five, score 2380 |

#### Progress during training

Each sample is a separate evaluation game (seed 101), recorded without changing the network.

| After 25 games | After 50 games | After 75 games | After 100 games |
|---|---|---|---|
| ![Episode 25](results/gifs/episode_0025.gif) | ![Episode 50](results/gifs/episode_0050.gif) | ![Episode 75](results/gifs/episode_0075.gif) | ![Episode 100](results/gifs/episode_0100.gif) |
| score 1010 | score 340 | score 110 | score 480 |

| After 125 games | After 150 games | After 175 games | After 200 games |
|---|---|---|---|
| ![Episode 125](results/gifs/episode_0125.gif) | ![Episode 150](results/gifs/episode_0150.gif) | ![Episode 175](results/gifs/episode_0175.gif) | ![Episode 200](results/gifs/episode_0200.gif) |
| score 500 | score 3750 | score 1280 | score 960 |

| After 225 games | After 250 games | After 275 games | After 300 games |
|---|---|---|---|
| ![Episode 225](results/gifs/episode_0225.gif) | ![Episode 250](results/gifs/episode_0250.gif) | ![Episode 275](results/gifs/episode_0275.gif) | ![Episode 300](results/gifs/episode_0300.gif) |
| score 270 | score 780 | score 360 | score 920 |

| After 325 games | After 350 games | After 375 games | After 400 games |
|---|---|---|---|
| ![Episode 325](results/gifs/episode_0325.gif) | ![Episode 350](results/gifs/episode_0350.gif) | ![Episode 375](results/gifs/episode_0375.gif) | ![Episode 400](results/gifs/episode_0400.gif) |
| score 510 | score 460 | score 930 | score 110 |

| After 425 games | After 450 games | After 475 games | After 500 games |
|---|---|---|---|
| ![Episode 425](results/gifs/episode_0425.gif) | ![Episode 450](results/gifs/episode_0450.gif) | ![Episode 475](results/gifs/episode_0475.gif) | ![Episode 500](results/gifs/episode_0500.gif) |
| score 1260 | score 2240 | score 400 | score 460 |

| After 525 games | After 550 games | After 575 games | After 600 games |
|---|---|---|---|
| ![Episode 525](results/gifs/episode_0525.gif) | ![Episode 550](results/gifs/episode_0550.gif) | ![Episode 575](results/gifs/episode_0575.gif) | ![Episode 600](results/gifs/episode_0600.gif) |
| score 210 | score 690 | score 550 | score 800 |

| After 625 games | After 650 games | After 675 games | After 700 games |
|---|---|---|---|
| ![Episode 625](results/gifs/episode_0625.gif) | ![Episode 650](results/gifs/episode_0650.gif) | ![Episode 675](results/gifs/episode_0675.gif) | ![Episode 700](results/gifs/episode_0700.gif) |
| score 490 | score 450 | score 1620 | score 800 |

| After 725 games | After 750 games | After 775 games | After 800 games |
|---|---|---|---|
| ![Episode 725](results/gifs/episode_0725.gif) | ![Episode 750](results/gifs/episode_0750.gif) | ![Episode 775](results/gifs/episode_0775.gif) | ![Episode 800](results/gifs/episode_0800.gif) |
| score 400 | score 730 | score 710 | score 1190 |

| After 825 games | After 850 games | After 875 games | After 900 games |
|---|---|---|---|
| ![Episode 825](results/gifs/episode_0825.gif) | ![Episode 850](results/gifs/episode_0850.gif) | ![Episode 875](results/gifs/episode_0875.gif) | ![Episode 900](results/gifs/episode_0900.gif) |
| score 800 | score 550 | score 830 | score 630 |

| After 925 games | After 950 games | After 975 games | After 1000 games |
|---|---|---|---|
| ![Episode 925](results/gifs/episode_0925.gif) | ![Episode 950](results/gifs/episode_0950.gif) | ![Episode 975](results/gifs/episode_0975.gif) | ![Episode 1000](results/gifs/episode_1000.gif) |
| score 310 | score 890 | score 1060 | score 590 |

### Files

- [pacman_dqn.ipynb](pacman_dqn.ipynb) — executed notebook with all outputs
- [config.json](results/config.json) — settings, hardware, package versions
- [training.csv](results/training.csv) — one row per training game
- [training_summary.json](results/training_summary.json) — episodes, decisions, updates, time
- [comparison.json](results/comparison.json) — all ten evaluation scores
- Model checkpoints (`*.pt`) are kept locally in the run's ZIP, not in this repository.

<!-- evidence:end -->

## What I observed

**The mean went up, but mostly because of one game.** The trained agent averaged 808 against the untrained
network's 492 (+316). Game by game, it was better on seeds 101 and 303, worse on 202 and 404, and tied on 505.
The median is 490 for both. Leaving out seed 303, the trained agent averaged 415 on the other four games, against
535 for the untrained network. Five games is a small sample, and one strong game moves the mean a lot.

**Where the points came from.** I replayed both saved checkpoints on the five evaluation seeds with
[analyze.py](analyze.py). The replay reproduces all ten recorded scores exactly; the full table is in
[evaluation_breakdown.md](results/evaluation_breakdown.md).

- **Seed 303, the 2,380-point game.** The agent ate a power pellet, then three ghosts in a row (200, 400, 800), then a
  fruit (100), all within about 50 decisions, roughly three seconds of play. That burst is 1,510 of its 2,380 points.
  It is the only ghost or fruit reward in any of the five trained games, so it may be as much luck as skill.
  The burst happens about 25 seconds in, so the 20-second "best trained game" GIF ends just before it.
- **The other four trained games** scored only from pellets, the same as the untrained network.

**What it learned to do.** The untrained network pressed the same move, up-left, in 95–98% of its decisions. Its score
came from drifting in one direction, plus the 5% random moves. The trained agent plays differently: its most common
choice is no-op (27–79% of decisions), which lets Ms. Pac-Man keep moving in her current direction. It mixes that with
down-right and down-left turns. It learned to keep moving and turn at corners, eating pellets along corridors. That
helped on some games (seeds 101 and 303) and not on others.

**What it did not learn: staying away from ghosts.** Trained games lasted about as long as untrained ones
(473–972 decisions vs. 534–640), and the first life was lost at similar times (decisions 175–252 vs. 141–340).
Training games say the same thing: they averaged about 600 decisions early on and about 630 at the end. In the GIFs,
the best trained game has already lost a life within 20 seconds, and the untrained game's score stalls while it
wanders through a cleared corridor.

**Training curve.** Training scores rose during the first ~150 games, then stayed flat, between about 760 and 860 per
100 games, for the rest of the run. Loss rose from about 0.02 to a peak near 0.13 around game 400, then settled near
0.10. Loss went up while scores stayed flat. The larger loss mostly reflects the network predicting bigger future
rewards; it is not a measure of better play.

**Compared with my expectation.** The mean landed inside my 600–1,000 guess, but not for the reasons I gave. Lower
exploration did not make games longer. The improvement is concentrated in one game instead of spread across five.
The flat training curve after ~150 games looks more like my "forgetting" worry than the steady rise I hoped for.

## How the agent learns

- **Observations — what it sees.** Four consecutive game screens, each shrunk to 84 × 84 grayscale pixels.
  One screen shows where everything is; four in a row show which way Ms. Pac-Man and the ghosts are moving.
- **Actions — what it can do.** The 9 joystick moves: no-op, up, right, left, down, and the four diagonals.
  Each decision is held for four emulator frames.
- **Rewards — how it is scored.** The game's own points: 10 per pellet, 50 per power pellet, 200–1,600 for eating
  ghosts, and more for fruit. For learning, each reward is clipped to between −1 and +1, so a pellet and a ghost
  count the same. Every score reported here is the real, unclipped game score.
- **Learning.** A convolutional network predicts a value for each of the 9 moves: the future reward it expects.
  The agent stores past moves in a replay memory, samples 32 at a time, and nudges each prediction toward
  *reward + 0.99 × the best predicted value of the next screen*. A slower-changing copy of the network supplies that
  target, which keeps learning stable. During training, a fixed share of moves is random so the agent keeps trying new things.

## Limitation and next experiment

**Limitation: the agent never learned to avoid ghosts, and its learning stalled after about 150 games.** Survival did
not improve, so every game ends after roughly the same number of decisions, however well the agent collects pellets.
Three parts of this setup make ghosts hard to learn:

- **Short memory.** The replay memory holds only 5,000 decisions, about eight games. The agent mostly learns from its
  last few games and keeps relearning the same early-maze situations.
- **Clipped rewards.** Rewards are clipped to ±1 for learning, so eating a ghost (200–1,600 points) teaches no more
  than a 10-point pellet.
- **No penalty for dying.** Losing a life only costs the pellets the agent would have eaten later, a weak and delayed signal.

**Next experiment: change only exploration, from 0.10 to 0.20.** Keep 1,000 episodes and learning rate 0.0001.
I chose 0.10 expecting fewer random moves to mean longer games, and the results did not support that: trained games
were no longer than the untrained network's. Meanwhile the agent settled into a narrow habit (mostly no-op and
down-right). With a 5,000-decision memory filled by that habit, it rarely experiences what happens when it turns away
from a ghost. Doubling the random moves should put more varied situations into memory. If that run shows longer games
or later first deaths, too little exploration was holding the agent back. If it does not, the small replay memory is
the more likely bottleneck.

## Repository layout

| Path | What it is |
|---|---|
| `pacman_dqn.ipynb` | The executed notebook from the final run |
| `results/` | Evidence copied from the run: scores, training log, dashboard, GIFs, evaluation breakdown |
| `run.py` | Runs the notebook headless and saves outputs after every cell |
| `collect.py` | Copies a run into `results/` and writes the Results section of this README |
| `analyze.py` | Replays the saved agents on the evaluation seeds; writes `results/evaluation_breakdown.md` |
| `pacman_player.py` | The notebook's floating local gameplay player (unchanged from upstream) |
| `tests/verify_notebook.py` | Upstream 5-episode verification script (unchanged) |
| `UPSTREAM_README.md` | The original project README, for implementation details |
