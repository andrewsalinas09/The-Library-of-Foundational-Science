---
uid: wv5t8h31
title: Hearing a Whisper Under a Waterfall
subtitle: How GPS recovers a signal buried far beneath the thermal noise floor
domain: radio / signal processing
assumes: nothing
mechanisms:
  - direct-sequence-spread-spectrum
  - correlation-despreading
  - matched-filter
ideas:
  - processing-gain
  - known-signal-shape
  - coherent-integration
  - root-n-averaging
  - white-noise
  - stability-licenses-integration
analogy: >-
  A stadium full of shouting strangers, one whispering friend, and a ledger
  that tallies only what the friend was scheduled to say.
claim: >-
  A six-gram module tracks a satellite signal 300,000 times weaker than the
  noise its own electronics generate, and times its arrival to a few nanoseconds.
status: published
created: 2026-08-14
---

## Preface: the claim we are going to earn

A GPS satellite orbits 20,200 kilometers above your head. Its transmitter for the civilian signal puts out roughly 27 watts, about half a modern laptop charger. By the time that signal has spread across the 20,000-plus kilometers to your antenna, the power your receiver captures is about $10^{-16}$ watts: −130 dBm in the units radio engineers use, a tenth of a millionth of a billionth of a watt. Meanwhile, the electrons jostling around inside your receiver's own first amplifier, doing nothing but being warm, generate about 100 times more power than that in the frequency band the signal occupies. The satellite's signal is not merely faint. It is buried a factor of one hundred beneath the random hiss that your own hardware produces just by existing at room temperature.

And yet a six-gram module costing a few dollars, the u-blox SAM-M10Q sitting on a hobbyist breakout board, not only finds this signal but measures its arrival time to a few nanoseconds, which is how it tells you where you are to within a meter or two. More remarkably still, that module's datasheet claims it can keep tracking a GPS signal down to −165 dBm. That is not 100 times below the noise. That is roughly 300,000 times weaker than the noise in the signal's bandwidth, more than 50 dB down, the kind of signal level you get indoors, under a roof, with the satellite's transmission having leaked through building materials.

This sounds like a violation of something. It is not. By the end of this document you will be able to do the arithmetic yourself and see that the recovery is not just possible but inevitable, and you will know exactly what currency is being spent to buy it, because nothing here is free. The one-sentence spoiler: **the receiver knows, in advance and exactly, the shape of the signal it is looking for, and it trades time for signal-to-noise ratio at a fixed, guaranteed exchange rate.** The whole document is an unpacking of that sentence.

We will build everything from zero: what a radio wave is, what power and decibels are, where noise comes from physically, what bandwidth means, why random things partially cancel when you add them, and what a pseudorandom code is. Then we will assemble the mechanism using one analogy, carried all the way through: a stadium full of shouting strangers, one whispering friend, and a ledger.

---

# Part I: Raw materials

## 1. What a radio signal actually is

Take an electron and shake it back and forth. The electric field around it, the invisible influence it exerts on other charges, shakes too, and that disturbance does not stay put: it ripples outward at the speed of light, 300,000 kilometers per second. Far away, another electron sitting in a piece of wire feels the ripple arrive and gets shaken in sympathy, a tiny copy of the original motion. That is all radio is. A transmitter is a machine for shaking electrons in a controlled pattern; an antenna is a piece of metal shaped so its electrons shake efficiently; a receiver is a machine for noticing the sympathetic shaking at the far end.

If you shake the electrons back and forth smoothly and regularly, the resulting wave is a sinusoid: the same shape as a point on a spinning wheel viewed edge-on, rising and falling, over and over. Three numbers describe it completely. The **frequency** is how many complete back-and-forth cycles happen per second, measured in hertz (Hz); GPS's civil signal lives at 1,575,420,000 cycles per second, written 1575.42 MHz. The **amplitude** is how hard the shake is, which sets the power. The **phase** is where in its cycle the wave is at a given instant: just starting to rise, at its peak, crossing zero on the way down. Phase is the odd one out, easy to dismiss as bookkeeping, but hold this thought: **phase is the property GPS manipulates to carry information, and phase is what lets contributions either reinforce or cancel.** Almost everything later turns on that.

One more derived number: wavelength, the physical distance the wave travels during one cycle, equal to the speed of light divided by frequency. At 1575.42 MHz that is 19.0 centimeters. Every 19 centimeters of extra travel distance shifts the arriving wave by one full cycle of phase. Radio waves at this frequency pass through plastic and drywall, reflect off metal and ground, and are absorbed somewhat by water, including the water in leaves and in concrete.

A pure, endless sinusoid at one frequency carries no information; it is a tone, forever. To send information you must change something about it over time: the amplitude, the frequency, or the phase. Any such changing is called **modulation**, and the pure underlying tone being modulated is called the **carrier**. GPS uses the crudest, most robust modulation imaginable, and we will meet it in Section 6.

## 2. Power, and why engineers count in decibels

Power is energy per unit time, measured in watts. A phone charger delivers about 20 W. The numbers in radio span such an absurd range, from the 500 effective watts leaving the satellite to the 0.0000000000000001 W arriving at your antenna, that writing them as decimals is hopeless. So radio engineers count in ratios, and specifically in logarithms of ratios, called **decibels (dB)**.

The rule: every factor of 10 in power is 10 dB. A factor of 100 is 20 dB, a factor of a million is 60 dB. A factor of 2 is very close to 3 dB, worth memorizing. Decibels turn multiplication into addition: if a signal is attenuated by a factor of 100 (down 20 dB) and then amplified by a factor of 1000 (up 30 dB), the net is up 10 dB, a factor of 10. Radio link budgets, which chain together dozens of gains and losses, become simple sums.

Decibels are ratios, so to express an absolute power you must pick a reference. The universal choice is one milliwatt, and powers expressed relative to it are written **dBm**. Thus 0 dBm is 1 mW, +30 dBm is 1 W, and −130 dBm is $10^{-13}$ mW, which is $10^{-16}$ W. Fix these anchors in your head, because the whole story will be told in dBm:

