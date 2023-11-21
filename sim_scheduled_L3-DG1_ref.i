ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 12 => r0 (12); loadI 8 => r2 (8)]
1:	[nop ; mult r2 (8), r0 (12) => r3 (96)]
2:	[nop ; nop ]
3:	[nop ; nop ] *1
4:	[add r2 (8), r3 (96) => r1 (104); nop ]
5:	[store r1 (104) => r0 (addr: 12); nop ]
6:	[nop ; nop ]
7:	[nop ; nop ]
8:	[nop ; nop ]
9:	[nop ; nop ] *5
10:	[output 12 (104); nop ]
output generates => 104

Executed 11 instructions and 22 operations in 11 cycles.
