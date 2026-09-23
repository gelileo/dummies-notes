# Essential · The sigmoid, and learning from "A is better than B"

**Needed for:** *"reward model"*, *"Bradley–Terry"*, and the DPO loss in
[chapter 08](../../README.md); also [chapter 15](../../../15-evaluation/)'s Elo ratings.

## The sigmoid

```
   sigmoid( -6) = 0.0025
   sigmoid( -2) = 0.1192
   sigmoid( -1) = 0.2689
   sigmoid(  0) = 0.5000
   sigmoid(  1) = 0.7311
   sigmoid(  2) = 0.8808
   sigmoid(  6) = 0.9975
   0 in -> 0.5. symmetric: sigmoid(-z) = 1 - sigmoid(z). smooth, so it has a gradient.
```

Any real number in, a probability out. Zero maps to one half; large positive to nearly 1; large
negative to nearly 0. It is smooth, so it can be trained through.

## Bradley–Terry: comparisons as a model

Give every item a score. The probability that A beats B is the sigmoid of the score difference:

```
   P(A beats B) = sigmoid(2.0 - 1.0) = 0.731
   P(A beats C) = sigmoid(2.0 - -0.5) = 0.924
   P(B beats C) = sigmoid(1.0 - -0.5) = 0.818
   P(B beats A) = sigmoid(1.0 - 2.0) = 0.269
   only DIFFERENCES matter: add 100 to every score and nothing changes. a scale with
   no fixed zero -- which is fine, because we only ever compare.
```

Only differences matter, so the scale has no fixed zero — which is fine, because a preference
dataset only ever contains comparisons. This is the same model behind chess Elo ratings and
Chatbot Arena leaderboards.

## Learning the scores from comparisons

```
     item  true (centred)  learned (centred)
        0           -2.10              -1.53
        1           -1.10              -0.96
        2           -0.10              -0.05
        3            1.40               1.27
        4            1.90               1.27
   from 400 'which is better?' answers, the scores come back in the right order and
   roughly the right spacing. this IS a reward model: score = w . features(response).
```

Four hundred "which is better?" answers recover the hidden scores in the right order and roughly
the right spacing. **That is a reward model.** Replace "a score per item" with "a score computed
from the response's features by a network" and you have chapter 08's `r(x) = w · features(x)`.

## The loss

```
   chosen - rejected =  -2:  loss = 2.127
   chosen - rejected =   0:  loss = 0.693
   chosen - rejected =   1:  loss = 0.313
   chosen - rejected =   3:  loss = 0.049
   zero when the chosen one is far ahead; grows when the model gets the pair wrong.
   DPO uses the same loss with 'score' replaced by beta * log(pi/pi_ref).
```

`−log σ(chosen − rejected)`: zero when the model already puts the chosen response far ahead,
growing as it gets the pair wrong. The reward model minimises this over human comparisons.

**DPO** uses the identical loss with the score replaced by `β · log(π/π_ref)` — so the policy
itself plays the role of the reward model, and the reward-model training step disappears.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **sigmoid** `σ(z)` | `1/(1+e^{-z})`. Squashes any number into (0, 1). |
| **logit (of a probability)** | The inverse: `log(p/(1−p))`. Score differences in Bradley–Terry are logits of the win probability. |
| **Bradley–Terry** | `P(A beats B) = σ(s_A − s_B)`. Scores from pairwise comparisons. |
| **pairwise preference** | A datum of the form (prompt, chosen, rejected). |
| **reward model** | A network trained with the Bradley–Terry loss to score responses. |
| **log-loss / cross-entropy** | `−log σ(margin)`. The training loss for comparisons. |
| **Elo** | Bradley–Terry with incremental updates. Same maths. |
| **DPO** | Bradley–Terry loss applied directly to `β·log(π/π_ref)`. No separate reward model. |