* A WiFi router transmits about +20 dBm (100 mW).
* Your phone receives WiFi comfortably at −65 dBm.
* A weak, one-bar cellular signal is around −110 dBm.
* GPS arrives at about **−130 dBm**, a hundred times weaker than that one-bar cell signal.

Where does −130 come from? The satellite feeds about 27 W into an antenna that focuses the energy toward Earth rather than wasting it into space, concentrating it about 20-fold, for an effective radiated power near 500 W (+27 dBW). Spreading over the 20,200 km to the ground dilutes it by the surface area of that enormous sphere: at 1575 MHz over that distance the standard free-space calculation gives about 182 dB of path loss. Take +27 dBW, subtract 182 dB, subtract a couple more for the atmosphere and imperfect geometry, and you land at roughly −158 dBW, which is −128 dBm; the official GPS interface specification guarantees a minimum around −128.5 dBm at the ground, and −130 dBm is the traditional round working number. Remember this number.

## 3. Thermal noise: the waterfall we must hear through

Now for the villain, and it is worth understanding physically, because it is not interference, not other transmitters, not the ionosphere. It is heat.

Any resistor, any lossy piece of wire, any antenna at a temperature above absolute zero contains electrons in ceaseless random thermal motion, rattling around like gas molecules. Each rattling electron is a tiny current, and random currents in a conductor produce a random voltage across it. This was measured by John Johnson and explained by Harry Nyquist, both at Bell Labs, in 1928, and it is called Johnson-Nyquist noise or simply **thermal noise**. It is not a defect of cheap components. It is statistical mechanics, as fundamental as the pressure of a gas, and a perfect, ideal resistor exhibits it in full.

The formula is astonishingly simple. The noise power available from any resistor is

$$
N = kTB
$$

where k is Boltzmann's constant ($1.38 \times 10^{-23}$ joules per kelvin, the conversion factor between temperature and energy), T is the absolute temperature in kelvin, and B is the **bandwidth** over which you listen, in hertz. In plain words: **thermal noise is spread perfectly evenly across all radio frequencies, and the total noise power you collect is proportional to how wide a slice of spectrum you accept.** Nature meters out noise per hertz of listening width.

At room temperature, T = 290 K, the noise density kT works out to $4.0 \times 10^{-21}$ watts per hertz of bandwidth, which is **−174 dBm per Hz**. This is one of the most important numbers in all of radio engineering; it is the universal floor. Every antenna on Earth, pointed at warm ground and a warm atmosphere, and every room-temperature amplifier, delivers at least this much hiss per hertz. Real amplifiers add a little of their own on top; a good GPS front end adds about 2 dB (its **noise figure**), so the practical density is about −172 dBm/Hz.

A caution about that unit before using it, because "dBm/Hz" is a notorious abuse of notation that trips careful readers. It does not mean a quantity of decibels divided by a quantity of hertz. It is shorthand for "each 1 Hz slice of spectrum contains this many dBm of noise power," decibels referenced to one milliwatt *per hertz*; the pedantically correct spelling is dB(mW/Hz). The underlying physical operation is always plain multiplication in linear units: density times bandwidth equals power, watts per hertz times hertz equals watts. Decibels merely record the logarithm of that multiplication, and logarithms turn multiplication into addition, so in dB-land the bandwidth enters as an added term, $10 \cdot \log_{10}$ of the bandwidth measured against 1 Hz, a quantity with its own unit, **dB-Hz**. The dimensional algebra then closes exactly as it does in linear space: dBm/Hz plus dB-Hz yields dBm, the hidden per-hertz cancelling the hidden hertz, because inside the logarithms it is literally (W/Hz)·(Hz) = W. Keep dB-Hz in your pocket; it returns shortly with a starring role.

Two consequences to flag, both load-bearing:

**First: the noise floor is not a single number. It depends entirely on your bandwidth.** Listen over 1 Hz and the noise is −172 dBm. Listen over 2 MHz, which is what the GPS signal occupies, and the noise is −172 dBm/Hz + $10\log_{10}(2{,}046{,}000\,\text{Hz} / 1\,\text{Hz})$ = −172 + 63 = about **−109 dBm** (in linear units, the same statement reads $6.3 \times 10^{-21}$ W/$Hz \times 2.046 \times 10^{6}$ Hz ≈ $1.3 \times 10^{-14}$ W; run it both ways once and the notation loses its power to confuse). Compare with the signal at −130 dBm, and mind the sign convention: less negative means more power, so the noise at −109 is the larger of the two. The signal sits about 20 dB, a factor of 100, below the noise collected in its own bandwidth. That is the precise meaning of "below the thermal noise floor," and notice it already contains a loose thread: the floor moved when the bandwidth moved. Hold that thought hard; the entire trick lives in that thread.

