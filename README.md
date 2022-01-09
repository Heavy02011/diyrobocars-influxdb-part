# diyrobocars-influxdb-part
documentation of integration of part influx.py into DIYrobocars.com framework

## Motivation and Background
As I'm again and again stumpling across understanding 
1. parts anatomy and integration
2. my car behaviour during training and race in the simulator
I take the opportunity to document every step to follow on how to integrate a new part - here influx.py - into the donkeycar framework.

The original version was published on the [discord channel](https://discord.com/channels/662098530411741184/671604287419187200/778673564387639367) in this [gist](https://gist.github.com/Heavy02011/0c31b8cd6025f50e7387456b25bffc20) on Nov. 18, 2020.

```
cloud-rocket — 19.11.2020
@Rainer Bareiß ·Parking Lot Nerds - that exactly was my original idea! But I had 2 issues with this approach, before I started implementing it:
1. Isn'tInfluxDB introducing a significant latency?
2. Grafana is fantastic, but it's not exactly mobile application. I'd like to have something on my phone attached to a remote control (better some Android app)..... How do you physically dealing with Grafana on the go?

ref. 1: I ran it on my local machine and did not see that - compared to the other parts - the influxdb introduced too much latency. however I did not measure it.
ref.2: you start an instance of grafana on your preferred server - eg the jetson nano on your car that generates your local wifi network - and connect with the browser on your phone.
ref. implementing: just test the part above. installing influxdb & grafana took me < 30 min on Ubuntu 18.04 on my local machine.
please make sure to set influxdb user & password as environment variables, see the code 

```
