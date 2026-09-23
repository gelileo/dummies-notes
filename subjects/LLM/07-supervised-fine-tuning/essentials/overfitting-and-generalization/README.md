# Essential · Overfitting and generalization

**Needed for:** *"few epochs, low learning rate, stop early"*, *"held-out loss"* and
*"catastrophic forgetting"* in [chapter 07](../../README.md) — and the train/validation
distinction everywhere after.

## The same data, models of growing capacity

Twenty noisy points from `y = sin(x)`. Fit polynomials of increasing degree, and measure the
error on those twenty points *and* on twenty more the fit never saw:

```
   20 training points from y = sin(x) + noise; 20 held-out points from the same rule
     degree  params  train error  held-out error
          1       2       0.2148          0.1749
          2       3       0.2140          0.1753
          3       4       0.0298          0.0391
          5       6       0.0127          0.0448   <- best held-out
          8       9       0.0117          0.0495
         12      13       0.0052          0.1204
         19      20       0.0000    9771682.1934   <- fits every point exactly
   train error only ever falls. held-out error falls, then RISES. degree 19 hits
   every training point and is useless -- it memorised the noise.
```

**Training error only ever falls.** More capacity fits the given points better, always. The
held-out error falls *and then rises*: past a certain point the model is fitting the noise in
the training set, and noise does not repeat. Degree 19 passes through every training point
exactly and is catastrophically wrong everywhere else. It has **memorised**, not learned.

## The same curve over time

Capacity is one axis; training time is another. Hold the model fixed and train longer:

```
      step     train  held-out
         1    0.5071    0.4303
        10    0.3937    0.3256
       100    0.2148    0.1718
       500    0.0786    0.0732
      2000    0.0459    0.0695
      5000    0.0268    0.0513
     10000    0.0173    0.0412
     20000    0.0147    0.0390
   held-out was best around step 20000. training longer only helps the train number.
   'early stopping' means: watch the held-out loss and stop when it turns.
```

Held-out loss bottoms out and turns back up while training loss keeps improving. **Early
stopping** is the practice of watching the held-out number and stopping when it turns — the
single most reliable regulariser there is.

## Why this bites fine-tuning harder than pretraining

Pretraining sees trillions of tokens roughly once; there is not enough repetition to memorise.
Fine-tuning sees a few thousand examples for several epochs. That is exactly the regime above:
small data, many passes, a model with far more capacity than the task. Chapter 07's measured run
shows it — train loss to zero, held-out loss rising after step 100.

**Catastrophic forgetting** is the same phenomenon from the other side. The model fits the new
examples so well that it drifts away from everything it knew before; the pretraining loss is a
held-out set it is quietly failing.

## The vocabulary

```
   train loss      : how well you fit what you were shown. always improvable.
   held-out loss   : how well you do on what you were not shown. the honest number.
   generalization  : held-out performance. the thing you actually want.
   overfitting     : train keeps improving while held-out gets worse. memorising.
   the gap between the two curves is the size of the problem.
```

## Run it

```bash
python3 demo.py
```

## Terms

| Term | Meaning |
| --- | --- |
| **training set** | The examples the model is fit to. |
| **held-out / validation set** | Examples kept aside, never trained on, used only to measure. |
| **training loss** | Error on the training set. Always improvable; not the goal. |
| **held-out loss** | Error on data the model did not see. The honest number. |
| **generalization** | Doing well on held-out data. What you actually want. |
| **overfitting** | Training loss falling while held-out loss rises. Fitting noise. |
| **memorisation** | The extreme: reproducing training examples rather than the rule behind them. |
| **early stopping** | Stop when held-out loss turns upward. |
| **regularisation** | Anything that trades training fit for held-out performance: decay, dropout, early stopping, replay. |
| **catastrophic forgetting** | A fine-tune drifting away from pretrained knowledge — overfitting seen from the base model's side. |