**Second: amplification cannot help.** An amplifier multiplies whatever enters it, signal and noise alike, and adds a bit more noise of its own. The signal-to-noise ratio (SNR), the only thing that matters, is fixed at the very first stage and can only degrade afterward (a fact formalized as Friis's cascade formula in 1944). Turning up the volume on a whisper drowned by a waterfall gives you a loud waterfall.

Because signal and noise will be compared constantly, engineers use a bandwidth-independent figure of merit: the carrier-to-noise-density ratio, **C/N0**, the signal power divided by the noise power per hertz. For open-sky GPS: −130 dBm minus (−172 dBm/Hz) = 42 dB-Hz, with good conditions reaching 45 to 50. There is the promised return of dB-Hz: subtracting a density from a power leaves a logged hertz standing, which is why C/N0 carries that unit, and you can read the number physically as "the bandwidth over which signal power would exactly equal noise power," here about 16 kHz. This number is honest in a way "SNR" is not, because it does not smuggle in a bandwidth choice, and it is the number every GNSS receiver, including the SAM-M10Q, reports for each satellite.

## 4. Bandwidth: why signals take up width at all

We keep saying the GPS signal "occupies 2 MHz." Why does a signal occupy any width? Is not the carrier a single frequency, 1575.42 MHz, a single point on the dial?

An unmodulated carrier is indeed a single point. But the moment you change a signal in time, you widen it in frequency, and the two are locked in an exact reciprocal relationship: **the faster you change a signal, the wider the band of frequencies needed to describe it.** This is the heart of Fourier analysis, and here is the physical intuition. A sinusoid interrupted or flipped abruptly is no longer the smooth eternal wave of one pure frequency; the abrupt edge is a feature that no single slow sinusoid can trace. To build a sharp edge out of smooth waves you must add in faster waves and slower waves around the original, a whole chorus of neighboring frequencies whose sum is smooth where the signal is smooth and whose conspiracy of phases creates the edge where the edge is. The shorter the time-scale of the change, the wider the chorus. Quantitatively, a signal whose fastest features last about $\tau$ seconds occupies a bandwidth of about 1/$\tau$ hertz.

So: flip something about the carrier a million times per second, and the signal smears across roughly 2 MHz of spectrum (a million flips per second produces a main spectral lobe 2 MHz wide). Flip it only 50 times per second and it occupies a whisker of 100 Hz. GPS, as we will see, deliberately does the former, taking a signal whose actual information content needs only about 100 Hz and smearing it across 2 MHz, a factor of 20,000 wider than necessary. Given what Section 3 said, that the noise you collect grows with the bandwidth you accept, this seems perverse: spreading the signal wide forces the receiver to open a wide gate and drink 43 dB more noise than the information requires. **The apparent perversity is the design.** Why anyone would do this on purpose, and how the receiver un-does it, is the subject of Part II. What you should hold from this section is the reciprocity itself: fast changes mean wide bandwidth, slow changes mean narrow bandwidth, and a receiver's noise intake is set by the width of the gate it must hold open.

## 5. The arithmetic of randomness: √N versus N

This section is the single most load-bearing raw material in the document. It is pure arithmetic, no radio at all.

Suppose you add up N numbers that are each random, equally likely to be positive or negative, each with typical size 1. What is the typical size of the sum? Not N: the terms do not cooperate. Not zero: cancellation is never perfect. The answer, one of the most consequential facts in all of measurement science, is that the sum typically has size **$\sqrt{N}$**. This is the drunkard's walk: a stumbling drunk taking N random steps of one meter ends up, on average, about $\sqrt{N}$ meters from the lamppost, not N meters and not zero. The reason, in plain words: each new random term is as likely to partially cancel the running total as to extend it, so the total creeps outward far slower than the count of steps. (Formally: variances of independent random quantities add, so the standard deviation, the square root of the variance, grows as the square root of the count.)

Now suppose instead you add up N numbers that are each exactly +1, or more generally N copies of the same value a. The sum is exactly N·a. Deterministic contributions add **coherently**, in proportion to N; random contributions accumulate **incoherently**, in proportion to $\sqrt{N}$.

Put both in the same sum and watch what happens. Each term is (a + noise), a tiny fixed signal plus a unit-sized random error, with a much smaller than 1 so any individual term is useless, dominated by its noise. Sum N of them:

* the signal part grows as N·a,
* the noise part grows as $\sqrt{N}$.

The ratio of signal to noise in the sum is $N \cdot a/\sqrt{N}$ = **$\sqrt{N} \cdot a$**. It grows without bound. Add enough terms and the signal must eventually tower over the noise, no matter how small a is. In power terms (power goes as amplitude squared), the signal-to-noise power ratio improves by a factor of exactly N: **every doubling of the number of summed terms buys 3 dB.** Sum a million terms, gain 60 dB.

This is why averaging repeated measurements works, why your oscilloscope's averaging mode cleans up a trace, why stacking 300 subframes of a nebula from a telescope pulls detail out of sky glow that no single frame contains. It is a guaranteed exchange rate: time in, SNR out, at 3 dB per doubling.

But read the fine print of the arithmetic, because it hides the requirement that will drive the whole design of GPS. The signal terms only add as N if they all have the same sign, if they are *aligned*. If the signal itself flips sign unpredictably from term to term, then the signal is just another random contributor, it accumulates as $\sqrt{N}$ like the noise, and the ratio never improves. **Coherent gain requires knowing the sign pattern of the thing you are accumulating.** If the signal flips signs but you know the flip pattern in advance, you can multiply each term by the known sign before adding, un-flipping every flip, restoring perfect alignment, and collecting the full factor of N. Knowledge of the pattern is what converts a signal from "random, grows as $\sqrt{N}$" to "coherent, grows as N."

Hold this thought with both hands: **the difference between N and $\sqrt{N}$ is knowledge, and that gap, the factor $\sqrt{N}$, is the entire profit margin of GPS.**

## 6. Chips and phase flips: the simplest possible modulation

How does GPS imprint a pattern on its carrier? By the bluntest method available: at prescribed instants, it flips the phase of the carrier by 180 degrees, turning the sinusoid exactly upside down. A sinusoid flipped upside down is the same as the sinusoid multiplied by minus one. So the transmitted signal is simply

> carrier × (a stream of +1s and −1s).

This is **binary phase-shift keying (BPSK)**: the information is a sequence of signs, and the radio wave is the carrier wearing that sequence. It is maximally robust because the receiver only ever has to answer the easiest possible question, "is the wave right-side-up or upside-down right now?", and it maps perfectly onto Section 5, whose entire machinery was about sums of terms with signs.

GPS's civil signal carries two sign streams multiplied together, running at wildly different speeds:

* The **navigation data**, the actual information (satellite orbit parameters, clock corrections, health), at a stately 50 bits per second. Each bit lasts 20 milliseconds.
* The **spreading code**, a fixed, publicly known pattern of 1023 signs that repeats every 1 millisecond, meaning the signs flip at 1.023 million per second. To keep vocabulary clean, each sign of this fast pattern is called a **chip**, not a bit, because chips carry no information; the pattern is fixed and known to everyone in advance.

The transmitted sign stream is (slow data bit) × (fast chip pattern), and by Section 4's reciprocity, the 1.023 MHz chipping smears the signal across about 2 MHz of spectrum. The 50 Hz information, which would have fit in about 100 Hz, has been deliberately spread by a factor of 20,460. Also note the physical scale, because it becomes the ruler that GPS measures position with: at the speed of light, one chip lasts 0.978 microseconds and is therefore 293 meters long in flight, and one full 1023-chip code period is one millisecond long, 300 kilometers of wave, streaming past your antenna a thousand times per second.

## 7. Pseudorandom codes: noise you can write down

The last raw material is the chip pattern itself. Its design requirements are strange and specific: it must *look* statistically like a fair coin flip sequence (balanced, patternless, no structure a narrow filter could exploit), yet be *exactly reproducible* by anyone, because Section 5 taught us that the receiver must know every sign in advance. Deterministic noise. Noise with a published score.

Such sequences are called **pseudorandom noise (PRN)** codes, and they are generated by one of the cheapest machines in digital electronics: a linear-feedback shift register, a row of ten memory cells that shuffles its contents along each tick and feeds a couple of them, combined, back into the front. Ten cells produce a sequence that takes 1023 ticks to repeat, wandering through every nonzero state, looking for all the world like coin flips. GPS combines two such registers, offset differently for each satellite, to make a family called **Gold codes** (Robert Gold, 1967), 32 different 1023-chip patterns, one per satellite, all published in the GPS interface specification. Your receiver has all 32 in its memory before it is ever switched on. In stadium terms, to preview the analogy: every friend's whisper schedule was agreed upon decades ago and printed in a public book.

What makes these codes precious is their **correlation** behavior, and correlation is the operation the entire receiver is built around, so define it plainly: to correlate two sign sequences, multiply them position by position and add up the products. Where the sequences agree, the product is +1; where they disagree, −1. The correlation is therefore (number of agreements) − (number of disagreements): a similarity score.

Gold codes are engineered so that this score behaves like a lock:

* A code against a perfectly aligned copy of itself agrees everywhere: score **+1023**. (The key turns.)
* A code against itself shifted by even one chip, out of the 1022 possible misalignments: score at most 65 in magnitude, typically much smaller. (The key does not turn a fraction; it does not turn at all.)
* A code against any of the other 31 satellites' codes, at any alignment: again at most 65. (No other key turns this lock.)

The ratio 1023 to 65 is about 24 dB of discrimination, and the collapse from 1023 to nearly nothing happens within a single chip of misalignment, within 293 meters of flight distance, less than a microsecond of timing. Hold this final thought: **the correlation score is a cliff, and the location of the cliff edge, found to a tiny fraction of a chip, is a stopwatch reading.** That cliff is simultaneously the mechanism of signal recovery and the mechanism of ranging; GPS gets both from the same operation.

We now own every raw material: waves and phase (1), power in dBm (2), noise as kTB with the bandwidth-shaped floor (3), the speed-width reciprocity (4), the N versus $\sqrt{N}$ gap that knowledge converts (5), signals as sign streams (6), and published sign patterns with cliff-like correlation (7). Time to assemble the machine.

---

# Part II: The mechanism

## 8. The naive approaches, and exactly why they fail

**Naive approach 1: amplify harder.** Already dead on arrival; Section 3 killed it. The signal-to-noise ratio is set at the antenna and the first transistor, where the signal is 20 dB under the noise, and every later stage can only preserve or worsen that ratio. Gain is free and useless.

**Naive approach 2: filter narrower.** Section 3 also showed the noise floor is proportional to bandwidth, so shrink the bandwidth. The information is only 50 bits per second; a 100 Hz filter would collect only −172 + 20 = −152 dBm of noise, and our −130 dBm signal would stand 22 dB proud of it. Problem solved?

No, and the reason is the crux of the entire subject. The signal, as transmitted, is not 100 Hz wide. The chipping smeared it across 2 MHz (Section 4), which means its energy is *distributed* across that whole width. A 100 Hz filter placed anywhere in the band captures only 100 Hz worth of the signal, about 1/20,000 of its power, along with 100 Hz of noise. The SNR inside the narrow filter is exactly as bad as before. **You cannot filter your way out, because filtering selects by frequency, and the signal has been deliberately arranged to have no frequency concentration to select.** The spreading code made the signal noise-like on purpose; to a filter, it *is* noise. (This is, incidentally, why the same technique serves militaries as "low probability of detection" communications: to anyone who does not know the code, the transmission is statistically indistinguishable from a slight warming of the noise floor.)

So the receiver faces a chicken-and-egg problem. To collapse the signal back into a narrow bandwidth where the noise floor is low, you must first *undo the chipping*, multiply the incoming signal by the very same ±1 pattern at the very same alignment, so the flips cancel (−1 × −1 = +1) and the smooth, narrow 50 Hz signal reappears. But undoing the chipping requires knowing the pattern (fine: it is published) *and* its exact arrival alignment, to within a fraction of a microsecond, and the alignment depends on the unknown distance to the satellite, which is the very thing GPS exists to measure. The receiver must find the alignment of a signal it cannot yet see.

The resolution: it does not need to see the signal to test an alignment. It only needs Section 5's arithmetic. Here is the machine, first as a story.

## 9. The stadium and the ledger

You are standing at the top row of a packed stadium, 100,000 strangers below. Once per second, every stranger flips a coin and bellows either "AAH" (call it +1) or "OHH" (−1) at full lungpower. The combined roar is deafening and perfectly random. Somewhere down on the pitch stands your friend, whispering, one hundredth as loud as the crowd's roar, inaudible in any honest sense of the word. You will never hear your friend. That is not the plan.

The plan was made last year. You and your friend agreed on a schedule, a long printed list of +1s and −1s, one per second: at second 1 whisper "aah," second 2 "ohh," second 3 "ohh," and so on, a pseudorandom pattern you both hold a copy of.

Your only instrument is a dumb sound meter that reports one signed number per second: the net acoustic sum of everything, crowd plus friend, that second. You keep a ledger. Each second you write down two things: the meter reading, and, from your printed schedule, the sign your friend was supposed to be whispering. You multiply the two and add the product to a running total. That is the entire procedure: multiply by the expected sign, accumulate.

Watch what the running total does to each party. Your friend's contribution to each meter reading is (scheduled sign) × (whisper loudness); multiplying by the scheduled sign gives sign² × whisper = **+whisper, every single second, always positive**. The multiplication un-flips every flip. Your friend's contribution marches upward by one whisper per second: coherent, growing as N. The crowd's contribution each second is a random number, and multiplying a random number by your schedule's ±1 just gives another random number; the crowd's contribution to the total is a drunkard's walk, growing as $\sqrt{N}$. After N seconds the friend stands at N whispers against crowd noise of $\sqrt{N}$ roars. With the whisper 100 times quieter than the roar, the friend's total pulls even with the crowd's wander when $\sqrt{N}$ = 100, at N = 10,000 seconds, and towers 10 times above it at N = 1,000,000. **Nothing was filtered. Nothing was amplified. You heard nothing. You correlated, and the schedule converted your friend's contribution, and only your friend's contribution, from random to coherent.**

Now the three elaborations that complete the analogy, each one a pillar of GPS:

**Many friends, one stadium.** Suppose thirty friends stand on the pitch, each whispering their own agreed schedule, all simultaneously, all in the same acoustic channel. When you run your ledger against friend 7's schedule, friend 7 accumulates coherently while the crowd *and all 29 other friends* accumulate as random walks, because their schedules are (by Gold's construction) nearly uncorrelated with the one you multiplied by. One physical channel, thirty separable whisperers, separated not by frequency or by time slots but by pattern. This has a name you have met in another costume: **code-division multiple access, CDMA**, the principle inside 1990s Qualcomm cell phones. All GPS satellites transmit on precisely the same 1575.42 MHz carrier, forever, simultaneously, and never interfere, because each wears its own code.

