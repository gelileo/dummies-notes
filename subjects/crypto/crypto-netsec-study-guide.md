# Cryptography & Network Security — A Visual Study Guide (Tiers 0–6)

Each concept below comes with an example chosen to *draw a picture in your head*. If you can see it, you can remember it.

---

## Tier 0 — Mathematical Foundations

**Modular arithmetic**
Picture a 12-hour clock. It's 9 o'clock, you wait 5 hours — you don't land on "14," you land on **2**. The numbers wrap around the dial. That wrap-around is *modular arithmetic*, and almost every cipher lives on a clock face of some size (RSA's "clock" just has hundreds of digits on its rim).

**GCD and the Euclidean algorithm**
Imagine a tile floor that's 1071 cm by 462 cm, and you want to cover it with the **largest possible identical square tiles**, no gaps. You shave off the biggest square you can (462×462), look at the leftover strip, shave again, and repeat. The last square that fits perfectly is your answer. That shrinking-rectangle dance *is* the Euclidean algorithm — fast, ancient, and the engine behind finding inverses in RSA.

**Primes and primality testing**
A prime is a number of pebbles you simply **cannot arrange into a rectangle** — 7 pebbles will only ever form a 1×7 line, never a neat grid. Composites always make a grid (12 = 3×4). Testing huge numbers for primality (Miller–Rabin) is like interrogating witnesses: you ask a random number a clever question, and if the number "lies," it's exposed as composite. Pass enough witnesses and you trust it's prime.

**Modular exponentiation and discrete logarithms**
Think of paint. Mixing blue into yellow to get green is *instant and easy*. Now hand someone the green and ask "how much blue went in?" — they're stuck. Raising a number to a power on the clock face is the easy mixing; recovering the exponent (the discrete log) is the un-mixing nobody can do. This one-way gap is the whole reason public-key crypto works.

**Groups, rings, and finite fields (especially GF(2ⁿ))**
A Rubik's Cube is a group you can hold. Every twist is a move; there's a "do-nothing" move (the solved cube = identity); every twist has an "undo" (its inverse); and twists combine into new twists. AES does the same thing to bytes inside a special arithmetic world called GF(2⁸), where addition is just flipping bits (XOR) and there are exactly 256 "numbers." Same group rules, different playground.

**Probability, entropy, and information theory**
Entropy = "how surprised am I going to be?" A coin that *always* lands heads carries zero surprise — telling you the result tells you nothing. A fair coin carries one bit. Picture the game of 20 Questions: a good question splits the possibilities in half, and the number of yes/no splits you need to pin down the answer is its entropy. Passwords are strong exactly when they're *surprising*.

**Complexity and one-way functions**
Open an old paper phone book. Name → number is trivial (it's alphabetized). Number → name is a nightmare (you'd scan every page). A *one-way function* is that phone book: easy forward, brutal backward. Or picture dropping a wine glass — shattering is a second's work, reassembling is hopeless. Cryptography is built almost entirely out of actions that are cheap to do and impossibly expensive to undo.

---

## Tier 1 — Classical / Historical Cryptography

**Caesar and substitution ciphers**
Picture two alphabet rings, one inside the other, like a decoder ring from a cereal box. Twist the inner ring three notches and A points at D, B at E. That twist is the Caesar cipher. A full *substitution* cipher scrambles the inner ring randomly instead of just rotating it — 26 letters mapped to 26 others.

**Vigenère cipher**
Now imagine not one decoder ring but a whole *row of them*, each twisted by a different amount, and you rotate through them letter by letter according to a keyword. The same letter "E" in your message can come out as three different letters depending on which ring it lands on. For centuries this looked unbreakable — it hides the tell-tale fingerprint that sinks the simple ciphers.

**Frequency analysis**
Draw a bar chart of how often each letter appears in English: **E** is a skyscraper, T and A are tall, Q and Z are ankle-high. Now chart the letters in a Caesar-ciphered message — you get the *exact same skyline, just slid sideways*. Find the slid-over skyscraper, and you've found E. The cipher betrays itself through its shape.

