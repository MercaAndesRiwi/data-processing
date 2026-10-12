# Throughput F4 — modo peak (2026-10-12)

## Comando
```powershell
uv run python -m src.simulators.marketplace_events.producer --orders 300 --duplicate-rate 0.05 --ooo --out data/raw/events_smoke.jsonl
uv run pytest tests/unit/test_throughput.py -v
```

## Resultado medido (local, Python 3.13+, seed 42)
- 300 órdenes → 1184 eventos.
- Generación pura en memoria: ~13800 ev/s.
- Test `test_peak_throughput_reaches_20_eps` (300 órdenes): pasa, exige ≥ 20 ev/s.

## Lectura
El criterio pide ≥ 20 ev/s en peak. El productor no usa `sleep`: los
timestamps son lógicos y el throughput es cómputo puro, por eso supera el
umbral por ~3 órdenes de magnitud en local. En prod con sink Kafka el
cuello será red, no generación.

## Reproducibilidad
Mismo `seed` + mismos parámetros = mismos eventos. Cambiar `--orders`
escala el volumen sin tocar código.