**The slide.** You do not actually know when your friend started the schedule; the sound also took time to cross the stadium. If your ledger's schedule is offset from the friend's actual whispering by even one time slot, the products (scheduled sign) × (actual sign) are effectively random, and the friend's contribution collapses from N to a random walk: the cliff of Section 7. So you run 1,023 ledgers in parallel, one per possible offset, and see which single ledger's total explodes upward. The offset of the winning ledger tells you, to within one time slot, exactly how delayed the friend's whisper stream is. **The search for the signal and the measurement of its travel time are the same act.** In GPS this offset, refined below one hundredth of a chip by comparing the totals of ledgers half a chip early and half a chip late, converts to distance at 293 meters per chip, and sub-meter ranging falls out.

**The schedule flip.** Your friend also wants to tell you something, not just be found. So once every 20 repetitions of the schedule, the friend either whispers the schedule as printed (+1: data bit 0) or whispers it globally inverted (−1: data bit 1). Your accumulated total for that stretch comes out strongly positive or strongly negative, and its *sign* is the message, delivered at a rate 20,000 times slower than the whispering. That is the 50 bit-per-second navigation data riding on top of the 1.023 Mchip code.

## 10. Transcribing the analogy into the receiver

The stadium is exact, not decorative. Here is the element-by-element mapping into hardware:

| Stadium element | GPS element | Where it lives in a real receiver (e.g., SAM-M10Q) |
|---|---|---|
| Friend's whisper | Satellite signal, ~ −130 dBm | Induced current in the 15.5 mm patch antenna |
| Crowd's random roar | Thermal noise kTB, ~ −109 dBm in 2 MHz | Antenna + SAW filter + LNA front end (NF ≈ 2 dB) |
| Whisper 100× under roar | SNR ≈ −20 dB pre-despreading | C/N0 ≈ 42 dB-Hz open sky |
| Printed schedule | 1023-chip Gold code, one per satellite | Stored/generated by a 10-stage shift register per channel |
| One meter reading per second | One complex sample of the downconverted band, ~2 to 16 Msample/s | The RF chip's ADC, often only 1 to 3 bits wide |
| Multiply reading × scheduled sign, add to total | The correlator: sample × local code replica × local carrier, integrate | Dozens to thousands of hardware multiply-accumulate lanes |
| Ledger total after N seconds | Correlation value after coherent integration time T | The I/Q accumulator dumped every 1 to 20 ms |
| 1,023 parallel ledgers at all offsets | Code-phase search during acquisition | Massively parallel correlator bank / FFT-based search |
| Winning ledger's offset | Code phase → pseudorange (293 m per chip) | The observable behind the position fix and the PPS timepulse |
| 30 friends, separate schedules | CDMA: all satellites share 1575.42 MHz | 12 to 100+ tracking channels running concurrently |
| Schedule occasionally inverted wholesale | 50 bps navigation data bits (20 ms each) | Ephemeris, clock corrections, decoded after tracking locks |

Two elements of the real system have no stadium counterpart and need a word each.

**The carrier must be un-spun too.** The whisper arrives riding a 1575.42 MHz sinusoid, and the receiver must multiply not only by the code replica but by a local copy of the carrier to bring the signal down to a standstill (this is the "× local carrier" in the table, done as a complex multiply producing the in-phase and quadrature components, I and Q). The complication: the satellite is moving at 3.9 km/s, so its radial motion Doppler-shifts the carrier by up to about ±4 kHz, and the receiver's own cheap crystal oscillator is off-frequency by typically another few kHz at L1. If the local carrier is wrong by more than roughly 1/(2T) Hz over a coherent integration of length T, the accumulating products slowly rotate in phase and cancel themselves. So acquisition is really a **two-dimensional search**: 2,046 half-chip code offsets × a few dozen 500 Hz Doppler bins, several tens of thousands of ledger cells, which is exactly why GNSS chips contain huge parallel correlator arrays and why cold starts historically took minutes and now take about 25 seconds. Once found, two feedback loops take over: a delay-locked loop nudging the code replica to stay centered on the correlation peak, and a phase/frequency-locked loop chasing the carrier. Acquisition is the search; **tracking** is surfing the peak continuously thereafter.

