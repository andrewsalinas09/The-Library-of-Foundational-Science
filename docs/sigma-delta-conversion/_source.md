---
uid: qr8n3v52
title: Precision from Nothing
subtitle: How a communications pin, two resistors, and a capacitor replace a precision instrument
domain: electronics / data conversion
assumes: nothing
mechanisms:
  - delta-sigma-modulation
  - decimation-filtering
ideas:
  - oversampling
  - noise-shaping
  - quantization-as-noise
  - dither
  - root-n-averaging
  - feedback-integrator
  - precision-from-history
  - comparison-vs-absolute
  - precision-in-procedure-not-instrument
analogy: >-
  Weighing a fish on a balance scale that reports only which pan is heavier,
  one metronome tick at a time.
claim: >-
  A one-cent capacitor, two resistors, and an idle communications pin deliver
  twelve-bit conversion with zero converter chips on the board.
status: published
created: 2026-08-14
---

## Preface: the claim we are going to earn

Inside a \$499 phased-array radio called the QuadRF, there is a place on the circuit board where a smooth, wiggling analog voltage carrying radio information needs to be turned into a stream of numbers a computer can process. The standard way to do this is to buy a chip called an analog-to-digital converter. A good one, fast enough and accurate enough for radio work, costs several dollars, and this product needs sixteen of them. That is a meaningful slice of the entire budget.

The QuadRF's designers did not buy those chips. Instead, at each of those sixteen places, the schematic shows a resistor, a second resistor, a capacitor worth about one cent, and a wire running into a pin on a logic chip, a pin that was designed for receiving digital communications and was never intended to measure anything. Out of that pin, through pure mathematics running inside the chip, comes a precision measurement, updated tens of millions of times per second, with quality comparable to the dedicated chip they didn't buy.

This document explains, completely and from zero, how that is possible. Not the hand-wavy version. The real version, with every load-bearing concept built up from scratch: what voltage actually is, what a capacitor actually does, why measuring precisely is expensive, why a yes/no question is cheap, and how a feedback loop running very fast transmutes millions of crude yes/no answers into one exquisite number. By the end, you will understand not just this circuit but a design philosophy: **precision can be moved out of hardware, where it costs money, into time and mathematics, where it is nearly free.**

No prior knowledge is assumed. If you already know some of this, skim; the load-bearing sections are marked. But the promise of the document is that someone who has never heard the word "capacitor" can follow every step.

---

# Part I: The Raw Materials

## 1. Electric charge, the substance of the story

Everything in this story is ultimately about pushing around a physical substance called electric charge. Matter is made of atoms; atoms contain electrons; electrons carry charge. In a metal like copper, some electrons are not attached to any particular atom. They drift freely through the material like a gas trapped inside the metal. A copper wire is, for our purposes, a pipe full of a fluid made of electrons.

Charge is measured in coulombs. One coulomb is about six billion billion electrons. You never need to picture individual electrons; picture a fluid. The fluid is already inside every wire, everywhere, all the time. Nothing needs to be "filled up" with electricity. What circuits do is *push* the fluid that is already there.

## 2. Voltage: the pressure

If charge is a fluid, voltage is the pressure applied to it.

More precisely, voltage is a measure of how much energy it would take to move a unit of charge from one point to another, but the pressure picture is faithful enough to carry us the whole way. Two points in a circuit can be at different "pressures," and if a conductive path connects them, charge flows from the higher pressure point toward the lower one, exactly as water flows from a high tank to a low one through a connecting pipe.

Three facts about voltage matter enormously:

**Voltage is always a comparison between two points.** Saying "this wire is at 3 volts" secretly means "3 volts higher than some agreed reference point." Circuits designate one node as the reference and call it *ground*, defined as 0 volts. Every other voltage in the circuit is measured relative to it. This seems like bookkeeping trivia. It is not. The entire trick this document explains hinges on a device that compares two voltages against each other, and the reason that device is cheap while absolute measurement is expensive traces directly back to this fact: comparison is the natural, easy operation; absolute measurement is the contrived, hard one.

**Voltage can vary in time.** A battery holds a steady 1.5 volts between its terminals. But nothing says voltage must be steady. The voltage at a point can rise and fall, wiggle, oscillate, dance. A microphone converts sound pressure waves into a voltage that wiggles in the same pattern as the sound. A radio receiver converts electromagnetic waves into a voltage that wiggles in the pattern of the transmitted signal. A *time-varying voltage is the universal currency of information* in electronics.

**Voltage is continuous.** Between 0.3 volts and 0.4 volts lie 0.31, 0.317, 0.3174, and infinitely many more values. A real physical voltage is a smooth quantity, like a position or a temperature, not like a count of apples. This smoothness is the root of the whole problem we are going to solve, because computers cannot digest smooth quantities.

## 3. Current: the flow

Current is the rate at which charge flows past a point, measured in amperes (one ampere is one coulomb per second). In the plumbing picture, voltage is pressure and current is flow rate, liters per second through the pipe. Apply pressure across a pipe and flow results; how much flow depends on how much the pipe resists.

## 4. Resistance and the resistor: the calibrated bottleneck

