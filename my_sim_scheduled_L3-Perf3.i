ILOC Simulator, Version 412-2020-1
Interlock settings: branches 

0:	[loadI 1024 => r2 (1024); loadI 4 => r4 (4)]
1:	[load r2 (addr: 1024) => r3 (0); add r2 (1024), r4 (4) => r0 (1028)]
2:	[load r0 (addr: 1028) => r1 (0); nop ]
3:	[nop ; nop ]
4:	[nop ; nop ]
5:	[nop ; nop ] *1
6:	[nop ; nop ] *2
7:	[store r2 (1024) => r3 (addr: 0); nop ]
8:	[nop ; nop ]
9:	[nop ; nop ]
10:	[nop ; nop ]
11:	[nop ; nop ] *7
12:	[store r0 (1028) => r1 (addr: 0); nop ]
13:	[nop ; nop ]
14:	[nop ; nop ]
15:	[nop ; nop ]
16:	[nop ; nop ] *12
17:	[output 2048 (0); nop ]
output generates => 0
18:	[output 2052 (0); nop ]
output generates => 0

Executed 19 instructions and 38 operations in 19 cycles.