**The objection you should be raising: the ADC.** The meter readings are digitized by an ADC with as little as one or two bits. One bit! How can a signal 100 times smaller than the noise survive quantization to a single sign bit? Because the noise itself acts as natural dither: with the input dominated by Gaussian noise, the *probability* that a given sample quantizes to +1 rather than −1 is delicately biased by the tiny signal riding on it, and the correlator's million-sample accumulation reads out that bias with exquisite precision. Hard one-bit quantization costs only about 2 dB of effective SNR (the factor 2/π), and 2-bit costs about 0.5 dB. This is why GPS front ends are so cheap: **the precision was never in the ADC; it emerges from the statistics of the accumulation.** The receiver is, in a real sense, measuring a probability, not a voltage.

## 11. The books balance: where the 20 dB went

Now run the accounting and watch the "impossible" 20 dB deficit get repaid with interest. Multiplying by a perfectly aligned code replica turns the received chip flips into an unbroken, flip-free tone (−1 × −1 = +1, everywhere). By Section 4's reciprocity run in reverse, a signal that no longer changes quickly no longer occupies a wide band: **despreading collapses the signal from 2 MHz back into the ~100 Hz its information always needed, without touching the noise**, which stays uniformly smeared. Integrating coherently for T seconds is equivalent to listening through a filter only 1/T hertz wide. The numbers, per millisecond of integration (one full code period, 2,046 samples at two samples per chip):

* Before: signal −130 dBm, noise in 2.046 MHz ≈ −109 dBm, SNR ≈ **−21 dB**.
* Integrate 1 ms: effective bandwidth 1 kHz, noise −172 + 30 = −142 dBm, SNR = **+12 dB**. The peak is already unmistakable.
* Integrate 20 ms (one full data bit, the longest stretch guaranteed flip-free): effective bandwidth 50 Hz, noise −155 dBm, SNR = **+25 dB**. Comfortable, clean, decodable.

The gain from despreading plus integration is the famous **processing gain**, and its size is simply the spreading ratio: $10\log_{10}(\text{chip rate} / \text{data rate}) = 10\log_{10}(1.023\,\text{MHz} / 50\,\text{Hz})$ ≈ **43 dB**, a factor of 20,000, precisely the factor by which the transmitter widened the signal in the first place. The transmitter dug a 43 dB hole and handed every code-holding receiver a 43 dB ladder. To anyone without the code, only the hole exists.

---

## A worked numerical example you can check by hand

Let us shrink the system until every number fits on paper, then run it honestly (the noise values below come from an actual simulation with a fixed random seed, not idealized).

