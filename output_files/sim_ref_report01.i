ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 2000 => r32 (2000); loadI 4 => r10 (4)]
1:	[load r32 (addr: 2000) => r30 (0); add r32 (2000), r10 (4) => r29 (2004)]
2:	[load r29 (addr: 2004) => r31 (1); add r29 (2004), r10 (4) => r28 (2008)]
3:	[load r28 (addr: 2008) => r23 (2); add r28 (2008), r10 (4) => r27 (2012)]
4:	[load r27 (addr: 2012) => r22 (3); add r27 (2012), r10 (4) => r26 (2016)]
5:	[load r26 (addr: 2016) => r24 (4); add r26 (2016), r10 (4) => r15 (2020)] *1
6:	[load r15 (addr: 2020) => r25 (5); add r15 (2020), r10 (4) => r0 (2024)] *2
7:	[add r30 (0), r31 (1) => r19 (1); loadI 2000 => r14 (2000)] *3
8:	[add r14 (2000), r10 (4) => r11 (2004); nop ] *4
9:	[add r23 (2), r22 (3) => r18 (5); mult r22 (3), r23 (2) => r21 (6)] *5
10:	[add r18 (5), r19 (1) => r17 (6); add r11 (2004), r10 (4) => r9 (2008)] *6
11:	[add r9 (2008), r10 (4) => r8 (2012); mult r24 (4), r25 (5) => r20 (20)] *9
12:	[nop ; nop ]
13:	[nop ; nop ] *11
14:	[add r20 (20), r21 (6) => r16 (26); nop ]
15:	[add r16 (26), r17 (6) => r3 (32); nop ]
16:	[store r3 (32) => r0 (addr: 2024); nop ]
17:	[nop ; nop ]
18:	[nop ; nop ]
19:	[nop ; nop ]
20:	[nop ; nop ] *16
21:	[load r14 (addr: 2000) => r12 (0); nop ]
22:	[load r11 (addr: 2004) => r13 (1); nop ]
23:	[load r9 (addr: 2008) => r7 (2); nop ]
24:	[load r8 (addr: 2012) => r6 (3); nop ]
25:	[nop ; nop ] *21
26:	[nop ; nop ] *22
27:	[nop ; mult r12 (0), r13 (1) => r5 (0)] *23
28:	[nop ; nop ] *24
29:	[add r6 (3), r7 (2) => r4 (5); nop ] *27
30:	[add r4 (5), r5 (0) => r2 (5); nop ]
31:	[add r2 (5), r3 (32) => r1 (37); nop ]
32:	[store r1 (37) => r0 (addr: 2024); nop ]
33:	[nop ; nop ]
34:	[nop ; nop ]
35:	[nop ; nop ]
36:	[nop ; nop ] *32
37:	[output 2024 (37); nop ]
output generates => 37

Executed 38 instructions and 76 operations in 38 cycles.
