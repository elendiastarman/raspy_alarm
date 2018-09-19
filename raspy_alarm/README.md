# Raspy Alarm

I started this project because frankly, alarms made for deaf people suck. So I set out to make my own with a Raspberry Pi 3 and as a bonus, I could hook it into other things. In particular, I have on-call duties for work on occasion and there is no effective solution for waking me up remotely in the middle of the night. Until now! This alarm clock can listen for emails from white-listed people and wake me up if I'm needed.

## Software

### Overview

There are three main pieces: the interface, the scheduler, and the rouser. The interface is what looks for or receives input from external sources, such as an email. The scheduler is responsible for managing the schedule file and starting the alarm when desired. The rouser is responsible for running the alarm, specifically the attached shaker (or other output devices) and any attached buttons (or other input devices).

### The Interface

Without the interface, the only way to add, change, or remove alarm times is to edit the schedule file directly. The included email interface polls a given email address and parses the latest emails to determine how to modify the alarm schedule. It also has some functionality to respond to these emails in some situations, e.g. for acknowledgement.

### The Scheduler

The scheduler here does three things in a loop:

1. Checks its interfaces (via `Interface.check`); the interface will use methods on the scheduler to update the schedule file.
1. Reads the schedule file and calculates the alarm times.
1. If an alarm time is in the very recent past, start the alarm and pass it the conditions to meet.

The conditions the scheduler passes will most likely be simple Python lambdas that take a list of button presses, effectively, and if any of the lambdas evaluate to a truthy value, then the alarm will stop. TBD how these lambdas are specified, but there will likely be a pre-existing list that can be referred to when setting alarm times. This is useful because you might want a regular weekly alarm to require a long press of 3 seconds to shut off whereas an on-call alarm requires sending an email to shut it off, thereby increasing the effort it takes to turn it off and increasing the chance that the target is awake.

### The Rouser

This is probably the simplest piece. The alarm can be started with `Rouser.start_alarm` and the rouser checks the conditions - passed to it by the scheduler - for stopping the alarm every second until they are met (`Rouser.main_loop`). The alarm can be stopped at any time with `Rouser.stop_alarm` and the rouser can be gracefully shut down with `Rouser.stop_loop`.

## Hardware

The major pieces are:

* Raspberry Pi to run the alarm program and handle input/output
* 5V power supply for the Raspberry Pi
* 12V shaker (which I have from previous alarms)
* 12V power supply for the shaker
* Relay switch because the Raspberry Pi can't power the shaker on it's own
* Buttons or other input devices to interact with the alarm
* Wires to connect all these