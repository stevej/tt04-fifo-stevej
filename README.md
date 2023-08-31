![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/wokwi_test/badge.svg)

# 8-bit FIFO with a depth of 32 for TinyTapeout 4

TinyTapeout is an educational project that aims to make it easier and cheaper than ever to get your digital designs manufactured on a real chip! This is my submission for TinyTapeout 4 in early September 2023.

A FIFO queue is a first-in, first-out digital device that allows two parties to communicate with a channel of limited size by following specific rules: one party writes, the other reads. The first thing written will be the first thing read. Reading an empty queue is disallowed and writing to a full queue is disallowed. Empty and full status can be checked via the proper status pin before use.

In psuedo-code, two parties can communicate with this FIFO as follows:

Party A
```
while !full:
    write_entry(item)
```

Party B
```
while !empty:
    item = read_entry()
```

The queue works in First-Word Fall-Through mode meaning that the top item is always available on the read bus even
if you haven't set `read_request` high. If you want to see the next item in the queue on your next read, be sure
to set `read_request` high.

`almost_full` and `almost_empty` signals exist so you can batch reads and writes. Instead of checking for
`full` or `empty` on each read or write you can instead check `almost_full` or `almost_empty` and batch read or writes
based on how many slots are available. For this design taped out in TinyTapeout 4, almost_full means 28 of 32 slots
have been used and almost_empty means that 28 of 32 slots are free.


# Want to see your own digital design taped out to an ASIC?
Go to https://tinytapeout.com for instructions!
