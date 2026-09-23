# Essential · Multiple comparisons and the winner's curse

**Needed for:** *"try ten prompts, report the best"*, *"hold out a test set you touch once"* in
[chapter 15](../../README.md).

## Trying many things and keeping the best

```
   every variant has TRUE accuracy 0.7. N = 200 questions. 5000 repetitions.
    K variants tried  mean of reported best  inflation (points)
                   1                  0.701                 0.1
                   3                  0.727                 2.7
                  10                  0.749                 4.9
                  30                  0.765                 6.5
                 100                  0.779                 7.9
   the more you try, the better the 'winner' looks -- and none of them is better.
```

Ten variants that are all exactly 70% accurate. Score them all, report the best, and you report
about 75% — five points of improvement that does not exist. The more you try, the better the
winner looks, and every one of them is the same.

## The winner's curse

```
   winner's score on the data used to pick it: 0.749
   the same winner on a FRESH test set:          0.699   (back to the truth)
   selection and evaluation on the same data is the bug. hold out a set you touch once.
```

Re-test the winner on data it was not selected on and it falls back to the truth. The bug is
**selecting and evaluating on the same data**. The fix is a held-out set you touch once.

## False positives multiply

```
    tests    P(at least one false positive at 5%)  Bonferroni threshold
        1                                   0.050                0.0500
        5                                   0.226                0.0100
       10                                   0.401                0.0050
       20                                   0.642                0.0025
      100                                   0.994                0.0005
   run twenty ablations and one will 'pass' at 5% by chance. either divide the threshold by
   the number of tests (Bonferroni) or pre-register the one comparison you care about.
```

Run twenty ablations at a 5% significance threshold and one will pass by chance. Either divide the
threshold by the number of tests (Bonferroni), or decide the one comparison you care about
*before* looking.

## Why public benchmark numbers drift upward

```
   many labs, many checkpoints, many prompts, one leaderboard: the max of a great many noisy
   draws. it is why a fresh, private test set almost always lands below the public number.
```

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **multiple comparisons** | Running many tests and reading each as if it were the only one. |
| **winner's curse** | The best of many noisy measurements overstates the truth. |
| **selection bias** | Choosing based on the score you then report. |
| **held-out test set** | Data used once, for the final number, after all choices are made. |
| **validation set** | Data used for choosing — prompts, checkpoints, hyperparameters. Separate from test. |
| **Bonferroni correction** | Divide the significance threshold by the number of tests. |
| **pre-registration** | Deciding the comparison before seeing results. |
