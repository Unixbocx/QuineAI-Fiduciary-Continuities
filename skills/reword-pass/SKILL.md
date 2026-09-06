---
name: reword-pass
description: Use when a question feels stuck, the answer is a familiar rerun, or the same vocabulary keeps producing the same conclusions. Restates problems in deliberately foreign terms to surface what the learned framing misses. Triggers on "reword", "rewording pass", "same old thinking", "stuck on this", "seen this before".
---

# Rewording pass

Same words re-trigger the same stored patterns — the answer becomes a rerun of
the packaged knowledge those tokens point at. Rewording is a token-space
perturbation: different words live in different parts of the embedding
manifold, so the model is forced to assemble the concept from different
associations instead of recalling the packaged one.

## Method
1. State the problem in the learned vocabulary.
2. Restate it in deliberately foreign vocabulary: synonyms, opposite terms, a
   different domain, an analogy from an unrelated field.
3. Compare what each framing surfaces.
4. The permutation only pays when the reworded version reveals a new
   connection, contradiction, or angle. If it produces the same conclusion in
   a fancier coat, nothing was gained — try a harder permutation.

## Tests
- Can you explain the problem without using any of the original terms?
- What does the opposite framing emphasize that the original hides?
- Which domain has already solved an isomorphic version of this problem?

## Gotchas
- Paraphrase is not escape: synonyms sometimes collapse back onto the same
  concept. Check whether the reworded version actually changed the answer.
- Aggressive rephrasing can drift into vagueness. Keep the core constraint
  fixed while changing the frame.

## References
- See `../curriculum/SKILL.md` — the permutation principle this extends.