**The one-time pad and perfect secrecy**
Imagine a key that is **as long as your message and perfectly random** — and used only once. Encrypting is laying that random key over your text like a randomly-colored transparency. The result is itself perfectly random noise: a ciphertext that could decrypt to "ATTACK AT DAWN" or "BRING ME CAKE" with equal plausibility. There's literally nothing to grip. This is the only cipher *proven* unbreakable — and it's a logistical nightmare, which is why we rarely use it.

**Kerckhoffs's principle**
Picture a glass-walled bank vault. Anyone can study the gears, hinges, and locking bolts in broad daylight — and it's still secure, because security lives in the *key*, not in hiding how the lock works. "Don't rely on the enemy not knowing your design" — a rule modern crypto takes as gospel.

**The Enigma machine**
Watch the rotors: each keypress lights up a different letter, and a rotor clicks forward like a car odometer, so pressing "A" five times in a row gives five *different* outputs. That clicking, ever-shifting wiring is what made Enigma fearsome — and the disciplined detective work that found patterns in it (helped by predictable German weather reports) is one of history's great cryptanalysis stories.

---

## Tier 2 — Symmetric-Key Cryptography

**Stream ciphers vs. block ciphers**
A *stream cipher* is a faucet: your message flows past and gets a drop of pseudo-random noise XORed into each bit as it passes. A *block cipher* is a kitchen — it grabs a fixed-size handful of data (say 16 bytes), thoroughly scrambles that whole block as a unit, then reaches for the next handful.

**Feistel networks**
Imagine kneading dough by folding it in half repeatedly. Split the data into a left and right half; scramble the right half and fold it into the left; swap; repeat. The elegant trick: because you only ever *fold* (XOR) and *swap*, you can run the exact same machine backwards to decrypt. DES is built this way.

**DES, 3DES, and why DES died**
DES used a 56-bit key — like a padlock with "only" 72 quadrillion combinations. That sounded huge in 1977 and is laughably small now; a determined attacker can try every key. 3DES was the duct-tape fix (run DES three times), buying time until a real replacement arrived.

**AES (Rijndael)**
Picture your data as a 4×4 grid of bytes — a tiny checkerboard. AES does four things to it, round after round: swap each square for another via a lookup table (SubBytes), shift the rows sideways (ShiftRows), blend each column into a smear (MixColumns), and stamp in part of the key (AddRoundKey). It's a Rubik's-Cube-style shuffle so thorough that the output looks like static.

**Modes of operation — and the ECB penguin**
This is the most famous picture in cryptography. Take an image of the Linux penguin "Tux." Encrypt it with **ECB mode** (each block scrambled independently) and... *you can still clearly see the penguin* — because identical patches of color encrypt to identical blocks, the outline survives. Switch to **CBC** or **CTR** mode (where each block is chained to or counted with the last) and the penguin dissolves into true noise. The lesson — *patterns leak unless you chain blocks together* — burns itself into your memory the moment you see it.

**ChaCha20**
A modern stream cipher built like a blender on a timer: it takes a key, a nonce, and a counter, whirls them through 20 rounds of additions, rotations, and XORs, and pours out a torrent of high-quality random-looking bytes to mix into your data. Fast even on phones with no special hardware — which is why your mobile HTTPS connections often use it.

**Padding and padding-oracle attacks**
Block ciphers need the last chunk filled out to full size — like packing peanuts topping off a shipping box. The danger: if a server reacts *differently* to "the padding looks wrong" versus "the padding's fine but the contents are off" — say, a slightly different error or a slower response — an attacker can poke it thousands of times and tease the secret out one byte at a time. A system that beeps differently for different mistakes is leaking.

---

## Tier 3 — Integrity, Hashing, and Authentication

**Cryptographic hash functions**
A hash is a fruit smoothie machine. Toss in *anything* — a one-line text or a 4 GB movie — and out comes a fixed-size "smoothie" (e.g., 256 bits) that acts as the file's fingerprint. You can never reconstruct the fruit from the smoothie, and any two different files should yield different smoothies.

**The avalanche effect**
Change a single comma in a 300-page novel and re-hash it: the fingerprint doesn't change a little — it changes **completely**, top to bottom, as if a different document entirely. One pebble triggers a whole landslide. That's how you can detect even the tiniest tampering.

