# Numbers drawn in each figure

## header

(a) endpoints at 90° and 237°; shaded arc 210°–330° (one third), 1/3 color
(b) radius at 270°, point at 0.20 r; chord ends at 348° and 192° (nearest vertex 18° away; radius 60° from every vertex); inner half of the radius (center to 0.5 r) drawn as a thicker line, 1/2 color
(c) midpoint at 0.30 r, angle 85°; inner disk of radius r/2 filled, 1/4 color
numbers under the panels: (a) 1/3, (b) 1/2, (c) 1/4

## phrasings

canonical id 0; rephrasings id 16 (numeric threshold) and id 6 (no radius), picked with random.Random(0) within those groups; labeled prompt w00_c0 (approach C, description c0, clause after the problem)
highlighted clause: "In this problem, "at random" means choosing a point uniformly at random inside the disk and taking the chord whose midpoint is that point."

## which

x order (threshold, radius, id): 0(triangle,no r), 6(triangle,no r), 1(triangle,r=1), 11(triangle,r=1), 3(triangle,r=2), 9(triangle,r=2), 15(triangle,r=5), 12(r√3,no r), 7(r√3,r=1), 13(r√3,r=1), 17(r√3,r=1), 4(r√3,r=2), 2(r√3,r=5), 14(r√3,r=5), 10(numeric,r=1), 5(numeric,r=2), 8(numeric,r=5), 16(numeric,r=5)
3B per phrasing (1/3, 1/2, 1/4, other): 0: 9,10,1,10; 6: 8,8,4,10; 1: 5,13,6,6; 11: 6,9,6,9; 3: 11,5,4,10; 9: 8,6,5,11; 15: 8,8,1,13; 12: 8,3,7,12; 7: 8,9,6,7; 13: 9,9,6,6; 17: 10,8,3,9; 4: 9,6,5,10; 2: 3,11,3,13; 14: 5,13,4,8; 10: 3,16,5,6; 5: 4,7,7,12; 8: 5,6,4,15; 16: 2,12,4,12
7B per phrasing (1/3, 1/2, 1/4, other): 0: 11,4,0,15; 6: 18,2,0,10; 1: 17,3,4,6; 11: 17,1,5,7; 3: 12,5,5,8; 9: 9,3,6,12; 15: 6,8,0,16; 12: 18,1,3,8; 7: 12,14,1,3; 13: 7,17,2,4; 17: 5,20,2,3; 4: 6,7,9,8; 2: 6,12,7,5; 14: 8,13,2,7; 10: 7,16,0,7; 5: 9,9,3,9; 8: 8,12,2,8; 16: 6,12,8,4

## how

3B 1/3: derived 30 (angle 30); recalled 91 (angle 87, midpoint 4)
7B 1/3: derived 142 (angle 142); recalled 40 (angle 37, other: area of a circular segment 2, none 1)
3B 1/2: derived 95 (distance 95); recalled 64 (midpoint 23, angle 22, none 10, distance 6, other: area of a band of chords 1, other: half of the disk area 1, other: segment area, then 'half the circle' 1)
7B 1/2: derived 143 (distance 143); recalled 16 (angle 8, midpoint 7, distance 1)
3B 1/4: derived 75 (midpoint 75); recalled 6 (midpoint 6)
7B 1/4: derived 57 (midpoint 57); recalled 2 (midpoint 2)

## famous number

3B triangle: derived 52/141 = 37%
3B r√3: derived 95/145 = 66%
3B numeric: derived 53/75 = 71%
7B triangle: derived 108/136 = 79%
7B r√3: derived 150/172 = 87%
7B numeric: derived 84/92 = 91%
right panel: 7B phrasing 12 sample 26, answer lines [0, 10, 18, 22, 26, 28, 29, 31], math rendered with mathtext; highlighted line 26 (computes 2/3) and line 29 (boxed 1/3)

## where we look

7B phrasing 2 sample 7 (final number 1/2, derived); prompt 56 tokens, last 4 shown; answer tokens 0–72 shown; first 60 answer tokens (0–59) shaded grey; branch word "perpendicular distance" (tokens 68–69); dots at answer tokens 38, 58, 63, 67
for the caption: branch word of this answer at answer token 68; median branch-word position over the 342 answers: token 110

## when

x (tokens before the branch word, equally spaced): [30, 20, 10, 5, 2, 1, 0]
probe, layer 22, balanced accuracy (%): 40.1, 47.9, 52.6, 57.2, 69.7, 74.6, 79.2
words only, prompt + answer text up to that point (%): 40.1, 48.8, 47.3, 46.1, 58.1, 59.2, 71.6
within-phrasing shuffle, 95th percentile, 50 shuffles (%): 40.6, 40.5, 46.4, 46.9, 48.5, 47.8, 51.9
chance: 33.3%
n per offset: 328, 333, 342, 342, 342, 342, 342