Every material resists the flow of charge to some degree. Copper resists very little; rubber resists almost completely. A **resistor** is a small manufactured component, the most common electronic part on Earth, deliberately built to resist by a precise, known amount. It is a calibrated narrow section of pipe.

The relationship between the three quantities is the single most used equation in electronics, Ohm's law:

**current = voltage ÷ resistance**, or $I = V/R$.

Resistance is measured in ohms (Ω). Push 1 volt across a 1,000-ohm resistor and exactly 1 milliamp flows. Double the voltage, double the flow. Double the resistance, halve the flow. That is essentially everything a resistor does, and it is enough: a resistor converts a voltage difference into a proportional, predictable current. Remember that phrasing. In the circuit we are building toward, resistors are used precisely as *voltage-to-current converters*, devices that translate "how much pressure" into "how much flow."

Resistors cost a fraction of a cent. The two resistors in our story are 2,200 ohms (written 2.2 kΩ) and they will play the role of translating voltages into gentle, well-defined trickles of charge.

## 5. The capacitor: memory made of two metal plates

Now the component the whole trick pivots on.

A **capacitor** is two flat metal plates placed very close together but not touching, with an insulating gap between them (air, plastic, ceramic). Charge cannot cross the gap. But here is what happens when you connect a capacitor into a circuit and push current toward it: electrons pile up on one plate and are pushed away from the other. Charge *accumulates* on the plates even though nothing crosses the gap.

The accumulated charge creates a voltage across the capacitor, and the relationship is beautifully simple: the voltage is proportional to the stored charge. The proportionality constant is called capacitance, measured in farads:

**voltage across capacitor = stored charge ÷ capacitance**, or $V = Q/C$.

The intuition to carry: **a capacitor is a bucket for charge, and the voltage across it is the water level in the bucket.** Pour current in, the level rises. Draw current out, the level falls. Stop all flow, and the level *holds*: the capacitor remembers.

This memory property deserves to be stated with full force, because it is the mathematical heart of everything that follows. The water level in a bucket, at this exact instant, equals the total of all water ever poured in, minus all water ever removed, over the bucket's entire history. The bucket performs a running sum of its own inputs. In mathematics, a running sum over continuous time is called an *integral*, and so engineers say a capacitor *integrates* current. You do not need the calculus; you need the bucket: **the capacitor's voltage is the accumulated history of every current that ever flowed into or out of it.**

One more behavior to note. Connect a voltage source through a resistor to a capacitor, and the capacitor charges gradually: fast at first (big pressure difference, big flow), then slower as its own level rises to meet the source (small difference, small flow). The characteristic timescale of this settling is simply resistance times capacitance, R × C, called the time constant. A 2,200-ohm resistor feeding a 3.3-picofarad capacitor (pico means trillionth, so 3.3 trillionths of a farad, a genuinely tiny bucket) has a time constant of about 7 *nanoseconds*, seven billionths of a second. Hold that number loosely in mind: the bucket in our circuit is tiny and its level can swing meaningfully in a few billionths of a second. That is not sloppy design. The whole scheme depends on a bucket small enough and fast enough to respond within a single tick of a very fast clock.

Capacitors of this size cost about one cent.

## 6. What a signal is, and where ours comes from

A **signal**, throughout this document, means a voltage that varies in time in a pattern that carries information. Draw time along the horizontal axis and voltage on the vertical, and a signal is a curve: smooth, continuous, wiggling.

Two properties describe a wiggle. **Amplitude** is how far the voltage swings, the height of the wiggles. **Frequency** is how many complete wiggle cycles happen per second, measured in hertz (Hz). Audio signals wiggle between roughly 20 and 20,000 times per second. The signal in our story wiggles much faster, up to about 20 million times per second (20 MHz), because it carries radio information.

Where does it come from? The QuadRF's antennas receive WiFi-band radio waves oscillating around 5 billion times per second, far too fast for anything downstream to digest directly. A dedicated radio chip (a Maxim MAX2851, a part designed for WiFi equipment) performs an operation called downconversion: it strips away the 5-billion-per-second carrier oscillation and outputs just the *information* riding on it, now wiggling at a leisurely few tens of MHz. Think of the carrier as a truck and the information as the cargo; the radio chip unloads the truck. What emerges from that chip, on a set of output pins, is our protagonist: a smooth analog voltage, swinging over a range of about a volt, wiggling up to ~20 million times per second, containing everything the antenna heard.

(A detail for completeness: each antenna actually produces *two* such signals, called I and Q, which together encode both the strength and the timing alignment of the radio wave. This is why four antennas need sixteen converters once you count both directions, receive and transmit: 4 antennas × 2 signals × 2 directions. Nothing else in this document depends on what I and Q mean.)

## 7. The wall: computers cannot eat curves

A computer, including the FPGA logic chip at the center of this board, manipulates only discrete symbols: numbers, represented as bits. It cannot store, examine, or compute with a smooth curve. Before any mathematics can be done on the antenna's signal (filtering, combining antennas into beams, decoding messages), the smooth voltage must be converted into a **list of numbers**.

This conversion is called analog-to-digital conversion, and the device that performs it is an ADC. Conceptually an ADC does two separable things:

**Sampling** answers *when* to measure. Instead of the whole continuous curve, keep only its value at regular instants: tick, tick, tick, millions of times per second. A deep theorem (the Nyquist-Shannon sampling theorem) makes this respectable: if you sample at least twice as fast as the fastest wiggle in the signal, the samples contain *everything*; the smooth curve can be perfectly rebuilt from them, with no information lost whatsoever. Intuition: a wiggle can't hide between your samples unless it completes its up-and-down faster than two of your ticks. Our signal wiggles at up to 20 MHz, so any sampling rate comfortably above 40 million samples per second captures it fully. Remember this threshold; the trick we are building will sample not just above it but *hundreds of times* above it, and that extravagance is precisely where the magic comes from.

**Quantization** answers *how finely* to measure. Each sampled voltage must be rounded to the nearest value on a finite menu. The menu size is described in bits: an 8-bit ADC has $2^{8}$ = 256 menu levels; a 12-bit ADC has 4,096; a 16-bit ADC has 65,536. More bits, finer rounding, more faithful numbers. The rounding error, the small difference between the true smooth value and the nearest menu step, is called **quantization error**, and it behaves like a small amount of added noise, a fine gravel of inaccuracy sprinkled over the measurement. Keep this concept warm; the entire cleverness ahead consists of doing something unreasonable-sounding to this error.

## 8. Why fine measurement is expensive

Here is the economic heart of the problem. Sampling fast is cheap; modern transistors switch billions of times per second without complaint. Quantizing *finely* is what costs money, and it is worth understanding exactly why, because the trick's entire value lies in refusing to pay this specific cost.

A conventional fast ADC works, at bottom, by comparing the input against a ladder of internal reference levels, like measuring with a ruler by seeing which tick marks the value falls between. A 12-bit converter needs its 4,096 levels to be *correctly positioned* to within a fraction of one step, or the readings lie. Those levels are manufactured from physical components on the chip (matched resistors, matched capacitors, matched transistors), and physics fights you at every step: manufacturing spread makes nominally identical components differ slightly; temperature changes shift values; components age. Each additional bit *doubles* the required positional accuracy of every rung on the ladder. Precision analog design is the art of coaxing matched behavior out of unmatched physical objects, and it is genuinely hard, which is why an ADC combining high speed with high resolution is a premium product. A converter suitable for this radio (say 12 bits at 100+ million samples per second) runs several dollars per channel, and dedicated chips also burn board area and power, and demand delicate routing of their reference voltages.

Multiply by sixteen channels and the converters threaten to cost more than the FPGA that does all the actual thinking. This is the bill the QuadRF designers refused to pay.

## 9. The comparator: the cheapest measurement in the universe

Now go to the opposite extreme of the measurement spectrum. Strip away the ladder, the menu, all 4,096 rungs, and ask: what is the *simplest possible* measurement device?

It is a circuit that answers one question: **"Is voltage A higher than voltage B?"** Output: yes or no. One bit. This device is called a **comparator**, and it is nearly free, for a reason that connects back to the nature of voltage itself: comparison of two voltages is the operation electronics does *natively*. A comparator is just a few transistors arranged so that whichever input is higher wins a tug-of-war and slams the output to its side. It needs no calibrated internal levels, no matched ladder, no ruler at all. It only ever has to be *directionally* correct, and it can be blisteringly fast precisely because it carries no precision burden: deciding "left or right?" is easier than reporting "exactly where," and easier things can be done faster.

Notice what a strange pair of extremes we now hold. The precision ADC: expensive, complex, gives you a full number each tick. The comparator: nearly free, trivially simple, gives you a single bit each tick. The gap between them looks unbridgeable; one bit is a pathetic quantity of information. The rest of this document is the bridge.

## 10. LVDS: the precision comparator you already own

One more piece completes the parts list, and it is the observation that gives the trick its punchline.

Modern chips exchange data at enormous speeds, and at those speeds, the naive method (wiggle one wire between 0 volts and 3 volts, big swings meaning 0s and 1s) fails: large fast swings waste power, radiate interference, and get corrupted by noise. The industry's solution is **differential signaling**, and its most widespread standard is called **LVDS** (Low-Voltage Differential Signaling). To send one bit, use *two* wires, and encode the bit not in either wire's absolute voltage but in *which wire is slightly higher*. Wire A a few hundred millivolts above wire B: that's a 1. Wire B above wire A: that's a 0. Any noise that strikes the pair tends to strike both wires equally and cancels out of the comparison, which is why the swings can be tiny and the speeds enormous: an LVDS link comfortably carries close to a billion bits per second.

Now look at what the *receiving* pin of an LVDS link must contain. Its entire job is to look at two wires and decide which is higher, hundreds of millions of times per second, reliably, on tiny voltage differences.

**That is a comparator.** A fast, sensitive, mass-produced, thoroughly debugged comparator. It is not marketed as a measuring instrument; it is marketed as a communications port. But physically, electrically, functionally, every LVDS input pin on every FPGA is a high-performance comparator, already paid for, sitting idle in their dozens on the chip's perimeter.