**Collisions, and the death of MD5/SHA-1**
A *collision* is two genuinely different documents that share the same fingerprint — like two unrelated strangers with identical fingerprints. For MD5 and SHA-1, researchers learned to *manufacture* such pairs on purpose (famously: two PDFs with the same SHA-1 but different contents). That's catastrophic for signatures, and why those two are retired.

**Merkle–Damgård and length-extension**
Older hashes are built like an assembly line, swallowing the message one block at a time and carrying a running "state" forward. The flaw: an attacker who knows the final state can sometimes *keep adding to the conveyor belt* and produce a valid hash for `your-message + their-extra-stuff` without knowing your secret. SHA-3 uses a different "sponge" design that soaks up and squeezes out data, immune to this trick.

**MACs and HMAC**
Picture a wax seal pressed over the flap of a letter with a signet ring only you own. Anyone can see the letter wasn't opened; nobody can re-seal it convincingly. An HMAC is that seal for data — it proves *both* that the message is untampered *and* that it came from someone holding the shared secret.

**Authenticated encryption (AEAD)**
Combine the locked box (encryption) *and* the tamper-evident shrink-wrap (the seal) into one operation — that's AES-GCM or ChaCha20-Poly1305. Open it and the wrapper is intact → trust it. Wrapper broken → reject the whole thing, don't even read it. It closes the gap where attackers used to flip bits inside encrypted-but-unauthenticated data.

**Merkle trees**
Picture a tournament bracket, but instead of teams, the bottom row is the fingerprints of your data chunks. Each pair of fingerprints is hashed together to make a parent fingerprint, on up to a single champion at the top: the *root*. Change one data chunk at the bottom and the change ripples straight up to the root. This lets Git, Bitcoin, and BitTorrent verify enormous datasets by checking one tiny root value.

**Password hashing and salt**
Never store passwords as plain hashes — attackers precompute giant "rainbow table" dictionaries of common-password fingerprints. The fix: a **salt**, a unique random sprinkle added to each password before hashing, like seasoning every dish differently. Now two people who both chose "password123" get totally different stored fingerprints, and the attacker's giant prebuilt table is worthless. Argon2/bcrypt/scrypt also make each guess *deliberately slow*, like a vault door that takes a full second to open — fine for one login, agonizing for a billion guesses.

---

## Tier 4 — Public-Key (Asymmetric) Cryptography

**The key-distribution problem it solves**
With symmetric crypto, two people must somehow *already share a secret key* to talk securely — but how do you share that key over an insecure line in the first place? It's the chicken-and-egg trap public-key crypto cracks open: it lets total strangers establish a secret **in full public view**.

**Diffie–Hellman key exchange**
The paint analogy, and it's perfect. You and a friend agree publicly on a shared **yellow** base. Each of you secretly stirs in a private color (you add red, they add blue) and mails the resulting mixture across the open street where eavesdroppers watch. You each then stir in your *own* secret color again. Both of you arrive at the identical muddy brown — yet an eavesdropper holding both mailed mixtures cannot un-stir them to reach it. A shared secret, born in the open.

**RSA**
Imagine you mail out thousands of **open padlocks** with your name on them, keeping the only key at home. Anyone can put a message in a box, snap your padlock shut, and ship it — but only your home key opens it. That's RSA encryption. Run it the other way (you lock something only your key could have locked) and anyone can verify *you* sent it — that's an RSA signature.

**Elliptic-curve cryptography (ECC)**
Picture a billiards table shaped by a gently looping curve. Start at a point, "bounce" to a new point by a precise geometric rule, and do it some secret number of times. Telling someone the start and end points doesn't reveal *how many bounces* you took — and that hidden bounce-count is your private key. ECC gives the same security as RSA with far smaller keys, which is why phones and chat apps love it (Curve25519, Ed25519).

**Digital signatures and non-repudiation**
A signature anyone can *verify* but only you can *produce* — like handwriting that's instantly recognizable yet impossible to forge. Sign a contract digitally and you can't later claim "that wasn't me," because only your private key could have made that mark. That's *non-repudiation*.

