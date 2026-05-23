# PsychoTests

A TUI application with 9 psychological tests, rebuilt from original DOS programs (1990s).

## Tests

| Test | What it measures | Questions |
|------|-----------------|-----------|
| **Biorhythm** | Physical, emotional, intellectual cycles | Date-based |
| **Eysenck EPI** | Extraversion, Neuroticism, Lie scale | 57 Yes/No |
| **Stress** | Stress level | 24 × 1-5 |
| **Neiro** | Neuropsychological state | 24 × 1-5 |
| **Connect** | Interpersonal compatibility | 25 × 1-5 |
| **Economy** | Business orientation | 25 × 1-5 |
| **Heart** | Cardiovascular tendencies (6 scales) | 25 × 1-5 |
| **Selftest** | Self-esteem | 20 × 1-5 |
| **Luscher** | Color personality test | 8 colors × 2 rounds |

## Usage

```bash
pip install -r requirements.txt
python3 run.py
```

| Key | Action |
|-----|--------|
| `q` / `й` | Quit |
| `escape` | Back |
| `1`–`5` | Select answer |
| `enter` | Next question |
| `↑↓←→` | Navigate |

Features: user management, test history, Russian interface.

## Reverse Engineering

The original DOS programs were reverse-engineered to extract test logic, question banks, and interpretation texts. See [docs/analysis.md](docs/analysis.md) for the full report.

## License

GPLv3
