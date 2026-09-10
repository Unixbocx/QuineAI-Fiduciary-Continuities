# 018-2026-09-09-leveraged-pair-scalp-methodology.md

## Before

Pair-play confidence lived in the code's own logic: underlying RSI bands
(40/60) gate the direction, the 2x/3x side executes it, quick-play scaling.
The approach was internally coherent but unvalidated externally, and carry no
explicit regime check — a "scalp the fall" signal fires whether the market is
choppy or in a strong trend.

## After

External research (scalping leveraged ETFs, 2x/3x edge theory) confirmed the
core design and added three decision filters that materially change *when the
signal is valid*:

1. **Wider RSI bands on leveraged sides (20/80)**, not 30/70 or 40/60.
   Standard thresholds whipsaw on 2x/3x — the side readings were being
   misread and stay widened in 027.
2. **ADX regime gate.** Mean reversion ("short the fall") fails in strong
   trends. ADX > 30 on the underlying kills the counter-side scalp; only
   trend-with-side confirmation counts. 027 computes ADX and gates on it.
3. **Rental doctrine.** Leveraged pairs are rentals (1-5 days), decay
   compounds. A deep-extended side gets an explicit "don't hold, decay is
   compounding" warning in 027's output.

## Produced by

Web research on leveraged ETF scalp methodology (mean-reversion edges, RSI on
2x/3x, ADX trend filter, pair decay), ran against the principal's actual
playbook.

## Implies

The pair lens (027_leverage_pair.py) now outputs regime + sides + decision
with the three filters wired in, verified on TSLA/TSLL/TSLS and NVDA/NVDL/NVDS.
Future pair work inherits: regime check first, wider bands on the ETF side,
rental warnings when extended.