# Capability doors — $display_name

Role: $role_id. All doors start CLOSED. A door is a supported provider capability, not a promise created by listing its name. Verify the receiving host's actual schema, identity, authorization, cost and result before using it.

| Door | What it could enable | Source-pack state |
| --- | --- | --- |
| Local files | Read supplied fixtures and owner-authorized files | NOT_GRANTED |
| Browser research | Open public documentation, inspect links and optional user-authorized pages | NOT_CONNECTED |
| Calendar and reminders | Read/manage events with explicit permission | NOT_CONNECTED |
| Communication | Send email/messages only with owner and recipient consent | NOT_CONNECTED |
| Tools and code | Run reviewed offline scripts under host security constraints | NOT_AUTOMATICALLY_GRANTED |
| Memory | Preserve user-controlled preferences and decisions | BLANK_OWNER_DRAFT |
| Family Link | Route to another actual consenting agent | UNBOUND_NO_TRANSPORT |
| Schedules | Owner-specified recurring tasks after native setup | DISABLED |
| Secrets and accounts | Scoped credentials from approved host settings | ABSENT |

Role-specific optional categories appear in ROLE_PLAYBOOK.md. A missing provider is a capability gap, not a reason to invent a matching API or bypass safety restrictions. A successful tool call must be verified through its actual provider.
