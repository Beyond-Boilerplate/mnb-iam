---
title: "Lesson 01 — Bank Briefing & UI Orientation"
stem: 01-bank-briefing-and-ui
voice: en-US-BrianNeural
rate: "-12%"
pitch: "+0Hz"
duration_target_min: 10
---

## cold-open

Hey — welcome to Meridian National Bank’s Identity and Access Academy.

This is the listen-along for Lesson One: Bank Briefing and U.I. Orientation.

Think of it as a podcast with your staff engineer on day one. We’ll cover the ideas you need in your head before you click around IdentityIQ. Keep the written lesson open if you want, or just listen first and do the lab after.

Grab a notebook. You’re going to hear names you’ll reuse for the next fifty lessons.

## why-youre-here

You just joined Meridian’s Identity and Access team. Your manager is not going to throw you into joiner workflows or segregation-of-duties policies on day one.

They’ll walk you through who owns what, what problem IdentityIQ is solving, and how to find things in the console without breaking anything.

That is this lesson. Orientation first. Lifecycle automation comes later — Lesson Twenty-Nine and beyond — after you understand people, apps, and the language of access.

Here’s the control angle, because this is a bank. When an examiner asks, “Who operates the governance console, and how do you find an identity or a job result?” — your answer should be muscle memory. Not a Slack search. Day-one navigation is the first control hygiene step.

## what-iam-is

Identity and Access Management — I.A.M. — is the practice of making sure the right people have the right access to the right systems, for the right reason, and can prove it later.

At a bank, examiners ask four questions.

Who works here? You need a reliable list of people from H.R.

What can they do in systems? Accounts and entitlements, tied to those people.

Who approved that access? Approvals, certifications, or documented exceptions.

What happens when someone leaves? Access removed or disabled on a known timeline.

I.A.M. is not the help desk resetting passwords all day. And it is not network firewalls. Those teams partner with you. Your focus is identity governance: knowing who someone is, what they have, and whether that access is still appropriate.

Meridian bought SailPoint IdentityIQ — you’ll hear “I.I.Q.” — as the governance platform. It does not replace Active Directory, SAP, or the wire portal. It connects to those systems, builds a picture of each person’s access, and runs the processes Risk and Audit expect: approvals, reviews, policies.

Wrong way beginners think: “I.I.Q. is the directory where people log in.”

Right way: Active Directory and peers are often where people authenticate. I.I.Q. is where Meridian governs and proves access across many systems.

## your-team

You are an I.A.M. Engineer on the Identity Governance squad under Information Security — SEC. You’ll hear “I.A.M. Ops,” “I.G.A.,” and “Identity” used for the same group. Don’t sweat the labels.

Helen Ross — user I.D. helen.ross — is Head of Identity and Access. That’s your leadership and the I.A.M. platform owner.

Under Helen you’ll hear three lanes: I.A.M. Engineering — that’s you — designing roles, apps, policies, and workflows. I.A.M. Operations — running scheduled jobs, triaging failures, handling tickets. And I.A.M. Governance — certification campaigns, policy exceptions, exam evidence.

Outside the squad, your partners are H.R. Operations for people-data quality; app and system owners for entitlements on their platforms; Risk and Compliance for segregation of duties and exam readiness; and Technology for directories, connectors, and infrastructure.

A few owners you’ll hear by name. Christopher Hayes owns cloud and directory platforms. Deepa Nair owns SAP finance entitlements. Anthony Powell partners on toxic-access design. Rachel Evans owns wire initiate versus approve. Daniel Griffin owns core banking access.

You will not configure those platforms yourself on day one. You govern access to them in I.I.Q., with those people as control owners.

## six-constructs

Ignore product buzzwords until six ideas are solid. Everything else in the curriculum hangs on them.

Identity — a person Meridian tracks as one worker. Example: priya.wire — Priya in Treasury.

Account — a login on one system. Priya’s Wire Portal username.

Entitlement — a permission or group on that system: what the account can do. WIRE underscore INIT means she can create a wire.

Application — an I.I.Q. definition of a connected system: how we read and write accounts. Later you’ll build MNB-Wire-Portal.

Role — a package of entitlements, or nested roles, assigned for a job. Think “Wire Specialist birthright,” which you’ll build around Lesson Twenty-Four.

Policy — a rule that flags bad access combinations. Classic bank example: nobody holds both wire initiate and approve.

Two more terms you’ll see in the U.I. today.

Identity cube — I.I.Q.’s person-centric record: H.R. attributes, accounts, roles, risk, and open work. You govern people, not spreadsheet rows.

Work item — a human decision waiting in someone’s Inbox: approve access, certify access, remediate a violation.

Picture it: Identity at the top. Under it, attributes from H.R., accounts that each carry entitlements on an application, roles that package access, and work items or certifications that capture human decisions.