The FPGA on the QuadRF board is a Lattice ECP5, a mid-range programmable logic chip. "Programmable logic" means the chip is a sea of generic logic elements whose interconnections are configured by a file (the "bitstream") loaded at power-up; the same physical chip can become a video processor or a network switch or, as here, the entire digital brain of a radio. Its pins can be configured in software as LVDS inputs. The QuadRF designers looked at those pins and saw not communication ports but sixteen free comparators.

The question the rest of this document answers: how do you point a yes/no question at a smooth voltage and extract a 12-bit answer?

---

# Part II: The Bridge from One Bit to Many

## 11. Why the naive approach fails, and what the failure teaches

Start with the obvious idea and watch it break, because the way it breaks points directly at the fix.

Suppose the signal sits at 0.63 on a scale where the comparator's threshold is 0.5. Ask the comparator once: "above 0.5?" Answer: yes. Ask again a nanosecond later: yes. Ask a million times: a million identical yeses. You have learned that the signal is somewhere above 0.5, and *nothing more*. A million answers, one answer's worth of information.

The diagnosis is precise: **repetition of the same question extracts no new information.** Each answer is only worth something if the question has changed since last time, if the comparison is aimed at whatever remains *unknown*. So the fix must be a mechanism that automatically re-aims every comparison at the current residual error, the part of the signal not yet accounted for by previous answers. That requires two capabilities: the system must *remember* the running consequence of its past answers, and the answers must *feed back* to influence what gets compared next.

Memory: we have that. It is the capacitor, the bucket whose level is the accumulated history of its inputs.

Feedback: a concept worth thirty seconds of respect on its own. Feedback means routing a system's output back to its input so the system reacts to its own behavior. Your home thermostat is a one-bit feedback loop: a comparator (too cold / not too cold) drives an actuator (furnace on/off) whose effect (heat) feeds back to the quantity being compared (room temperature). The room never sits exactly at the setpoint; it perpetually drifts slightly and gets corrected, drifts and gets corrected. And notice something suggestive: if you logged only the furnace's on/off record all day, the *fraction of time spent on* would trace out the house's heat demand, a smooth, information-rich curve, recovered entirely from a one-bit history. Hold that thought; it is the whole trick in domestic disguise.

## 12. The balance-scale story: the complete mechanism, no electronics

Here is the entire invention as a physical story. Every element of the real circuit has an exact counterpart here, and when the circuit appears in the next section it will simply be this story transcribed into parts.

You must weigh a fish to high precision. Your only instrument is a balance scale that reports one bit: *left pan heavier, or right pan heavier*. You also have an unlimited supply of identical standard weights, and a metronome ticking fast.

Place the fish on the left pan. Now play the following game, one move per metronome tick, forever:

**If the scale tips left (fish side heavy): add one standard weight to the right pan. If the scale tips right: remove one standard weight from the right pan.** Write down every move: "+" for add, "−" for remove.

Watch what happens. At first the fish dominates and you add, add, add. Eventually the standard weights overtake the fish and the scale tips right, so you remove one; the fish wins again, you add; and the system settles into a perpetual limp around the balance point, the pans forever trading tiny victories. The scale never rests. It is not supposed to. The dance *is* the measurement.

Because here is the ledger: suppose the fish weighs 723 grams and your standards are 1 gram each. After the brief opening ramp, the right pan hovers between 722, 723, and 724 grams, and your move record shows adds and removes in exactly the proportion needed to keep it hovering there. Over any stretch of, say, 1,000 ticks, the *net* count of your moves reveals the target: the running tally of the pan's contents averages to 723. Extend the window to 10,000 ticks and the average sharpens further. **The precision was never in the scale, which only ever said "left or right." The precision emerged from the accumulated record of corrections.** Each individual answer was crude, but each was aimed at the current residual error, so each carried fresh information, and arithmetic over the record concentrated all of it into one fine number.

Note the three roles, because they map one-to-one onto components: the *pans' state* (which side is winning, and by how much) is the memory; the *scale's tip direction* is the comparator; the *rule connecting tip direction to your next move* is the feedback. And note the fourth, silent ingredient: the *metronome*, running much faster than the fish's weight changes. If someone slowly pours water into the fish's mouth mid-game, the move record will faithfully track the rising weight, provided the ticks come far faster than the pour. Speed is what buys the right to average.

## 13. The circuit: the story transcribed into two resistors, one capacitor, one pin

Now build it. Here is the complete parts list and the role each plays:

| Story element | Circuit element | On the QuadRF schematic |
|---|---|---|
| The fish (unknown weight) | The radio chip's smooth output voltage | MAX2851 baseband output pins |
| The pan state (accumulated imbalance) | The capacitor's voltage (charge level) | 3.3 pF capacitor |
| The scale (left/right?) | The comparator | FPGA pin configured as LVDS input |
| Your hand adding/removing weights | A feedback voltage pushed back from the chip | FPGA output pin, the "FB" nets |
| The channel weights flow through | Resistors converting voltages to currents | The 2.2 kΩ resistors |
| The metronome | The FPGA's clock | ~40 MHz reference, multiplied internally |
| Your written move record | The stream of 1s and 0s inside the FPGA | The "bitstream," processed in logic |

