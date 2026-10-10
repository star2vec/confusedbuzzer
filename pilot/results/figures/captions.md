# Figure captions

**header.** Three ways to draw a chord at random in the same circle, with the inscribed equilateral triangle: (a) two random points on the circle, (b) a random point on a random radius, with the chord at right angles to it, (c) a random midpoint in the disk. The shaded part marks where the chord comes out longer than the triangle's side.

**phrasings.** Prompts as the model sees them. Top: the canonical Bertrand problem statement and two of the 17 rephrasings (ids picked at random). Bottom: a labeled prompt, with the clause that states the approach highlighted.

**which.** Which number each model gives on each phrasing of the neutral problem (30 samples per phrasing, temperature 0.7, label = final number). Phrasings are grouped by how the threshold is stated (triangle side, r√3, or a number) and by radius ("r": radius not given).

**how.** How the neutral answers ending in 1/3, 1/2 or 1/4 got there, by hand judgment. Solid: derived (the written steps produce the number), colored by the variable treated as evenly spread; every derived 1/3 uses the angle, every derived 1/2 the distance, every derived 1/4 the midpoint, so the colors match the numbers. Hatched: recalled (the working gives something else, or the number is just stated). 3B: 361 answers; 7B: 400.

**famous_number.** Left: share of hand-judged answers whose steps actually produce their number, by how the threshold is phrased. Right: a recalled 1/3 from the 7B (real answer, lines removed where marked …): the working gives 2/3, the boxed answer is the famous 1/3.

**where_we_look.** Where the probes look, on one real 7B answer (phrasing 2, sample 7). Grey: the end of the prompt; the last prompt token is the reading probe's position. Bracket: the first 60 answer tokens averaged by the window probe. Highlighted: the first word that names the variable (the branch word, here at token 68); ticks mark positions 30, 10, 5 and 1 tokens before it. This answer was chosen for fit; the branch word usually comes around token 110.

**when.** When the final number becomes readable in the 7B's answer. x: position, in tokens before the first word that names the variable; y: balanced accuracy of a linear probe for the final number (1/3, 1/2, 1/4), test phrasings unseen in training. Black: probe on the residual stream at layer 22. Red: a classifier on the words alone. Grey: what shuffling labels within each phrasing reaches (95th percentile of 50 shuffles), the bar for reading more than the phrasing.
