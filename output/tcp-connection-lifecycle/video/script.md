# TCP connection lifecycle — narration script

## TCP connection lifecycle

This is tcp connection lifecycle. The full set of steps two computers go through to talk reliably over a network: they first greet each other to agree to start, then send messages back and forth while confirming each one arrived, and finally say goodbye to close the conversation cleanly.

## Unreliable delivery

Next: unreliable delivery. The fact that a message sent across a network can quietly fail to arrive, arrive damaged, or arrive out of order, with no automatic warning to the sender.

Here is what the sender does. It hands four messages to the network, numbered one through four, in order. As far as the sender is concerned, the job is done. The messages are on their way. What the sender cannot see is the network in the middle: a long chain of cables and machines it does not control.

Now follow the messages into the network. This is where things quietly go wrong. One message simply gets dropped and never comes out. Another gets a few bits flipped along the way, arriving damaged. A third overtakes the message ahead of it, so they fall out of order. None of this is announced. The wires do not call home.

Here is what actually shows up at the other end. Message one arrives perfectly. Message four arrives next, before message three, so the order is scrambled. Message three arrives, but damaged. And message two? It never comes. Meanwhile the sender still believes everything went fine. It was never told otherwise.

So this is unreliable delivery in one picture. A message can vanish. It can arrive corrupted. It can arrive out of order. And the thread tying all three together is silence: the network makes no promise, and sends no warning back. If you want reliability, you have to build it yourself, on top, by numbering messages, checking them, and asking for the missing ones again. For the wires-and-machines layer underneath this, see the computer-network figure; for what one of these numbered messages actually is, see the data-packets figure.

## Delivery acknowledgement

Next: delivery acknowledgement. A short reply one computer sends back to confirm it received what the other sent, so the sender knows the message arrived and does not have to guess or resend it blindly.

A computer sends a packet across the link. Call it packet five. But sending is not the same as arriving. The link can drop things. So the sender does something smart. It keeps its own copy of packet five. If anything goes wrong, it can send it again. For now, it waits to hear back. Go deeper: for what a numbered packet is and why it carries a number, see the data-packets figure.

The packet crosses the link and lands at the receiver. The receiver now has packet five. But here is the catch. The sender is far away. It has no window into the receiver. From where the sender sits, this moment looks exactly like a packet that got lost. It cannot tell the difference. It still does not know.

So the receiver speaks up. It sends back a tiny reply. Just a few bytes that say: I got number five. This little reply is the acknowledgement. When it reaches the sender, the guessing ends. The sender now knows for certain the packet arrived. It can safely throw away its kept copy. The job is done.

Now watch what an acknowledgement protects against. The sender sends packet six. But this time the link drops it. It never reaches the receiver. And because the receiver never saw it, it sends back nothing. No ack arrives. The sender keeps waiting. The silence is the signal: something went wrong. Go deeper: for why links drop packets in the first place, see the unreliable-delivery figure.

Because the sender kept its copy, it can simply send packet six again. This time it gets through. The receiver stores it and replies: got number six. The ack makes it back. Delivery is confirmed. That is the whole idea. A short reply turns a hopeful send into a sure one — no blind guessing, no needless resending.

## TCP connection lifecycle

Next: tcp connection lifecycle. The full set of steps two computers go through to talk reliably over a network: they first greet each other to agree to start, then send messages back and forth while confirming each one arrived, and finally say goodbye to close the conversation cleanly.

Two computers want to talk. Before sending anything important, they greet each other. Computer one calls out: can we talk? Computer two answers: yes, I'm ready. Computer one confirms: great, starting. That back-and-forth-and-back is the handshake. Now both sides know the other is listening.

The connection is open, so now the real talking begins. Computer one sends a packet of data. Computer two sends back a short note: got it. Then the next packet, and another got it. Each piece is confirmed before it counts as delivered. That is how both sides stay sure nothing slipped through.

Networks lose things. Here packet three sets off and simply vanishes. Computer two never saw it, so it sends no confirmation. Computer one waits, hears nothing, and takes the hint. It sends packet three again. This time the confirmation comes back. A missing got-it always means try again, so nothing is ever quietly dropped.

The talking is finished, so the two computers wind down politely. Computer one says: I'm done. Computer two answers: heard you. Then Computer two says: I'm done too. And Computer one replies: goodbye. Each side announces it is finished and waits for the other to agree. Nobody hangs up mid-sentence.

Step back and the whole shape is simple. First they greet, to agree to start. Then they talk, sending data and confirming each piece arrived. Then they say goodbye, closing the line cleanly on both ends. Greet, talk, goodbye — that is the life of a reliable connection from hello to hang-up. To go deeper: the data sent in the talk phase travels as numbered packets — see the data-packets figure. The greeting rules both sides follow are a shared agreement — see the communication-protocol figure. And the got-it confirmations are covered by the delivery-acknowledgement figure.

## Recap

That is tcp connection lifecycle, built up one idea at a time.