## shorthand-later

Managers talk in shorthand. Today you only need recognition — not configuration.

Joiner — someone new starts; they need starting access. Lesson Twenty-Nine.

Mover — someone changes job or department; access must follow. Lesson Thirty.

Leaver — someone leaves; access must be removed or disabled. Lesson Thirty-One.

Birthright — access every active person of a class gets automatically. Lesson Twenty-Four.

SoD — segregation of duties: toxic combinations one person should not hold. Lesson Thirty-Nine.

Population — a saved search or filter of identities, like all contractors. Lesson Seven.

Aggregation — a job that pulls accounts and entitlements from an application into I.I.Q. Lesson Four and beyond.

Certification — a campaign where managers or owners attest that access is still needed. Lesson Forty-Three and beyond.

If someone says “fix the joiner for Nina,” they mean: make sure the new hire’s cube exists and starting access is correct. You’ll practice that after H.R., apps, and roles are in place.

## four-surfaces

IdentityIQ separates work into four places. Bookmark them mentally.

Configuration — applications, roles, policies, workflows. Meridian names start with MNB dash.

Operational data — identities, account links, certifications. Search people by name, like helen.ross.

Tasks — aggregation, refresh, certification jobs. Prefer named tasks later, like Aggregate MNB-H.R.

Work items — human decisions. Your Inbox on day one — even if it’s empty.

Flow it in your head: you configure apps, roles, and policies. Tasks pull accounts and refresh cubes. Task results give you counters and proof. Identity cubes hold the person picture. Work items hold the human decisions.

Corporate context for the lab: email domain at meridiannb.com. Lab U.R.L. is localhost port eighty-eighty, path identityiq. Default admin is spadmin, password admin — unless your install changed it. Homelab sites may publish a different U.R.L.; use what LOCAL SETUP documents.

## lab-tour

When you sit down at the keyboard, the written lesson walks you through eight tasks. Here’s the mental map so the clicks make sense.

Task one: login and environment hygiene. Confirm you’re on the lab, not a mislabeled shared U.R.L., before you explore cubes. Wrong-environment mistakes in production become incident tickets.

Task two: tour an identity cube. Open Identities, search spadmin, and click through the tabs once — attributes, accounts, roles, work items, risk. In your own words, finish the sentence: “An identity cube is…” Optional: search helen.ross if she already exists; if not, that’s fine — H.R. aggregation comes in Lesson Four.

Task three: Applications and Tasks map. Applications are systems I.I.Q. knows about. Tasks are jobs that move data or run campaigns. Today you only look. Do not run random jobs.

Task four: Work Item Inbox. Approvals and certifications land here. Empty on day one is normal. Bookmark it. Lessons Thirty-Five through Forty-Six will fill it with real decisions.

Task five: Debug awareness. Debug is the engineer’s X-ray. Objects are often XML under the hood. Browse Application, Identity, TaskDefinition, Bundle, Workflow. Open one. Confirm it’s XML. Look — don’t edit randomly.

Task six: skim Meridian lab data. Before I.I.Q. “knows” Meridian workers, the truth lives in files. Open H.R. Applications dot text. Find leadership MNB zero-zero-zero-zero-one through zero-eight — helen.ross, christopher.hayes, deepa.nair, and friends. Find scripted personas MNB ninety through ninety-seven — priya.wire, marcus.approve, jordan.reed, raj.external, samir.hassan, sofia.torres, kai.nguyen, amelia.brooks. Glance at the entitlement dictionary and the SoD matrix so you know Meridian already listed bad pairs. Don’t memorize policy design yet.

Task seven: write one plain-language paragraph for your manager — why Meridian runs IdentityIQ. Cover knowing who works here, what access they hold, proving reviews to examiners, and reducing leftover access when people change jobs or leave.

Task eight: file a persona cheat sheet. You’ll reuse these names through Lesson Forty. Especially remember the wire pair: priya.wire holds initiate only; marcus.approve holds approve only. That’s healthy dual control later. jordan.reed holds an intentional bad finance-plus-cloud combo for later labs. samir.hassan is terminated with leftover I.T. access. sofia.torres is on leave. nina.joiner is your new-hire scenario for Lesson Twenty-Nine.

## close

By the end of the written lab, you should be able to explain I.A.M. versus directories in a sentence or two; name Helen and at least three partner owners; define identity, account, entitlement, application, role, and policy without looking them up; log in as spadmin; tour a cube; find Applications, Tasks, Inbox, and Debug; and recognize the scripted personas.

Examiner rehearsal question: “Show me how an operator finds an identity and a task result in this system.”

When you’re ready, open Lesson One in the Academy, complete the tasks, and file your binder screenshots.

Next up in the curriculum: Lesson Two — Meridian’s org model and risk language.

That’s your briefing. Welcome to the bank.