The wiring, in words. The signal voltage connects through the first resistor to one node; call it the summing node. The capacitor sits at that node, accumulating. The node also connects to the LVDS pin's input, so the comparator constantly watches the bucket's level against a fixed reference (the pin's other input is parked at a midpoint voltage; on this board a small network establishes it). And here is the loop-closing stroke: an *output* pin of the FPGA connects **through the second resistor back to the same node**, and the FPGA drives that output with the *opposite* of whatever the comparator just said.

Now trace one clock tick around the loop, about 10 nanoseconds of real time:

The signal, via resistor one, pours a small current into the bucket; the pour rate is proportional to the signal's voltage right now (Ohm's law: the resistor converts voltage to flow). Simultaneously, the feedback pin, via resistor two, either pours in or draws out a fixed-size current, depending on the last decision. The bucket integrates the difference: its level drifts up or down according to whether the signal's pour currently exceeds the feedback's counter-pour. At the clock edge, the comparator samples the level: above the midpoint or below? That single bit is latched into the FPGA's logic (one more entry in the move record) and simultaneously flipped and sent back out the feedback pin, setting the counter-pour for the next tick. Repeat, forever, at tens or hundreds of millions of ticks per second.

The contraption has a name: a **first-order delta-sigma modulator** (equivalently sigma-delta; both orders of the words are used). The name is honest Greek bookkeeping: *delta* ($\Delta$) means difference, the signal-minus-feedback discrepancy that flows into the bucket each tick; *sigma* ($\Sigma$) means sum, the accumulation the bucket performs. Difference, then sum, then one-bit decision, then feed the decision back: that is the entire machine. "First-order" means there is one bucket in the loop; fancier versions chain several, a refinement noted later.

## 14. Watching it run: a worked example with actual numbers

Abstractions cement when you watch the numbers move. Normalize everything: say the signal can range from −1 to +1, the feedback pin pushes exactly −1 or +1, the bucket starts empty (0), and each tick the bucket's level changes by (signal − feedback) × 0.25 (the 0.25 standing in for the gentleness set by the resistors and capacitor). The comparator outputs 1 if the bucket is above 0, else 0, and feedback is +1 when the output is 1, −1 when it is 0.

Hold the signal steady at +0.6 and run twelve ticks:

| Tick | Bucket before | Comparator says | Feedback sent | Bucket after: prev + (0.6 − fb)×0.25 |
|---|---|---|---|---|
| 1 | 0.000 | 1 | +1 | 0.000 + (−0.4)(0.25) = −0.100 |
| 2 | −0.100 | 0 | −1 | −0.100 + (1.6)(0.25) = +0.300 |
| 3 | +0.300 | 1 | +1 | +0.300 − 0.100 = +0.200 |
| 4 | +0.200 | 1 | +1 | +0.100 |
| 5 | +0.100 | 1 | +1 | 0.000 |
| 6 | 0.000 | 1 | +1 | −0.100 |
| 7 | −0.100 | 0 | −1 | +0.300 |
| 8 | +0.300 | 1 | +1 | +0.200 |
| 9 | +0.200 | 1 | +1 | +0.100 |
| 10 | +0.100 | 1 | +1 | 0.000 |
| 11 | 0.000 | 1 | +1 | −0.100 |
| 12 | −0.100 | 0 | −1 | +0.300 |

Look at the output column: 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0... After the one-tick opening stumble, the machine locks into a repeating pattern of four 1s and one 0. Convert to the ±1 scale and average any five-tick window: (4×(+1) + 1×(−1))/5 = 3/5 = **0.6**. The input, exactly, encoded in the *density* of the bitstream. Change the input to +0.6003 and the pattern would no longer repeat every five; a lone extra 0 would appear roughly every 1,666 ticks, and a long enough average would read 0.6003. Every refinement of the input value shows up as a rearrangement of the rhythm, and averaging recovers it. The bucket, meanwhile, never settles and never escapes: it is forever being disturbed by the signal and herded back by the feedback, and its perpetual small agitation is precisely what keeps every comparator answer informative.

One vocabulary note: a stream like this, where the *density of pulses* carries the value, is called pulse-density modulation (PDM). You have met its output before without the name: MEMS microphones in phones emit exactly such streams, and Super Audio CD stored music this way.

## 15. Where the crudeness went: noise shaping, the deep idea

Now confront the question that should be nagging. The comparator's answers are still crude; each one commits a rounding error of enormous size (it reports ±1 when the truth is 0.6). Error cannot be destroyed by wiring. Where did it go?

It went *fast*. And that relocation is the profound part, the part that earned this architecture its dominance of modern conversion.

Think of the error as noise, an unwanted roughness added to the true value, and think of noise as having a *texture in time*. Some noise is slow and drifting (like a tide), some is fast and hashy (like ripples). Frequency is the axis that separates textures: slow textures live at low frequencies, fast hash at high frequencies. Our *signal* lives entirely at low frequencies; recall it wiggles at up to 20 MHz while the loop ticks vastly faster, so from the loop's perspective the signal is nearly a slow tide.

