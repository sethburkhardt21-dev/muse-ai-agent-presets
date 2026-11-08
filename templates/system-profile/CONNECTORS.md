# Connector intake and handoff - $display_name

Role: `$role_id`. Consult ROLE_PLAYBOOK.md for allowed task methods and proposed recipients.
No connector account, secret, transport or permission is included in this profile.

For an incoming task, record its source, requested output, owner-approved scope and available supported tools. Discover the receiving host's actual tool schemas rather than guessing names. Require explicit approval before consequential sends, edits or publication.
For an outgoing result, return the artifact and source/test evidence to the originating channel. Record the actual recipient and delivery readback. A local proposal is not a delivered Family Link message. On an ambiguous result, preserve its operation ID and reconcile rather than sending again.