**Public-key infrastructure (PKI) and certificates**
A passport solves a trust problem: you don't personally know me, but you trust the government that stamped my passport, so you trust my identity. A TLS **certificate** is a website's passport, signed by a **Certificate Authority** everyone's browser already trusts. Your browser checks the chain of signatures — site → CA → root — like an immigration officer checking the seal is authentic.

**Forward secrecy**
Imagine writing each day's conversation on a chalkboard, then *erasing it completely* every night and starting tomorrow with a fresh, unrelated key. If a burglar later steals your master key, yesterday's erased conversations are still safe — there's nothing left to decrypt. Modern TLS uses fresh per-session keys precisely so a future break-in can't unlock the past.

---

## Tier 5 — Protocols and Network Security

**The CIA triad**
Picture a vending machine. **Confidentiality** = the glass is one-way mirror, nobody sees what you bought. **Integrity** = tamper-evident wrapping, you know your snack wasn't swapped or poisoned. **Availability** = the machine is always plugged in and stocked. Every security decision is really about protecting one of these three; an attack is just knocking one over.

**Threat modeling**
Before locking your house you ask: *who* might break in, *how*, and *what* are they after? Threat modeling is that walk-around-the-house thinking applied to a system — naming the burglars before they arrive, instead of bolting doors at random.

**TLS / SSL and the handshake**
Two strangers meet in a crowded square and need to talk privately. First they check ID (the certificate). Then, in front of everyone, they perform a clever choreography (the key exchange) that leaves them both holding the same secret handshake nobody watching could copy. From then on they whisper in a code only the two of them know. TLS 1.3 streamlined this dance to be faster and dropped the old, breakable steps.

**The OSI / TCP-IP model**
Mailing a gift: you wrap it in tissue, put it in a box, slap on an address label, hand it to the courier, who loads it on a truck. Each layer wraps the one before without caring what's inside. Network data is nested the same way — your chat message sits inside an HTTP envelope, inside a TCP envelope, inside an IP envelope, inside an Ethernet frame. Attacks target specific layers, so knowing the stack tells you *where* a threat lives.

**Man-in-the-middle (MITM) attacks**
Picture a dishonest mail carrier who steams open every letter, reads it, maybe rewrites it, then reseals it so neither sender nor recipient suspects a thing. They sit *in the middle* of the conversation, impersonating each side to the other. Certificates and key exchange exist largely to make this carrier's reseal job impossible.

**ARP and DNS spoofing**
Imagine a prankster repainting the street signs in your town so "Bank Street" now points down an alley to a fake bank. ARP spoofing repaints the *local* signs (which machine is which on your network); DNS spoofing repaints the *address book* (which server `yourbank.com` resolves to). You think you're going to the right place; you've been quietly rerouted.