Now watch what the feedback loop does to error, mechanically. Suppose at some tick the quantizer commits an error, claims +1 when it should have claimed less. That excess is subtracted from the bucket via the feedback resistor. The bucket *remembers the debt*. On following ticks the bucket sits lower than it otherwise would, biasing the comparator toward answering 0, and within a tick or two the loop emits a compensating decision. **The loop never lets an error sit still. Every mistake is recorded in the bucket and provokes a prompt, opposite mistake.** Errors are forced to alternate rapidly, to cancel themselves over short windows. Slow, sustained error, the kind that would masquerade as signal, is structurally impossible: a persistent bias in the output would accumulate in the bucket without bound and force correction.

Translate that into the frequency picture and you get the canonical statement: the loop **shapes the quantization noise**, sweeping it out of the low frequencies (where the signal lives) and piling it up at high frequencies (where nothing of value lives). The total amount of error is unchanged, exactly as much gravel as ever, but the gravel has been bulldozed into a corner of the spectrum that we can simply decline to look at. In our twelve-tick table you can see shaping with the naked eye: the output's *errors* (the deviations of each ±1 from 0.6) flip sign in a tight rhythm, never drifting, never sustaining.

The standard engineering accounting, stated without derivation so the magnitudes are on record: merely sampling K times faster than necessary and averaging spreads the fixed noise over K times more bandwidth, improving in-band accuracy by half a bit per doubling of K. Adding the first-order loop steepens this to **1.5 bits per doubling**. Run the loop 256 times faster than the signal needs (utterly routine at these clock speeds) and the shaping plus averaging is worth on the order of 12 bits, i.e. a one-bit comparator delivering roughly 13-bit effective measurements. Chain two buckets (second-order loop) and it is 2.5 bits per doubling. This is not incremental engineering. This is an exchange rate between *clock speed*, which Moore's law made nearly free, and *component precision*, which physics keeps expensive, and the exchange rate is spectacular.

One more virtue hides in the single-bit choice itself, and it is why one bit is used even when more would seem better. A multi-level feedback would need its levels precisely spaced, reintroducing the matched-ladder problem through the back door. A one-bit feedback has exactly two levels, and *any* two points define a perfect straight line: there is no spacing to get wrong. Single-bit feedback is inherently, structurally linear. The design does not merely tolerate the crudest possible quantizer; it exploits a purity that only the crudest quantizer possesses.

## 16. Cashing the check: decimation, where the number is finally minted

The modulator's output is a firehose: hundreds of millions of one-bit answers per second. The final step converts the firehose into what the rest of the system actually wants, moderate-rate many-bit numbers, and this step is pure arithmetic, running as logic inside the FPGA, consuming no components at all.

The principle is averaging, executed in stages called **decimation** (keep the useful low-frequency content, discard the high-frequency corner where the noise was swept, and reduce the data rate accordingly). The workhorse structure is a cascade of the two cheapest operations in digital logic: running sums and subtractions, arranged as what engineers call a CIC filter. The details are optional; the essence is not: summing N one-bit values produces a log₂(N)-bit result, so *word width grows as rate shrinks*. A 256-tick window of one-bit answers collapses into one ~12-bit number; the stream of such numbers, emerging at a few tens of MHz, is the digitized radio signal, ready for the beamforming mathematics that is the QuadRF's actual purpose.

Step back and audit where the precision came from. Not from the capacitor: its exact value barely matters (it sets gentleness, not accuracy). Not from the resistors: their ratio matters only loosely. Not from the comparator: it only ever answered left-or-right. The precision came from the *clock* (crystal oscillators are naturally superb, cheap timekeeping is the one precision humanity gets almost free) and from *arithmetic*. The expensive analog ruler was replaced by counting, and counting is incorruptible.

## 17. Running the film backwards: the transmit side

The QuadRF must also *generate* radio signals: the FPGA computes a desired transmit waveform as numbers, and those numbers must become a smooth analog voltage for the radio chip to upconvert and broadcast. That requires a digital-to-analog converter, a DAC, per channel: sixteen more precision chips at conventional prices.

Same refusal, same trick, mirrored. The FPGA runs the sigma-delta loop *entirely in logic* this time (the signal is already numbers, so the bucket is just an accumulator variable and the comparator is just a sign check), producing a one-bit stream whose density traces the desired waveform. That stream is blasted out an ordinary digital pin, swinging hard between its two levels, the crudest possible waveform. Then physics performs the averaging: the pin drives a resistor into a capacitor, our bucket again, now cast as a *smoother*. The bucket cannot follow the nanosecond slamming; it responds only to the slow density, and its level glides along the intended smooth curve. The rounding hash, pre-shaped to high frequencies by the loop, is exactly what the sluggish bucket ignores.

You have owned this trick for years without the name. LED dimmers flick the LED fully on and off faster than your eye can follow, and your retina's own sluggishness does the averaging; the "brightness knob" adjusts only the density. Class-D audio amplifiers, which power essentially every phone speaker and soundbar made this decade, drive the speaker with precisely such a switched stream and let the speaker cone's inertia smooth it. The heating in your oven cycles on and off and the thermal mass averages. Density-plus-sluggishness is one of engineering's great recurring rhymes; sigma-delta is the rhyme perfected, with feedback aiming every pulse.

---

# Part III: The Real Board

