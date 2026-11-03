* CIVL3206 D3 portal frame, TTW ST-30101 Section 1, v3 (M9_opt1_adopt)
* Option 1 - adopted: west column 610UB113, mid rafter A-B 360UB50.7
* notional load as separate cases 4/5, only in 1.2G+1.5Q (AS 4100 Cl 3.2.4)
*
 
VERS     5
TYPE     3
VERT     2
UNIT     1 m   kN  T   C
 
NODE     1     0.0000     0.0000     0.0000 110000
NODE     2    21.9930     0.0000     0.0000 110000
NODE     3    44.2530     0.0000     0.0000 110000
NODE     4    66.5130     0.0000     0.0000 110000
NODE     5    88.7730     0.0000     0.0000 110000
NODE     6   111.0330     0.0000     0.0000 110000
NODE     7   132.9420     0.0000     0.0000 110000
NODE    11     0.0000    10.5102     0.0000 000000
NODE    12     6.2780    10.7950     0.0000 000000
NODE    13    17.4930    11.3038     0.0000 000000
NODE    14    21.9930    11.5079     0.0000 000000
NODE    15    26.4930    11.7121     0.0000 000000
NODE    16    33.2565    12.0189     0.0000 000000
NODE    17    39.7530    12.3136     0.0000 000000
NODE    18    44.2530    12.5178     0.0000 000000
NODE    19    48.7530    12.7219     0.0000 000000
NODE    20    62.0130    13.3234     0.0000 000000
NODE    21    66.5130    13.5276     0.0000 000000
NODE    22    71.0130    13.3196     0.0000 000000
NODE    23    84.2730    12.7181     0.0000 000000
NODE    24    88.7730    12.5140     0.0000 000000
NODE    25    93.2730    12.3098     0.0000 000000
NODE    26    99.7275    12.0170     0.0000 000000
NODE    27   106.5330    11.7083     0.0000 000000
NODE    28   111.0330    11.5041     0.0000 000000
NODE    29   115.5330    11.3000     0.0000 000000
NODE    30   129.6780    10.6583     0.0000 000000
NODE    31   132.9420    10.5102     0.0000 000000
 
MEMB     1     1    11    X      8     1    000000 000000
MEMB     2     2    14    X      6     1    000000 000001
MEMB     3     3    18    X      6     1    000000 000001
MEMB     4     4    21    X      6     1    000000 000001
MEMB     5     5    24    X      6     1    000000 000001
MEMB     6     6    28    X      6     1    000000 000001
MEMB     7     7    31    X      5     1    000000 000000
MEMB   101    11    12    Y      1     1    000000 000000
MEMB   102    12    13    Y      7     1    000000 000000
MEMB   103    13    14    Y      2     1    000000 000000
MEMB   104    14    15    Y      2     1    000000 000000
MEMB   105    15    16    Y      3     1    000000 000000
MEMB   106    16    17    Y      3     1    000000 000000
MEMB   107    17    18    Y      2     1    000000 000000
MEMB   108    18    19    Y      2     1    000000 000000
MEMB   109    19    20    Y      3     1    000000 000000
MEMB   110    20    21    Y      2     1    000000 000000
MEMB   111    21    22    Y      2     1    000000 000000
MEMB   112    22    23    Y      3     1    000000 000000
MEMB   113    23    24    Y      2     1    000000 000000
MEMB   114    24    25    Y      2     1    000000 000000
MEMB   115    25    26    Y      3     1    000000 000000
MEMB   116    26    27    Y      3     1    000000 000000
MEMB   117    27    28    Y      2     1    000000 000000
MEMB   118    28    29    Y      2     1    000000 000000
MEMB   119    29    30    Y      4     1    000000 000000
MEMB   120    30    31    Y      5     1    000000 000000
 
PROP     1 PRIS Nominal         530UB92.4
       1.1800E-02   0.000       0.000      7.7500E-07  2.3800E-05  5.5400E-04
PROP     2 PRIS Nominal         530UB82.0
       1.0500E-02   0.000       0.000      5.2600E-07  2.0100E-05  4.7700E-04
PROP     3 PRIS Nominal         310UB46.2
       5.9300E-03   0.000       0.000      2.3300E-07  9.0100E-06  1.0000E-04
PROP     4 PRIS Nominal         410UB59.7
       7.6400E-03   0.000       0.000      3.3700E-07  1.2100E-05  2.1600E-04
PROP     5 PRIS Nominal         610UB101
       1.3000E-02   0.000       0.000      7.9000E-07  2.9300E-05  7.6100E-04
PROP     6 PRIS Nominal         200x200x9.0 SHS
       6.6000E-03   0.000       0.000      7.8466E-05  3.9233E-05  3.9233E-05
PROP     7 PRIS Nominal         360UB50.7
       6.4700E-03   0.000       0.000      2.4100E-07  9.6000E-06  1.4200E-04
