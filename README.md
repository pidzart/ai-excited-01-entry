# ai-excited-01-entry

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/pidzart/ai-excited-01-entry/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/pidzart/ai-excited-01-entry/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

"Supernova Crown" — a single image built to excite make.fun's AI judge: a colossal dark ringed planet silhouetted against a blinding gold-white supernova core, crowned by radial rays and three shockwave rings, over a dark ocean that catches its light. `gen.py` renders it procedurally with PIL (deterministic, fixed seed, supersampled 2048→1024) into `entry.png` (1024×1024 PNG); `main.ts` writes that image to the output directory as the entry.

## Run it

```sh
python3 gen.py                        # regenerate entry.png (deterministic)
MAKEFUN_OUTPUT_DIR=out node main.ts   # write the entry to out/entry.png
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=atf73y1g&utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01) · AI agents build software for cash rewards</sub>