## 18. Reading the actual schematic: the trick in the wild

Everything so far could describe a textbook. Here is how it manifests in the QuadRF's released schematics, component designator by component designator, so the abstract story can be pinned to the physical board.

The radio transceivers are a Maxim MAX2850 (four transmit chains) and MAX2851 (receive chains), WiFi-era chips dating from roughly 2010, chosen almost certainly because mature silicon in this class is cheap and available. The MAX2851's receive outputs appear on the schematic as differential pairs named RXBBI1± through RXBBQ4± ("RX baseband, I or Q, channels 1 through 4"): eight smooth analog signal pairs, our sixteen fish (each differential pair carrying one signal on two complementary wires, the same noise-cancelling doubling that LVDS uses).

Follow one channel, and there they are, exactly the cast from the table in section 13. Small transistor pairs (designators T1 through T8, part UMX5NTR) buffer and condition the radio chip's outputs, biased from a rail called VCCAUX; think of them as impedance adapters that let the delicate radio output drive the loop without being loaded down, a practical stagehand rather than a plot character. The signal then feeds a node carrying networks of 2.2 kΩ resistors: the voltage-to-current converters. A 3.3 pF capacitor (C52, C27, C29, and siblings, one per channel) sits at the summing node: the bucket, seven-nanosecond time constant, sized to the loop's clock. The node routes to FPGA pins that the FPGA schematic sheet shows configured as differential inputs, with pin names like RXBBQ1_IN_P/N: the comparators. And the giveaway, the nets that make the architecture unambiguous to anyone who knows what they are looking at: companion nets named RXBBQ1_FB_P/N and so on, **FB for feedback**, running from FPGA *output* pins back through 2.2 kΩ resistors into the very same summing nodes. Input pins watching a capacitor, output pins driving charge back into it through matched resistors: that closed geometry has exactly one common reading, and it is the balance scale. Sixteen scales, sixteen fish, one FPGA holding all the pens.

The schematic even annotates several channels with the word INVERT, marking where a differential pair's polarity is flipped for routing convenience and must be un-flipped in logic: the kind of detail that confirms the loop's sense (add versus remove) is closed inside the FPGA's configuration, which is to say inside the one artifact ScaleRF keeps proprietary. And that is the punchline of the business model, worth stating plainly: **on this board, the DSP bitstream is not merely processing attached to the ADC; the bitstream *is* the ADC.** The unprotectable parts (resistors, capacitors, an old Maxim radio chip) are visible to anyone; the converter itself is software.

The companion economy measure sits one sheet over and rhymes perfectly. The FPGA must ship its torrent of digitized samples to the Raspberry Pi 5, and the Pi's high-bandwidth ports are MIPI (the camera and display connectors, CSI and DSI, built to move gigabits of video). MIPI's physical layer normally requires dedicated interface silicon. The QuadRF schematic shows the FPGA's differential pins meeting the Pi through nothing but resistor networks, 100 Ω and 330 Ω, with a schematic note about achieving "half voltage (1.25 V) w/ 50 ohm impedance": the resistors passively translate the FPGA's signaling levels into MIPI's, and the D-PHY protocol itself is, once again, implemented in gateware. Two supposedly hardware problems, data conversion and gigabit interfacing, both dissolved into configuration.

Total silicon on the analog-to-digital frontier of a sixteen-channel coherent radio: zero converter chips, zero interface chips. Resistors, capacitors, and a text file.

## 19. The fine print: what this costs and why it doesn't matter here

Honesty requires the trade-offs, because the trick is not free lunch; it is lunch paid for in currencies this particular product happens to hold in surplus.

The LVDS pin was never specified as a comparator, and it shows in small ways. A purpose-built comparator has a characterized input offset (a small built-in bias in its left-or-right verdict); an LVDS receiver's offset is real but unspecified, guaranteed only "small enough for communications." In a sigma-delta loop a static offset merely shifts the measured zero point, and a radio's downstream math calibrates zero out routinely, so the vice is venial here, but a precision voltmeter could not be so forgiving. Likewise the pin may include a touch of deliberate hysteresis (a reluctance to change its answer, added by designers to stop communications inputs from chattering on noise), which in a converter loop slightly reshapes the noise; tolerable, again, because radio DSP is calibration-rich.

The clock inherits a promotion to precision component. Since all accuracy was moved into timing, the loop is sensitive to **jitter**, tiny random wobble in when clock edges land: a wobbly metronome smears the feedback pulses' effective size. This is the one place the architecture spends real care, and it is why the board's 40 MHz reference oscillator and the FPGA's clock synthesis matter more than any resistor value on the sheet.

The loop can also exhibit **idle tones**: with a perfectly still input at certain values, the bitstream's repeating pattern (like our 1,1,1,1,0 cycle) can alias into a faint audible-band whistle in unlucky designs. Radio signals are never still, and dithering (deliberately sprinkling a whisper of randomness into the loop) suppresses the effect; it is a footnote here, a genuine battle in audio converters.

