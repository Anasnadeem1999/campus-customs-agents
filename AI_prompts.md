# AI prompts — Homework 5

A running log of the prompts given to the assistant, one section per problem.

## Problem 1 — setup, data, and the shop brief

> Hello Mister, we are working on HW 5 of the AI foundations course, please
> work in the separate HW5 folder available in the AI Foundations folder.

In answer to two setup questions: HW5 gets **its own git repo** (as HW4 did),
and **nothing is carried over from HW4** — a fresh start.

Then, with `data.zip` attached:

> Okay so we are making campus customs multi agent operations team which is an
> agentic team that is suppose to run the shop. The open tickets will be
> landing on a board including customer orders, rents, unpaid bills, discount
> requests and whatever the shop basically has to handle. We will be building
> three pieces that interact with each other, including mcp server, a fastapi
> backend with the multi agents team and also a react dashboard so that the
> human can watch how the agents are working and also approve the requests.
> Our agents team is suppose to have complete connectivity which means any
> agent may delegate the tasks to other agents for help. This assignment
> specifically asks to build the following agents, a boss agent wich reads each
> ticket and decides who should be working on it and making the final calls, a
> inventory agent which checks the stocks by SKUs and sizes and looks for any
> shortfalls also figuring out which of the vendors can restock it, a
> accounting agent which basivally looks out for the cashs and invoices and
> also checks the margins while preparing for the payments and or the purchase
> orders for the humans approval, a facilities agent which basically handles
> the shop space side including leases and rents ectectra and finally a
> customers service agent which will be draft messages for the customers.
>
> Now with respect to the data I will be uploading a DATA.ZIP file which you
> need to unzip in order to gain access to data/campus_customs.db. This file is
> going to be the original data base including tables which include desk,
> tickets, inventories, pricings, vendors, leases, cash accounts, payments,
> invoices and what not. All of the tools are to be updated within the database
> as the tickets start getting resolved. I want you to please make a copy of
> this database file called data/campus_customs_new.db and also point the mcp
> server and backend at that specific working copy. Please keep the
> campus_customs.db as untouched so that we can reset when we want when we have
> to restart resolving the tickets.
>
> Now coming to the rules of the shop, the field desk.date_today is the "today"
> for the shop, this date will be used to determine basically what is overdue.
> Secondly vendor lead times will be coming from the vendors table, the vendor
> will not be shipping the new product while they still have any unpaid
> invoice, the human approval is to be required for any payments. Please please
> please make sure whenever the payment is made, the relevant table is also
> updated. Also if there is no sufficient cash then the payment shall be
> refused by the pay tool so that there is no negative balance. Cash is to only
> go out in this homework as we have not modeled revenue hence no money is
> coming in. Also before the full run to resolve the tickets please please
> please make sure to reset the database to the original values. AND DO NOT
> EMAIL CUSTOMERS OR CALL REAL VENDORS the drafts are to stay on board.
>
> We will me using portkey_API_key for the ai calls. We are to use gpt-6-luna
> equivalent through the portkey for this assignment for every agent. As you
> know multi agent chats will be burning the tokens very fast. The professor is
> going to deduct points if any other models shows up in the code or the runs.
>
> Okay so now pls work one problem at a time. The final submission is to be
> public Github repo.