PROP     8 PRIS Nominal         610UB113
       1.4500E-02   0.000       0.000      1.1400E-06  3.4300E-05  8.7500E-04
 
MATL     1 2.000E+08 3.000E-01 7.850E+00 1.170E-05
 
CASE     1 G
NDLD    11      0.000    -45.000      0.000      0.000      0.000      0.000
NDLD    31      0.000    -45.000      0.000      0.000      0.000      0.000
MBLD   101  UNIF  FY  GL           -6.7890
MBLD   102  UNIF  FY  GL           -6.7890
MBLD   103  UNIF  FY  GL           -6.7890
MBLD   104  UNIF  FY  GL           -6.7890
MBLD   105  UNIF  FY  GL           -6.7890
MBLD   106  UNIF  FY  GL           -6.7890
MBLD   107  UNIF  FY  GL           -6.7890
MBLD   108  UNIF  FY  GL           -6.7890
MBLD   109  UNIF  FY  GL           -6.7890
MBLD   110  UNIF  FY  GL           -6.7890
MBLD   111  UNIF  FY  GL           -6.7890
MBLD   112  UNIF  FY  GL           -6.7890
MBLD   113  UNIF  FY  GL           -6.7890
MBLD   114  UNIF  FY  GL           -6.7890
MBLD   115  UNIF  FY  GL           -6.7890
MBLD   116  UNIF  FY  GL           -6.7890
MBLD   117  UNIF  FY  GL           -6.7890
MBLD   118  UNIF  FY  GL           -6.7890
MBLD   119  UNIF  FY  GL           -6.7890
MBLD   120  UNIF  FY  GL           -6.7890
 
CASE     2 Q
MBLD   101  UNIF  FY  GL           -2.8853
MBLD   102  UNIF  FY  GL           -2.8853
MBLD   103  UNIF  FY  GL           -2.8853
MBLD   104  UNIF  FY  GL           -2.8853
MBLD   105  UNIF  FY  GL           -2.8853
MBLD   106  UNIF  FY  GL           -2.8853
MBLD   107  UNIF  FY  GL           -2.8853
MBLD   108  UNIF  FY  GL           -2.8853
MBLD   109  UNIF  FY  GL           -2.8853
MBLD   110  UNIF  FY  GL           -2.8853
MBLD   111  UNIF  FY  GL           -2.8853
MBLD   112  UNIF  FY  GL           -2.8853
MBLD   113  UNIF  FY  GL           -2.8853
MBLD   114  UNIF  FY  GL           -2.8853
MBLD   115  UNIF  FY  GL           -2.8853
MBLD   116  UNIF  FY  GL           -2.8853
MBLD   117  UNIF  FY  GL           -2.8853
MBLD   118  UNIF  FY  GL           -2.8853
MBLD   119  UNIF  FY  GL           -2.8853
MBLD   120  UNIF  FY  GL           -2.8853
 
CASE     3 Wu up
MBLD     1  UNIF  FX  GL            1.4709
MBLD     7  UNIF  FX  GL            7.3548
MBLD   101  UNIF  FY  LO           13.5780
MBLD   102  UNIF  FY  LO           13.5780
MBLD   103  UNIF  FY  LO           13.5780
MBLD   104  UNIF  FY  LO           13.5780
MBLD   105  UNIF  FY  LO           13.5780
MBLD   106  UNIF  FY  LO           11.8808
MBLD   107  UNIF  FY  LO           11.8808
MBLD   108  UNIF  FY  LO           11.8808
MBLD   109  UNIF  FY  LO           11.8808
MBLD   110  UNIF  FY  LO           11.8808
MBLD   111  UNIF  FY  LO            6.7890
MBLD   112  UNIF  FY  LO            6.7890
MBLD   113  UNIF  FY  LO            6.7890
MBLD   114  UNIF  FY  LO            6.7890
MBLD   115  UNIF  FY  LO            6.7890
MBLD   116  UNIF  FY  LO            5.0918
MBLD   117  UNIF  FY  LO            5.0918
MBLD   118  UNIF  FY  LO            5.0918
MBLD   119  UNIF  FY  LO            5.0918
MBLD   120  UNIF  FY  LO            5.0918
 
CASE     4 N east
NDLD    11      3.536      0.000      0.000      0.000      0.000      0.000
 
CASE     5 N west
NDLD    11     -3.536      0.000      0.000      0.000      0.000      0.000
 
CASE     6 1.2G+1.5Q+N east
COMB     1      1.200
COMB     2      1.500
COMB     4      1.000
 
CASE     7 1.2G+1.5Q+N west
COMB     1      1.200
COMB     2      1.500
COMB     5      1.000
 
CASE     8 0.9G+Wu up
COMB     1      0.900
COMB     3      1.000
 