**VPNs and IPsec**
You need to cross hostile, bandit-filled territory carrying valuables. A VPN is an **armored tunnel** built through it: everything you send is sealed inside an encrypted pipe so the bandits (the open internet, your café's Wi-Fi) see only an opaque conduit, not the cargo inside.

**Firewalls, NAT, and IDS/IPS**
A firewall is a nightclub bouncer with a guest list, deciding which connections get in and which get turned away at the door. An **IDS** is the security camera that flags suspicious behavior inside; an **IPS** is the guard who actually tackles the troublemaker. NAT is the front desk that lets a whole building of rooms share one public street address.

**Web security — the OWASP Top 10**
The classic image is the xkcd cartoon: a mother names her son *"Robert'); DROP TABLE Students;--"* so that when the school types his name into a careless database query, the query itself executes a command and wipes the records. That's **SQL injection** — untrusted input smuggled in as commands. **XSS** is the same idea aimed at browsers (sneaking a malicious script onto a trusted page); **CSRF** tricks your logged-in browser into "signing a blank check" — firing off a real request to your bank while you thought you were clicking a cat video.

**Authentication systems — OAuth, JWT, Kerberos**
**OAuth** is a *valet key*: you hand a parking attendant a key that starts the car and nothing more — it won't open the trunk or glovebox. That's how "Log in with Google" lets an app see your name without ever touching your password. A **JWT** is a tamper-proof wristband at a festival: it proves you paid and which zones you can enter, and the gate staff can verify it instantly without phoning the box office — but only if the festival actually *checks the seal* (a classic JWT misuse is forgetting to).

**DNSSEC, HTTPS, HSTS, certificate transparency**
If DNS spoofing is repainting street signs, **DNSSEC** is *notarizing* every sign so a forged one is obvious. **HSTS** is a standing order to your browser: "only ever approach this site through the armored tunnel, never the open road." **Certificate transparency** is a public ledger where every passport (certificate) ever issued is logged in the open, so a forged one for your bank can be spotted and revoked.

---

## Tier 6 — Advanced & Modern Frontiers

**Zero-knowledge proofs**
Picture a ring-shaped cave with a magic door at the back that only opens for someone who knows the secret word. You want to prove you know it without *saying* it. So your friend waits at the entrance, you walk in and pick a side at random, and they shout which side they want you to come out of. If you really know the word you can always obey — door or no door. Do this twenty times and dumb luck is ruled out: you've *proven you know the secret while revealing absolutely nothing about it*. This is the magic behind private logins and zk-rollups.

**Homomorphic encryption**
A laboratory glovebox: the dangerous sample stays sealed inside, but a technician reaches in through built-in gloves and manipulates it without ever taking it out or touching it directly. Homomorphic encryption is that glovebox for data — a cloud server can add, multiply, even search *your encrypted data while it stays locked*, and hand back a sealed result that only you can open. Compute on a secret you never get to see.

**Secure multiparty computation (MPC)**
Two millionaires want to know who is richer — without either revealing their net worth. MPC is the protocol that pulls this off: several parties feed private inputs into a shared "machine" that announces *only the final answer* (who's richer, the average salary, the vote tally) and never leaks the individual parts. It's a group computing a joint result while each keeps their own cards face-down.

**Shamir's secret sharing**
Tear a treasure map into five pieces so that *any three* can redraw the whole map — but any two reveal nothing at all. The trick: the secret is a single hidden point on a curve, and each share is one dot on it. Two dots fit infinitely many curves (useless); three pin the curve down exactly. Split trust so no single guardian — and no single break-in — can expose or destroy the secret.

**The quantum threat and Shor's algorithm**
Modern public-key crypto leans on un-mixing being impossible — factoring huge numbers (RSA), un-stirring the discrete-log paint (Diffie–Hellman, ECC). A large enough quantum computer running *Shor's algorithm* is the machine that genuinely *can* un-stir the paint, collapsing those one-way gaps. It's the alarm clock ticking under nearly all of today's asymmetric crypto — not a threat yet, but the reason the next entry exists.

**Post-quantum cryptography (lattice-based)**
Hide your key as one specific point in a vast grid that stretches across *hundreds of dimensions*, then nudge it slightly off the grid lines. Finding the nearest grid point in that many dimensions is a needle-in-a-high-dimensional-haystack problem that stumps even quantum computers. The new NIST standards — **Kyber** for key exchange, **Dilithium** for signatures — are built on exactly this lattice hardness, the planned successors to RSA and ECC.

**Quantum key distribution (BB84)**
Send the key not as bits but as single photons, each tilted to a secret polarization. Quantum physics guarantees that *anyone who measures a photon disturbs it*. So an eavesdropper's very act of listening scrambles the stream — and when you and your partner compare a sample afterward, the errors expose them. Here secrecy is enforced by the laws of physics rather than the difficulty of a math problem.

**Blockchain: the primitives in concert**
This is where the whole guide composes. Hash-link each page of a ledger to the one before (change page 2 and every later fingerprint shatters — a tamper-evident chain). Make adding a page *deliberately expensive* by demanding the answer to a costly hash puzzle (proof-of-work, like requiring a winning lottery ticket just to write). Sign every entry (Tier 4). The result needs no trusted authority: integrity is guaranteed by hashing, signatures, and cost stacked together.

---

## How to use this guide

Pair each picture with one hands-on action: implement the Caesar cipher, watch a real ECB penguin appear in your own code, salt a password, snoop your own TLS handshake in Wireshark. The image makes you *remember* it; the keyboard makes you *understand* it.