The toy system: a 7-chip pseudorandom code, C = [+1, +1, +1, −1, −1, +1, −1] (a maximal-length shift-register sequence, the 7-chip cousin of GPS's 1023). The "satellite" transmits this code repeated over and over with amplitude a = 0.2. The channel adds Gaussian noise of standard deviation 1.0 to every chip. So each received sample is 0.2 × (scheduled sign) + (noise of typical size 1): per-sample SNR = $0.2^{2}/1^{2}$ = 0.04, which is **−14 dB**, the signal 25 times below the noise in power. Genuinely buried: here are the first seven received samples from the simulation, with the transmitted pattern + + + − − + −:

> 0.20, 0.50, −0.07, −1.09, −0.65, −0.79, −0.14

Stare at those as long as you like; the pattern is not visibly there (sample 3 even has the wrong sign). Correlating just this single period against the code gives 1.72, when pure noise would typically give ±$\sqrt{7}$ ≈ ±2.6. One period tells us nothing, exactly as one second of stadium ledger tells us nothing.

Now integrate: repeat the code P = 100 times (700 received samples) and compute the full correlation, the ledger total, at every one of the 7 possible alignments:

| Code shift (chips) | Correlation total | Prediction |
|---|---|---|
| **0 (aligned)** | **+114.1** | mean +140, noise $\sigma$ ≈ ±26.5 |
| 1 | −44.5 | mean −20, ±26.5 |
| 2 | −32.5 | mean −20, ±26.5 |
| 3 | −27.0 | mean −20, ±26.5 |
| 4 | −49.2 | mean −20, ±26.5 |
| 5 | −35.1 | mean −20, ±26.5 |
| 6 | +18.0 | mean −20, ±26.5 |

Verify the predictions yourself. Aligned: the signal contributes a × (number of samples) = 0.2 × 700 = +140 coherently; the noise contributes a random walk of $\sqrt{700} \times 1$.0 ≈ 26.5; the realized value 114.1 sits one noise-sigma below the mean, unremarkable. Misaligned: this m-sequence's off-peak correlation is −1 per period, so the signal contributes −0.2 × 100 = −20, plus the same ±26.5 walk; all six realized values land within that band. The aligned cell stands about 5 standard deviations above its rivals, a detection you could bet on, and post-correlation SNR is $a^2$·(700)/$\sigma^2$ = 28, which is **+14.5 dB, a swing of 28.5 dB from the −14 dB we started at**, purchased with exactly 700 samples: $10\log_{10}(700)$ = 28.5 dB. The exchange rate paid out to the decibel.

And that is not a coincidence of the example; it is the theorem. GPS runs the identical arithmetic with a = "100 times under the noise" and, in one millisecond, N = 2,046 samples instead of 700, then keeps going: 20 ms, then (as we will see) seconds. Want the peak higher? Integrate longer. The knob has no detent.

---

## The deep part: where, exactly, did the signal-to-noise ratio come from?

Something should still feel unpaid-for. The signal arrived 100 times below the noise, and we did not filter, did not amplify, did not cool the receiver. Multiplying by ±1 adds no energy. Where did 40-plus decibels come from?

The honest answer reorganizes how you think about noise floors: **the signal was never below the noise in the only accounting that physics cares about, which is energy, not power.** "The noise floor" at −109 dBm was not a fact about nature; it was a fact about a bookkeeping choice, namely comparing the signal against noise collected across the full 2 MHz gate over a single sample's duration. Nature's actual ledger is this: the signal delivers energy at C = $10^{-16}$ joules per second, and the noise is an energy density of N0 = $6.3 \times 10^{-21}$ joules per hertz of bandwidth (that is what "watts per hertz" is: joules). Neither of those is above or below the other; they have different units. They only become comparable once you decide how long to collect and how much bandwidth to accept, and both of those are choices.

The receiver's whole strategy is to make those two choices adversarially well. Collect for the duration of one data bit, T = 20 ms: signal energy captured, E = C·T = $2 \times 10^{-18}$ J. Accept only the bandwidth the information genuinely occupies, 50 Hz, which the despreading made possible: noise energy in the decision, N0 × 50 Hz × 20 ms = $6.3 \times 10^{-21}$ J... and the ratio E/N0 is about 320, or 25 dB, matching Section 11. The 43 dB of processing gain was never created; it was *recovered*. The transmitter's spreading had scattered the signal's energy across 20,000 times more bandwidth than its information required, artificially inflating the noise gate an ignorant receiver must open. Despreading merely restores the natural gate width. **Processing gain is not a violation of any limit; it is the un-doing of a self-imposed handicap, and the code is the receipt that lets you claim the refund.**

There is a deeper theorem standing behind this, worth knowing by name: the **matched filter theorem** (D.O. North, 1943, RCA Labs, working on radar). It says that when a signal of *known shape* is buried in white noise, the detector that maximizes output SNR is precisely correlation against a template of that shape, and the resulting SNR is 2E/N0: it depends **only on the collected signal energy and the noise density, and not at all on the signal's power, bandwidth, or duration individually**. A signal can be arbitrarily weak in power and remain perfectly detectable, provided you know its shape and can afford to collect it long enough for the energy to mount up. Sub-noise-floor recovery is not a trick appended to detection theory; it is detection theory's central result. What the theorem prices explicitly is the cost of admission: the words "of known shape." The entire 43 dB is paid out only against presented knowledge. An adversary without the code holds a claim on nothing; for them the drunk walks forever.

One more ownership-of-property statement, the one that should reorganize your head: **the receiver's sensitivity does not live in its antenna, its amplifier, or its ADC. It lives in a copy of a 1023-chip sequence agreed upon before the receiver was built, plus arithmetic, plus patience.** Knowledge of signal structure is a physical resource, interchangeable with antenna aperture and transmitter power at a published exchange rate. GPS works because the system's designers moved the hard part of the link budget out of the hardware and into an agreement.

---

## The fine print: what the trick costs and where it breaks

No free lunch was served above; itemize the bill.

**The currency is time, and the exchange rate decays.** Coherent integration pays 3 dB per doubling, but only while three things hold still: the data must not flip (20 ms ceiling for legacy GPS, unless assistance data tells you the bits in advance, which is exactly what modern "coherent assisted GNSS" does), the local oscillator must not drift a significant fraction of a carrier cycle (a garden-variety TCXO limits unaided coherence to tens of milliseconds; this is why timing-grade receivers carry better oscillators), and the *user must not move unpredictably* (a few centimeters of unmodeled motion is a whole carrier phase revolution at 19 cm wavelength). Past those limits the receiver falls back to **noncoherent integration**: square each coherent block's magnitude (discarding the un-trackable phase) and add the squares. Squaring commits the sin of multiplying noise by noise, incurring the **squaring loss**, and the payout degrades from 3 dB per doubling toward roughly 1.5 dB per doubling at low SNR. This soft ceiling, not any hard wall, is what ultimately sets the −165 dBm figure: each extra dB of sensitivity costs progressively more seconds, and below roughly −160 dBm the costs compound viciously.

**Knowledge is the gate, and partial knowledge partially fails.** Everything assumed the code is known exactly. The military P(Y) and M signals are the contrapositive: same physics, encrypted codes, so the 43 dB ladder simply is not handed to you. Similarly, an unknown weak signal from nature (SETI's problem) gets no processing gain against its unknown structure; only known-template searches (LIGO's solution) collect it.

**Jamming wins the raw power war.** Processing gain protects against exactly its own size. A jammer overpowering the signal by more than roughly the 43 dB margin (minus loop margins, in practice ~30 to 40 dB) captures the front end, and 43 dB above −130 dBm is only −90 dBm: a one-watt jammer does that from tens of kilometers. This is why GPS jamming is trivially easy, why the SAM-M10Q ships with jamming/spoofing detection flags, and why anti-jam receivers reach for a resource correlation cannot supply, spatial nulling with antenna arrays. Note also the doppelgänger threat: since the codes are public, a spoofer can transmit a *stronger correct* signal, and correlation, which rewards code match rather than provenance, will happily lock to the lie.

**The near-far problem.** Gold codes suppress cross-talk by only ~24 dB, fine when all satellites arrive within a few dB of each other (the GPS geometry guarantees this), fatal if one transmitter is vastly closer than another. Terrestrial CDMA systems survive only via strict transmit power control; GPS survives by orbit.

**Multipath is inside the moat.** A reflection of the true signal carries the true code and correlates beautifully, arriving tens of nanoseconds late and dragging the measured cliff edge by meters. Processing gain is helpless here because the enemy is a copy of the friend. This, not noise, is the dominant error source in cities, and it is the actual reason the 30 ns PPS is 30 ns rather than 3.

**And the deliberate trade at the heart of it: spreading spends bandwidth.** GPS occupies 2 MHz (24 MHz for the full modernized ensemble) of globally protected spectrum to move 50 bits per second. It is among the most bandwidth-profligate communication systems ever deployed, and correctly so, because the mission needed chip-edge timing (Section 7's cliff is sharp *because* the bandwidth is wide: ranging precision is bought with the same coin), CDMA sharing, and interference resistance, and protected spectrum was purchasable while transmitter watts on a 1970s satellite were not. The system has bandwidth in surplus and power in famine; spread spectrum is precisely the arbitrage between those two markets.

---

## The idea underneath the idea

Zoom all the way out. The pattern is: **a signal too weak to see in any single look becomes arbitrarily visible if you know its structure, because knowledge lets you add looks coherently (as N) while everything you did not predict adds incoherently (as $\sqrt{N}$.** Correlation against a known template, plus patience. Once you hold that shape, you will find it running the world:

* **The lock-in amplifier** (R.H. Dicke, 1946), the patron saint of every precision optics lab: chop or modulate the quantity you care about at a known reference frequency and phase, multiply the measured mess by the reference, integrate. A photodiode signal nanovolts deep under 1/f noise and room light walks straight out.
* **Radar pulse compression** (independently matured in WWII-era and 1950s programs): transmit a long, low-power coded waveform (a chirp or a Barker/PRN phase code), correlate on receive, and get the detection energy of the long pulse with the range resolution of a short one. Same theorem, pointed outward; the matched filter was literally invented for this.
* **LIGO**: gravitational-wave strains at $10^{-21}$ arrive beneath seismic and quantum noise; detection is correlation of the strain record against a bank of ~250,000 pre-computed general-relativity waveform templates. GW150914 was a correlation peak, found the same way a cold-starting receiver finds PRN 7.
* **Pulsar astronomy**: individual pulses from most pulsars are below the radio noise of any dish; astronomers "fold" the data stream at the known rotation period, stacking thousands of periods so the pulse adds as N. The known period is the code.
* **Astrophotography stacking**: hundreds of subframes, each with the nebula far beneath read noise and sky glow, registered (that is the alignment search) and averaged: target adds as N, noise as $\sqrt{N}$. A telescope with a cooled CMOS camera is a GPS receiver whose code is the sky's fixed geometry.
* **CDMA cellular and modern spread-spectrum radio** (IS-95, 1995; today's GNSS constellations, military links, and notably LoRa, whose chirp spread spectrum decodes packets ~20 dB under the noise floor at SF12, which is precisely how kilometer-scale mesh nodes whisper to each other on milliwatts).

The history explains why the idea, mathematically available since the 1940s, waited decades to reach your pocket. The pieces arrived in this order: North's matched filter (1943) and Shannon's proof (1948-49) that wideband, noise-like signaling was not merely tolerable but capacity-optimal; the famous Hedy Lamarr and George Antheil frequency-hopping patent (August 1942), a sibling idea from outside the establishment, unbuilt because its player-piano-style synchronization was mechanically hopeless; MIT Lincoln Laboratory's classified NOMAC and Rake systems (Price and Green, mid-1950s), the first true direct-sequence radios, racks of vacuum-tube equipment affordable only to the military; Gold's code families (1967); and then the inversion that made everything flip: **digital logic became effectively free.** A PRN generator is ten flip-flops; a correlator is a multiply-accumulate; by the 1970s these cost dollars and by the 1990s micro-cents. The moment generating and correlating pseudonoise became cheaper than transmitting watts or buying exclusive spectrum, the optimal engineering answer inverted from "concentrate your power in the narrowest possible band and keep others out" to "smear your power below everyone's noise floor and share." GPS (approved 1973, first satellite February 1978, full constellation 1995, and fully open to civilians at full accuracy when Selective Availability was switched off in May 2000) was the first planetary-scale monument of that inversion, and it is why the sensitivity of the radio in your pocket is mostly not made of metal. It is made of agreement, arithmetic, and time.

---

# Appendix: Glossary

* **Acquisition**: the initial 2-D search over code offset and Doppler for a satellite's correlation peak.
* **BPSK**: binary phase-shift keying; modulation by flipping the carrier's phase 180°, i.e., multiplying it by ±1.
* **C/A code**: the civil "coarse/acquisition" GPS code: 1023 chips, 1.023 Mchip/s, 1 ms period.
* **C/N0**: carrier power divided by noise power density, in dB-Hz; bandwidth-independent link quality.
* **Carrier**: the underlying pure sinusoid that modulation imprints information onto.
* **CDMA**: code-division multiple access; many transmitters sharing one band, separated by their codes.
* **Chip**: one symbol of the spreading code (called a chip, not a bit, because it carries no information).
* **Coherent integration**: summing correlator outputs with phase preserved; SNR grows as N.
* **Correlation**: multiply two sequences element-wise and sum; a similarity score.
* **dB / dBm**: logarithmic power ratio (10 dB per factor of 10) / absolute power referenced to 1 mW.
* **Despreading**: multiplying the received signal by an aligned code replica, collapsing it back to its narrow information bandwidth.
* **Doppler shift**: frequency offset from relative motion; up to ~±4 kHz for GPS at L1.
* **Gold codes**: families of PRN sequences (Gold, 1967) with guaranteed low cross- and off-peak auto-correlation.
* **Matched filter**: correlation against the known signal shape; the provably optimal detector in white noise, achieving SNR = 2E/N0.
* **Noise figure**: the dB by which a receiver stage degrades SNR beyond ideal thermal noise.
* **Noncoherent integration**: summing squared magnitudes of coherent blocks; pays reduced gain (squaring loss) but tolerates phase drift and data flips.
* **Processing gain**: the SNR recovered by despreading; ≈ $10\log_{10}(\text{chip rate} / \text{data rate})$ ≈ 43 dB for C/A.
* **PRN code**: pseudorandom noise sequence; deterministic and reproducible but statistically noise-like.
* **Pseudorange**: distance to a satellite inferred from code arrival time, biased by the receiver clock error (hence "pseudo").
* **Squaring loss**: the SNR penalty of noncoherent combining, from multiplying noise by noise.
* **Thermal (Johnson-Nyquist) noise**: kTB; −174 dBm per Hz at 290 K; the hiss of warm electrons.
* **TCXO**: temperature-compensated crystal oscillator; the receiver's few-ppm local timebase.
