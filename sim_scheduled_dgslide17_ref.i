ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 12 => r4 (12); loadI 8 => r3 (8)]
1:	[load r3 (addr: 8) => r2 (3); add r3 (8), r4 (12) => r0 (20)]
2:	[load r0 (addr: 20) => r1 (0); nop ]
3:	[nop ; nop ]
4:	[nop ; nop ]
5:	[nop ; nop ] *1
6:	[nop ; nop ] *2
7:	[store r1 (0) => r0 (addr: 20); nop ]
8:	[nop ; nop ]
9:	[nop ; nop ]
10:	[nop ; nop ]
11:	[nop ; nop ] *7
12:	[output 12 (4); nop ]
output generates => 4

Executed 13 instructions and 26 operations in 13 cycles.