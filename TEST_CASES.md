# Test Cases

## 1. Configuration and budget memory

Input:
- I am looking for a 3 BHK.
- My budget is around 1.5 crore.

Expected:
- AI remembers the 3 BHK.
- AI remembers the ₹1.5 crore budget.
- AI explains that 3 BHK starts at ₹1.75 crore onwards.
- AI may suggest the 2 BHK because it starts at ₹1.35 crore onwards.

Actual:
- Verify through the running Gemini-powered application.

## 2. Price

Input:
What are the prices?

Expected:
- 2 BHK: ₹1.35 crore onwards.
- 3 BHK: ₹1.75 crore onwards.

Actual:
- Verify through the running Gemini-powered application.

## 3. Unknown information

Input:
What amenities are available?

Expected:
- AI does not invent amenities.
- AI says it does not have verified information.
- AI offers human escalation.

Actual:
- Verify through the running Gemini-powered application.

## 4. Discount

Input:
Can you give me a discount?

Expected:
- AI does not invent a discount.
- AI offers human escalation.

Actual:
- Verify through the running Gemini-powered application.

## 5. Site visit

Input:
- I want a site visit.
- 2026-09-10 at 11:00 AM.

Expected:
- AI handles the site visit flow.
- Application simulator returns a booking result.
- AI communicates the booking result.

Actual:
- Verify through the running Gemini-powered application.

## 6. Booking failure

Input:
- I want a site visit.
- 2026-09-10 at 00:00.

Expected:
- Simulator marks the slot unavailable.
- AI communicates the failure and asks for another date/time or offers human escalation.

Actual:
- Verify through the running Gemini-powered application.

## 7. Opt out

Input:
Please don't contact me again.

Expected:
- Lead is marked opted out.
- Conversation ends.

Actual:
- Verify through the running Gemini-powered application.

## 8. Human escalation

Input:
I want to speak to a sales representative.

Expected:
- Human escalation is recorded.
- AI responds naturally and asks for a convenient connection time.

Actual:
- Verify through the running Gemini-powered application.
