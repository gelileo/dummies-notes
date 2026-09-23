# Essential · The policy gradient

**Needed for:** *"REINFORCE"*, *"push up the log-probability of good responses"*, and everything
about PPO and GRPO in [chapters 08](../../README.md) and [09](../../../09-reasoning-training/).

## The objective

The policy is a probability distribution over responses; each response has a reward. We want to
change the policy's parameters to raise the **expected reward**:

```
   rewards  [1.  3.  0.5 2.  4. ]
   policy   [0.219 0.162 0.179 0.242 0.198]
   J(theta) = E_pi[reward] = 2.0706
```

## The gradient we want

Since this toy has only five responses, the exact gradient can be measured by nudging each
parameter ([derivatives](../../../04-optimization-loop/essentials/derivatives-and-gradients/)):

```
   dJ/dtheta = [-0.2343  0.1507 -0.2814 -0.0171  0.3821]
```

A real policy has a distribution over *every possible text*. You cannot enumerate it. So the
question is how to get this gradient without summing over all responses.

## The trick

```
   the gradient of an expectation becomes an expectation of a gradient -- which
   means it can be ESTIMATED FROM SAMPLES, without knowing pi in closed form.
   for softmax logits, grad log pi(k) = onehot(k) - pi.
   sum_k pi(k) * r(k) * grad log pi(k) = [-0.2343  0.1507 -0.2814 -0.0171  0.3821]   <- matches
```

**`∇ E[r] = E[ r · ∇ log π ]`.** The gradient of an expectation becomes an expectation of a
gradient — and an expectation can be *estimated from samples*. You do not need to know the
policy in closed form; you need to be able to sample from it and compute `∇ log π` of what you
sampled. For softmax logits that gradient is just `onehot(k) − π`.

This identity is the whole of policy-gradient reinforcement learning. Every method after it —
REINFORCE, PPO, GRPO — is a way of estimating that expectation with less noise.

## Estimating it from samples: REINFORCE

```
    samples                            estimate   error
          4[ 0.117  0.466 -0.314  0.077 -0.347]   0.874
         32[-0.271 -0.152 -0.281  0.119  0.585]   0.391
        256[-0.288  0.031 -0.303 -0.053  0.613]   0.269
       4096[-0.229  0.164 -0.28  -0.025  0.37 ]   0.020
   unbiased, converging with more samples. in RLHF each 'sample' is a full response
   the model generated and the reward model scored.
```

Sample responses, score them, weight each `∇ log π(response)` by its reward, average. Unbiased,
converging with more samples. In RLHF each "sample" is a full response the model generated and
the reward model scored.

## Baselines

```
   no baseline      mean error 0.0195   scatter 0.477
   baseline = E[r]  mean error 0.0052   scatter 0.224
   (reward - baseline) is the ADVANTAGE. it is why every RL method for LLMs -- PPO,
   GRPO -- centres rewards before using them.
```

`(reward − baseline)` is the **advantage**. Same expected gradient
([why](../expectation-and-sampling/)), half the scatter. PPO estimates the baseline with a
learned value network; GRPO uses the mean reward of a group of samples for the same prompt.

## One step

```
   J before 2.0706   J after one step 2.2250   policy now [0.194 0.174 0.155 0.239 0.239]
   mass moved toward the high-reward responses. repeat, and the policy converges on r4.
```

Add the gradient (we are *maximising*), and probability mass moves toward the high-reward
responses. Chapter 08 does this for 300 steps and watches what the policy converges on — and what
it exploits.

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **policy** `π` | The model, seen as a distribution over responses. Its parameters are what we train. |
| **reward** `r` | A number scoring a response. From a reward model (08) or a checker (09). |
| **expected reward** `J` | `E_π[r]`. The objective. |
| **policy gradient** | `∇J = E_π[r · ∇ log π]`. Lets the gradient be estimated by sampling. |
| **score function** `∇ log π` | For softmax logits: `onehot(chosen) − π`. |
| **REINFORCE** | Estimate the policy gradient by sampling; step along it. |
| **advantage** | `r − baseline`. Same expectation as `r`, less variance. |
| **PPO** | Policy gradient with a learned baseline and a cap on how far the policy moves per update. |
| **GRPO** | Policy gradient with the group's mean reward as baseline. No value network. |