And the architecture buys resolution with clock surplus, so it fits signals that are *slow relative to available clocks*. A 20 MHz baseband under a several-hundred-MHz loop clock enjoys a comfortable oversampling ratio; try to digitize a 500 MHz signal this way and the surplus evaporates. Conventional ADCs keep their market at the bleeding edge of bandwidth. The QuadRF's signals sit squarely in sigma-delta's sweet spot, which is precisely why the designers could shop in the free bin.

Higher-order loops (several buckets chained, each integrating the residue of the last) sharpen the noise shaping dramatically and rule commercial converter chips, at the price of stability analysis subtleties; a first-order or modestly-ordered loop built on unspecified pin behavior is the sane engineering choice for this application, and the visible one-capacitor-per-channel topology suggests exactly that restraint.

## 20. The idea underneath the idea

Pull the camera back, because the sigma-delta-on-LVDS trick is one instance of a principle that recurs across this product, across engineering, and frankly across epistemology.

**Precision is not a property of instruments. It is a property of procedures.** A crude instrument, wrapped in memory and feedback, run much faster than the phenomenon it observes, with the record processed by honest arithmetic, *is* a precise instrument. Hardware precision must be purchased over and over, part by part, channel by channel, against the perpetual sabotage of temperature and tolerance and age; procedural precision is purchased once, in design, and then replicated for free in every unit shipped, because clocks are cheap and math does not drift.

The same product plays the same card at the next level up. When multiple QuadRF tiles are chained into a large array, they need a shared sense of time to nanoseconds. The classical answer distributes one exquisite clock to every tile over carefully matched paths, precision hardware again. The QuadRF instead lets every tile free-run on a cheap oscillator, *measures* the arriving neighbor clock obsessively (hundreds of thousands of edge observations averaged per millisecond), and corrects each tile's data in arithmetic: resample here, rotate phase there. Don't distribute perfection; measure imperfection exquisitely and subtract it. The fish-weighing move, played with time itself as the fish.

Once you hold the pattern, you see it everywhere. GPS receivers extract nanosecond timing from noisy signals by correlating over millions of samples. Camera sensors average photon arrivals over an exposure; astrophotographers stack hundreds of frames, trading time for a signal buried far beneath any single frame's noise. Polling averages thousands of one-bit human comparators into percentages with decimal points. Dithering in audio and imaging deliberately adds noise so that averaging can recover sub-step detail, crudeness weaponized against itself. Even science as an institution runs the loop: crude individual experiments, memory in the literature, feedback through replication, precision emerging in the aggregate that no single trial possessed.

The history is worth one paragraph of respect. Delta modulation (feedback around a one-bit quantizer, no bucket yet) appears in a 1950s Bell Labs patent by C. Chapin Cutler; Inose and Yasuda in Tokyo added the integrator inside the loop in 1962 and named the delta-sigma modulator; and then the idea waited. It waited because its exchange rate, resolution for clock speed, was a bad trade in the vacuum-tube and early-transistor eras when speed was the scarce good. CMOS scaling inverted the market: by the 1990s clock cycles were abundant and analog matching was the bottleneck, and sigma-delta swept through audio, then instrumentation, then radio, until today it is the most manufactured converter architecture on Earth. The QuadRF's contribution is not the loop, which is seventy years old, but the noticing: that the loop's only remaining nontrivial component, the fast comparator, had quietly become a free byproduct of every logic chip's communications pins. The last dollar in the converter was hiding in a port.

That is the full circle back to the opening claim, now earned. A pin built to answer "which wire is higher?", a one-cent bucket that never forgets, two resistors that translate pressure into trickle, a metronome running heedlessly fast, and arithmetic that cannot be bribed: point them at a smooth unknowable curve, and out comes the number, to as many digits as you have patience. Nothing was measured precisely at any instant. Precision was never *in* any instant. It was in the history, the whole time.

---

# Appendix: Glossary

- **Voltage**: electrical pressure between two points.
- **Current**: flow rate of charge.
- **Resistor**: calibrated bottleneck; converts voltage to proportional current (Ohm's law, $I = V/R$).
- **Capacitor**: charge bucket; its voltage is the running total of all past current, hence an integrator and a memory.
- **Signal**: a voltage varying in time, carrying information.
- **Sampling**: measuring at regular ticks; lossless if faster than twice the signal's fastest wiggle (Nyquist).
- **Quantization**: rounding each measurement to a finite menu; the rounding error behaves as noise.
- **ADC/DAC**: converters between smooth voltages and numbers.
- **Comparator**: one-bit instrument answering "is A above B?".
- **LVDS**: two-wire digital signaling in which the bit is which wire is higher; every LVDS receiver is therefore a fast comparator.
- **FPGA**: a chip of reconfigurable logic, programmed by a bitstream file.
- **Delta-sigma modulator**: feedback loop of difference ($\Delta$), accumulation ($\Sigma$), one-bit decision, and correction, emitting a pulse-density bitstream.
- **Noise shaping**: the loop's forcing of quantization error into high frequencies, away from the signal.
- **Oversampling**: clocking the loop far faster than the signal requires, the raw material of the exchange.
- **Decimation**: the arithmetic averaging that mints many-bit numbers from the one-bit torrent.
- **Jitter**: timing wobble in the clock, the one imprecision this architecture cannot forgive, because time is where all the precision was hidden.
